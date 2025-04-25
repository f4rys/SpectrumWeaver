"""A module containing SpectrumAnalyzer class for generating spectrograms."""

import librosa
import matplotlib.pyplot as plt
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtGui import QImage, QPixmap


class SpectrumAnalyzer:
    """
    A class for analyzing audio files and generating spectrograms.
    This class uses the librosa library to load audio files and generate
    spectrograms. It provides methods to create and retrieve the spectrogram
    as a QPixmap for display in a PyQt application.
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.y, self.sr = librosa.load(self.path)
        self.stft = librosa.stft(self.y)
        self.spectrogram = np.abs(self.stft) ** 2

    def create_spectrogram(self) -> QPixmap:
        """
        Create a spectrogram from the audio data using librosa and matplotlib.
        The spectrogram is generated using the Short-Time Fourier Transform (STFT)
        and is displayed using matplotlib's specgram function.
        """
        # Load audio data using librosa
        y, sr = librosa.load(self.path)

        # Generate spectrogram using matplotlib
        fig, ax = plt.subplots()
        P, a, b, c = plt.specgram(y, Fs=sr)  # noqa: N806
        plt.close(fig)

        # Convert the spectrogram to a QImage
        qimage = QImage(P.shape[1], P.shape[0], QImage.Format.Format_Grayscale8)
        for i in range(P.shape[0]):
            for j in range(P.shape[1]):
                qimage.setPixelColor(j, i, QtCore.Qt.GlobalColor.gray())

        # Convert the QImage to a QPixmap
        return QPixmap.fromImage(qimage)
