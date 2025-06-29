"""A streaming spectrum viewer widget that displays spectrograms in real-time."""

import threading

import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout

from analyzers.spectrum_analyzer import SpectrumAnalyzer
from .custom_context_menu import CustomContextMenu


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
 
    def __init__(self, parent: QStackedWidget, path: str = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.audio_path = path
        self.analyzer: SpectrumAnalyzer = None
        self.spectrogram_data: np.ndarray = None
        self.data_lock = threading.Lock()
        self.metadata: dict = {}
        self._last_displayed_frame = 0

        # Connect signals
        self.frame_received.connect(self._on_frame_received)

        # UI components
        self.plot_widget = None
        self.image_item = None
        self.color_bar = None
        self.context_menu = CustomContextMenu(
            self,
            plot_widget=None,  # will be set after _setup_ui
            image_item=None,   # will be set after _setup_ui
            colorbar=None,  # will be set after _setup_ui
            audio_path=self.audio_path,
            spectrogram_data=self.spectrogram_data,
            metadata=self.metadata
        )

        self._setup_ui()

        # Set plot_widget and image_item references in context_menu
        self.context_menu.plot_widget = self.plot_widget
        self.context_menu.image_item = self.image_item

        if self.audio_path:
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
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()

        # Set initial view range
        self.plot_widget.setXRange(0, 60)
        self.plot_widget.setYRange(0, 22050)
        
        # Set color map
        cmap = pg.colormap.get('viridis')
        self.image_item.setColorMap(cmap)

        # Add color bar for dB scale
        self.color_bar = pg.ColorBarItem(
            values=(-120, 0),
            colorMap=cmap,
            label='dB',
            interactive=False
        )
        self.color_bar.setImageItem(self.image_item, insert_in=self.plot_widget.getPlotItem())

        if self.audio_path:
            self.plot_widget.setTitle(self.audio_path)
        else:
            self.plot_widget.setTitle("")

        # After UI is set up, update context_menu references
        if self.context_menu:
            self.context_menu.plot_widget = self.plot_widget
            self.context_menu.image_item = self.image_item
            self.context_menu.colorbar = self.color_bar

    def contextMenuEvent(self, event):
        # Update context_menu data before showing
        self.context_menu.audio_path = self.audio_path
        self.context_menu.spectrogram_data = self.spectrogram_data
        self.context_menu.metadata = self.metadata
        self.context_menu.exec(event)

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
        if not self.audio_path:
            return
        try:
            # Create analyzer with optimized parameters (using Hann window)
            self.analyzer = SpectrumAnalyzer(
                path=self.audio_path,
                callback=self._on_fft_result_threaded,
                fft_size=2048,
                hop_length=512,
            )

            # Start analysis and get metadata
            self.metadata = self.analyzer.start()

            # Initialize spectrogram data array with noise floor value
            num_time_frames = self.metadata['num_time_frames']
            num_freq_bins = len(self.metadata['frequencies'])
            self.spectrogram_data = np.full((num_time_frames, num_freq_bins), -140.0, dtype=np.float32)
            self._last_displayed_frame = 0

            # Configure plot axes based on metadata
            self._configure_axes()

        except Exception as e:
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
        if 0 <= frame_index < self.spectrogram_data.shape[0]:
            # Only lock for the row update
            with self.data_lock:
                end_idx = min(len(magnitudes_db), self.spectrogram_data.shape[1])
                self.spectrogram_data[frame_index, :end_idx] = magnitudes_db[:end_idx]
                self._last_displayed_frame = max(self._last_displayed_frame, frame_index + 1)

        QTimer.singleShot(0, self._update_display)

    def _update_display(self) -> None:
        """
        Update the display with new spectrogram data.
        This runs on a timer to provide smooth progressive updates.
        """
        if self.spectrogram_data is None or not self.metadata:
            return

        # Display only the frames that have been processed so far
        current_data = self.spectrogram_data[:self._last_displayed_frame]
        self.image_item.setImage(current_data, levels=(-120, 0), autoRange=False)
        duration = self.metadata['duration']
        frequencies = self.metadata['frequencies']

        time_extent = duration
        if self.spectrogram_data is not None:
            time_extent *= (self._last_displayed_frame / self.spectrogram_data.shape[0])

        rect = [
            0,  # x start (time=0)
            frequencies[0],  # y start (lowest freq, bottom of display)
            time_extent,  # width (time extent so far)
            frequencies[-1] - frequencies[0]  # height (freq extent)
        ]
        self.image_item.setRect(*rect)

    def _on_analysis_complete(self) -> None:
        """Called when streaming analysis is complete."""
        self._update_display()
        self.analysis_complete.emit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Clean up when the widget is closed."""
        if self.analyzer:
            self.analyzer.stop()
        super().closeEvent(event)

    def load_audio(self, path: str):
        """Load a new audio file and reset the spectrogram viewer."""
        # Stop current analysis and timer
        if self.analyzer:
            self.analyzer.stop()
            self.analyzer = None

        self.spectrogram_data = None
        self.metadata = {}
        self.audio_path = path

        # Clear plot and update title
        self.plot_widget.setTitle(self.audio_path)
        self.image_item.clear()

        # Start new analysis
        self._start_analysis()

        # Ensure axes and limits are updated for new file
        self._configure_axes()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Accept only if at least one file is an audio file
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")):
                self.load_audio(url.toLocalFile())
                break
        event.accept()
