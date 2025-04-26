"""A module containing SpectrumAnalyzer class for generating spectrograms."""

import librosa
import numpy as np
from PySide6.QtGui import QImage, QPixmap


class SpectrumAnalyzer:
    """
    A class for analyzing audio files and generating spectrograms.
    This class uses the librosa library to load audio files and generate
    spectrograms. It provides methods to create and retrieve the spectrogram
    as a QPixmap for display in a PySide6 application.
    """
    def __init__(self, path: str) -> None:
        self.path = path

        # Load audio file, preserving the original sample rate
        self.y, self.sr = librosa.load(self.path, sr=None)

        # Compute Short-Time Fourier Transform (STFT)
        self.stft = librosa.stft(self.y)

        # Convert amplitude spectrogram to dB-scaled spectrogram
        self.spectrogram_db = librosa.amplitude_to_db(np.abs(self.stft), ref=np.max)

    def create_spectrogram(self) -> QPixmap:
        """Create a QPixmap from the pre-calculated dB-scaled spectrogram."""
        # Normalize the spectrogram data to 0-255 for grayscale image
        spec_min = self.spectrogram_db.min()
        spec_max = self.spectrogram_db.max()

        # Handle potential division by zero if max and min are the same (e.g., silence)
        if spec_max == spec_min:
            normalized_spectrogram = np.zeros_like(
                self.spectrogram_db, dtype=np.uint8)
        else:
            # Normalize the data to the 0-255 range
            normalized_spectrogram = (255 * (self.spectrogram_db - spec_min) / (
                spec_max - spec_min)).astype(np.uint8)

        # Get dimensions (frequency bins, time frames)
        height, width = normalized_spectrogram.shape

        # Flip the array vertically for standard spectrogram display
        flipped_spectrogram = np.flipud(normalized_spectrogram)

        # Ensure the data is contiguous in memory
        contiguous_spectrogram = np.ascontiguousarray(flipped_spectrogram)

        # Create QImage directly from the numpy array buffer
        # Format_Grayscale8 expects 8-bit grayscale data.
        # The bytesPerLine is the width for grayscale8 format.
        qimage = QImage(contiguous_spectrogram.data, width,
                        height, width, QImage.Format.Format_Grayscale8)

        # Create a deep copy to ensure the QImage owns its data
        qimage_copy = qimage.copy()

        # Convert the QImage to a QPixmap
        return QPixmap.fromImage(qimage_copy)
