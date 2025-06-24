"""A module containing SpectrumAnalyzer class for generating spectrograms."""

from pathlib import Path

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
        self.y = None
        self.sr = None
        self.stft = None
        self.spectrogram_db = None
        
        try:
            self._load_and_process_audio()
        except Exception as e:
            print(f"Failed to initialize SpectrumAnalyzer for file {path}: {e}")
            raise RuntimeError(f"Could not process audio file: {e}") from e

    def _load_and_process_audio(self) -> None:
        """Load audio file and compute spectrogram data."""
        try:
            # Validate file exists
            if not Path(self.path).exists():
                raise FileNotFoundError(f"Audio file not found: {self.path}")
            
            # Load audio file, preserving the original sample rate
            self.y, self.sr = librosa.load(self.path, sr=None)
            
            # Validate audio data
            if self.y is None or len(self.y) == 0:
                raise ValueError("Audio file contains no data or is corrupted")
            
            if self.sr is None or self.sr <= 0:
                raise ValueError("Invalid sample rate detected in audio file")
            
            # Compute Short-Time Fourier Transform (STFT)
            self.stft = librosa.stft(self.y)
            
            # Convert amplitude spectrogram to dB-scaled spectrogram
            self.spectrogram_db = librosa.amplitude_to_db(np.abs(self.stft), ref=np.max)
            
            print(f"Successfully processed audio file: {self.path}")
            
        except librosa.LibrosaError as e:
            print(f"Librosa error processing {self.path}: {e}")
            raise RuntimeError(f"Audio processing error: {e}") from e
        except Exception as e:
            print(f"Unexpected error processing {self.path}: {e}")
            raise

    def create_spectrogram(self) -> QPixmap:
        """Create a QPixmap from the pre-calculated dB-scaled spectrogram."""
        try:
            if self.spectrogram_db is None:
                raise RuntimeError("Spectrogram data not available. Audio processing may have failed.")
            
            # Normalize the spectrogram data to 0-255 for grayscale image
            spec_min = self.spectrogram_db.min()
            spec_max = self.spectrogram_db.max()

            # Handle potential division by zero if max and min are the same (e.g., silence)
            if spec_max == spec_min:
                print("Detected silent audio or constant amplitude - creating blank spectrogram")
                normalized_spectrogram = np.zeros_like(
                    self.spectrogram_db, dtype=np.uint8)
            else:
                # Normalize the data to the 0-255 range
                normalized_spectrogram = (255 * (self.spectrogram_db - spec_min) / (
                    spec_max - spec_min)).astype(np.uint8)

            # Get dimensions (frequency bins, time frames)
            height, width = normalized_spectrogram.shape
            
            if height == 0 or width == 0:
                raise ValueError("Invalid spectrogram dimensions")

            # Flip the array vertically for standard spectrogram display
            flipped_spectrogram = np.flipud(normalized_spectrogram)

            # Ensure the data is contiguous in memory
            contiguous_spectrogram = np.ascontiguousarray(flipped_spectrogram)

            # Create QImage directly from the numpy array buffer
            # Format_Grayscale8 expects 8-bit grayscale data.
            # The bytesPerLine is the width for grayscale8 format.
            qimage = QImage(contiguous_spectrogram.data, width,
                            height, width, QImage.Format.Format_Grayscale8)

            if qimage.isNull():
                raise RuntimeError("Failed to create QImage from spectrogram data")

            # Create a deep copy to ensure the QImage owns its data
            qimage_copy = qimage.copy()

            # Convert the QImage to a QPixmap
            pixmap = QPixmap.fromImage(qimage_copy)
            
            if pixmap.isNull():
                raise RuntimeError("Failed to create QPixmap from QImage")
            
            print(f"Successfully created spectrogram: {width}x{height}")
            return pixmap
            
        except Exception as e:
            print(f"Error creating spectrogram: {e}")
            # Return a simple error pixmap instead of crashing
            error_pixmap = QPixmap(300, 150)
            error_pixmap.fill()  # Fill with white
            return error_pixmap
