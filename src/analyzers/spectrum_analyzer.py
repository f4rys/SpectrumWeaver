"""A module containing SpectrumAnalyzer class for generating spectrograms."""

from pathlib import Path

import librosa
import numpy as np


class SpectrumAnalyzer:
    """
    A class for analyzing audio files and generating spectrograms.
    This class uses the librosa library to load audio files and generate
    spectrograms.
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.y = None
        self.sr = None
        self.stft = None
        self.spectrogram_db = None
        self.times = None
        self.frequencies = None
        self.duration = None

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

            # Calculate time and frequency axes
            self.duration = len(self.y) / self.sr
            self.times = librosa.frames_to_time(
                np.arange(self.stft.shape[1]), sr=self.sr
            )
            self.frequencies = librosa.fft_frequencies(sr=self.sr)

            print(f"Successfully processed audio file: {self.path}")
            print(f"Duration: {self.duration:.2f}s, Frequency range: 0-{self.frequencies[-1]:.0f}Hz")

        except librosa.LibrosaError as e:
            print(f"Librosa error processing {self.path}: {e}")
            raise RuntimeError(f"Audio processing error: {e}") from e
        except Exception as e:
            print(f"Unexpected error processing {self.path}: {e}")
            raise

    def get_spectrogram_data(self) -> dict:
        """
        Get raw spectrogram data for display with proper axes.
        """
        try:
            if self.spectrogram_db is None:
                raise RuntimeError("Spectrogram data not available. Audio processing may have failed.")
            
            return {
                'data': self.spectrogram_db,
                'times': self.times,
                'frequencies': self.frequencies,
                'duration': self.duration,
                'sample_rate': self.sr,
                'shape': self.spectrogram_db.shape
            }

        except Exception as e:
            print(f"Error getting spectrogram data: {e}")
            raise
