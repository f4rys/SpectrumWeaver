"""A streaming spectrum viewer widget that displays spectrograms in real-time."""

import threading
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout

from analyzers.spectrum_analyzer import SpectrumAnalyzer


class SpectrumViewer(QWidget):
    """
    A widget for displaying a streaming spectrogram of an audio file.
    This widget uses a streaming spectrum analyzer to process audio data
    in real-time and display the results progressively.
    It supports thread-safe updates using Qt signals to ensure smooth UI performance.
    The spectrogram is displayed using PyQtGraph's ImageItem for efficient rendering.
    The widget automatically configures its axes based on the audio metadata
    and updates the display at a maximum rate of 60 FPS.
    """
    # Signals for thread-safe communication
    frame_received = Signal(int, np.ndarray)  # frame_index, magnitudes_db
    analysis_complete = Signal()
 
    def __init__(self, parent: QStackedWidget, path: str) -> None:
        super().__init__(parent)
        self.audio_path = path
        self.analyzer: SpectrumAnalyzer = None
        self.spectrogram_data: np.ndarray = None
        self.data_lock = threading.Lock()
        self.metadata: dict = {}

        # Connect signals
        self.frame_received.connect(self._on_frame_received)

        # UI components
        self.plot_widget = None
        self.image_item = None

        # Update timer for progressive display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)

        self._setup_ui()
        self._start_analysis()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#202020')

        # Create the image item for the spectrogram
        self.image_item = pg.ImageItem()
        self.plot_widget.addItem(self.image_item)
        main_layout.addWidget(self.plot_widget)

        # Configure the plot
        self.plot_widget.setLabel('left', 'Frequency', units='Hz')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setTitle(self.audio_path)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.image_item.setColorMap('viridis')

    def _configure_axes(self) -> None:
        """Configure plot axes based on audio metadata."""
        if not self.metadata:
            return

        frequencies = self.metadata['frequencies']
        duration = self.metadata['duration']

        # Set the view range
        # X-axis: Time (0 to duration)
        # Y-axis: Frequency (0 Hz at bottom to max freq at top)
        self.plot_widget.setXRange(0, duration)
        self.plot_widget.setYRange(frequencies[0], frequencies[-1])

        # Set limits
        self.plot_widget.setLimits(
            xMin=0, xMax=duration,
            yMin=frequencies[0], yMax=frequencies[-1]
        )

    def _start_analysis(self) -> None:
        """Start the streaming spectrum analysis."""
        try:
            # Create analyzer with optimized parameters (using Hann window)
            self.analyzer = SpectrumAnalyzer(
                path=self.audio_path,
                callback=self._on_fft_result_threaded,
                fft_size=2048,
                hop_length=512,
                max_freq=22050
            )

            # Start analysis and get metadata
            self.metadata = self.analyzer.start()

            # Initialize spectrogram data array
            num_time_frames = self.metadata['num_time_frames']
            num_freq_bins = len(self.metadata['frequencies'])
            self.spectrogram_data = np.full((num_freq_bins, num_time_frames), -120.0, dtype=np.float32)

            # Configure plot axes based on metadata
            self._configure_axes()

            # Start the display update timer (60 FPS max)
            self.update_timer.start(16)

        except Exception as e:
            # Display error in plot title
            self.plot_widget.setTitle(f"Error: {str(e)}")

    def _on_fft_result_threaded(self, frame_index: int, magnitudes_db: np.ndarray) -> None:
        """
        Thread-safe callback function called by the streaming analyzer.
        This emits Qt signals to ensure UI updates happen on the main thread.
        """
        if frame_index == -1:  # End of processing signal
            QTimer.singleShot(0, self._on_analysis_complete)
        else:
            self.frame_received.emit(frame_index, magnitudes_db)

    def _on_frame_received(self, frame_index: int, magnitudes_db: np.ndarray) -> None:
        """
        Main thread handler for FFT results.
        This is called via Qt signal from the worker thread.
        """
        if self.spectrogram_data is None:
            return

        # Update the spectrogram data
        if 0 <= frame_index < self.spectrogram_data.shape[1]:
            with self.data_lock:
                # Store magnitudes in natural FFT order (0 Hz to max freq)
                end_idx = min(len(magnitudes_db), self.spectrogram_data.shape[0])
                self.spectrogram_data[:end_idx, frame_index] = magnitudes_db[:end_idx]

    def _update_display(self) -> None:
        """
        Update the display with new spectrogram data.
        This runs on a timer to provide smooth progressive updates.
        """
        if self.spectrogram_data is None or not self.metadata:
            return

        # Get current spectrogram data with thread safety
        with self.data_lock:
            current_data = self.spectrogram_data.copy()

        # Transpose and set the image item
        self.image_item.setImage(current_data.T, autoLevels=False, levels=(-80, 0))

        # Update the coordinate system
        duration = self.metadata['duration']
        frequencies = self.metadata['frequencies']
        rect = [
            0,  # x start (time=0)
            frequencies[0],  # y start (lowest freq, bottom of display)
            duration,  # width (time extent)
            frequencies[-1] - frequencies[0]  # height (freq extent)
        ]
        self.image_item.setRect(*rect)

    def _on_analysis_complete(self) -> None:
        """Called when streaming analysis is complete."""
        self.update_timer.stop()
        self._update_display()
        self.analysis_complete.emit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Clean up when the widget is closed."""
        if self.analyzer:
            self.analyzer.stop()
        self.update_timer.stop()
        super().closeEvent(event)
