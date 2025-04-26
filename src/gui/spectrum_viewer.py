"""A module containing a widget for displaying a spectrogram of an audio file."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QWidget

from analyzers.spectrum_analyzer import SpectrumAnalyzer


class SpectrumViewer(QWidget):
    """
    A widget for displaying a spectrogram of an audio file.
    This widget inherits from QWidget and sets up a layout with a label
    for displaying the spectrogram image. It initializes the SpectrumAnalyzer
    with the provided file path and retrieves the spectrogram image.
    The spectrogram is displayed in the label and scaled to fit the widget.
    """
    def __init__(self, parent: QStackedWidget, path: str) -> None:
        super().__init__(parent)

        self.spectrogram_label = QLabel()
        self.hBoxLayout = QHBoxLayout(self)

        self.hBoxLayout.addWidget(self.spectrogram_label)
        self.setLayout(self.hBoxLayout)

        self._init_analyzer(path)

    def _init_analyzer(self, path: str) -> None:
        analyzer = SpectrumAnalyzer(path)

        spectrogram = analyzer.create_spectrogram()
        spectrogram = spectrogram.scaled(600, 300)

        self.spectrogram_label.setPixmap(spectrogram)
        self.spectrogram_label.setScaledContents(1)
