"""A module containing a widget for displaying a spectrogram of an audio file."""

import pyqtgraph as pg
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QWidget

from analyzers.spectrum_analyzer import SpectrumAnalyzer


class SpectrumViewer(QWidget):
    """
    A widget for displaying a spectrogram of an audio file using pyqtgraph.
    This widget displays the spectrogram with proper time and frequency axes,
    complete with ticks and labels for better visualization.
    """
    def __init__(self, parent: QStackedWidget, path: str) -> None:
        super().__init__(parent)

        # Store the path for use in configuration
        self.audio_path = path

        # Create the plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#202020')

        # Set up the layout
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.plot_widget)
        self.setLayout(self.hBoxLayout)

        # Create the image item for the spectrogram
        self.image_item = pg.ImageItem()
        self.plot_widget.addItem(self.image_item)

        self._configure_plot()
        self._init_analyzer(path)

    def _configure_plot(self) -> None:
        """Configure the plot widget with proper labels and styling."""
        # Set axis labels
        self.plot_widget.setLabel('left', 'Frequency', units='Hz')
        self.plot_widget.setLabel('bottom', 'Time', units='s')

        # Set audio path as the plot title
        self.plot_widget.setTitle(self.audio_path)

        # Show grid
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configure the view
        self.plot_widget.getViewBox().setAspectLocked(False)

        # Disable the right-click context menu
        self.plot_widget.setMenuEnabled(False)

        # Hide auto-scaling button
        self.plot_widget.hideButtons()

        # Set a nice colormap for the spectrogram
        self.image_item.setColorMap('viridis')

    def _init_analyzer(self, path: str) -> None:
        """Initialize the spectrum analyzer and display the spectrogram."""
        try:
            analyzer = SpectrumAnalyzer(path)
            spec_data = analyzer.get_spectrogram_data()

            # Get the spectrogram data
            spectrogram = spec_data['data']
            times = spec_data['times']
            frequencies = spec_data['frequencies']

            # Set the image data with proper axis order
            self.image_item.setImage(spectrogram, autoLevels=True, axisOrder='row-major')

            # Calculate the correct rect for the image
            # The rect defines the coordinate system: (x, y, width, height)
            time_extent = times[-1] - times[0] if len(times) > 1 else 1.0
            freq_extent = frequencies[-1] - frequencies[0] if len(frequencies) > 1 else 1.0

            # Set the rectangle to map image pixels to real coordinates
            # For row-major: x=time, y=frequency
            rect = [times[0], frequencies[0], time_extent, freq_extent]
            self.image_item.setRect(*rect)

            # Set the view range to show the entire spectrogram
            self.plot_widget.setXRange(times[0], times[-1])
            self.plot_widget.setYRange(frequencies[0], frequencies[-1])
            self.plot_widget.setLimits(xMin=times[0], xMax=times[-1], yMin=frequencies[0], yMax=frequencies[-1])

        except Exception as e:
            print(f"Error displaying spectrogram: {e}")
            # Display error message in the plot
            self.plot_widget.setTitle(f'Error loading spectrogram: {str(e)}')
