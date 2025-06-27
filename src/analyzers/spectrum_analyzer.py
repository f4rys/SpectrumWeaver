"""A module containing the SpectrumAnalyzer class for real-time audio spectrum analysis."""

import queue
import threading
from typing import Optional, Callable, Dict, Any

import librosa
import numpy as np
from scipy import signal
from PySide6.QtWidgets import QMessageBox


class SpectrumAnalyzer:
    """
    A streaming spectrum analyzer that processes audio in chunks and computes FFT in real-time.
    This class uses threading to read audio data and perform FFT calculations concurrently.
    It supports a callback mechanism to return FFT results for each frame, allowing for real-time visualization.
    The analyzer can handle large audio files without loading them entirely into memory, making it suitable for long recordings.
    It uses a Hann window function by default for spectral analysis, which is common in audio processing.
    """
    def __init__(self, path: str, callback: Callable[[int, np.ndarray], None], 
                 fft_size: int = 2048, hop_length: Optional[int] = None, 
                 max_freq: Optional[float] = None):
        """
        Initialize the streaming spectrum analyzer.

        Args:
            path: Path to audio file
            callback: Function to call with (sample_index, fft_magnitudes) for each FFT result
            fft_size: Size of FFT window (power of 2)
            hop_length: Number of samples between successive frames
            max_freq: Maximum frequency to display (None for Nyquist)
        """
        self.path = path
        self.callback = callback
        self.fft_size = fft_size
        self.hop_length = hop_length or fft_size // 4
        self.max_freq = max_freq

        # Audio properties
        self.sample_rate: Optional[int] = None
        self.duration: Optional[float] = None
        self.total_samples: Optional[int] = None

        # Processing state
        self.is_running = False
        self.is_finished = False
        self._stop_event = threading.Event()

        # Threads
        self._reader_thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None

        # Thread communication
        self._audio_queue = queue.Queue(maxsize=10)

        # Pre-compute Hann window function and frequency bins
        self._window_func = signal.windows.hann(self.fft_size)
        self._freq_bins: Optional[np.ndarray] = None

    def start(self) -> Dict[str, Any]:
        """
        Start the streaming analysis.

        Returns:
            Dict containing audio metadata
        """
        if self.is_running:
            raise RuntimeError("Analyzer is already running")

        # Load audio metadata first
        try:
            # Get duration without loading audio data
            self.duration = librosa.get_duration(path=self.path)
            
            # Load a small sample to get sample rate
            _, sr = librosa.load(self.path, sr=None, duration=0.1)
            self.sample_rate = sr
            self.total_samples = int(self.duration * self.sample_rate)

            # Set up frequency bins
            self._freq_bins = np.fft.rfftfreq(self.fft_size, 1/self.sample_rate)
            if self.max_freq:
                # Find the index of the maximum frequency
                max_freq_idx = np.searchsorted(self._freq_bins, self.max_freq)
                self._freq_bins = self._freq_bins[:max_freq_idx]

        except Exception as e:
            raise RuntimeError(f"Failed to load audio metadata: {e}")

        # Start threads
        self.is_running = True
        self.is_finished = False
        self._stop_event.clear()

        self._reader_thread = threading.Thread(target=self._reader_worker, daemon=True)
        self._worker_thread = threading.Thread(target=self._fft_worker, daemon=True)

        self._reader_thread.start()
        self._worker_thread.start()

        return {
            'sample_rate': self.sample_rate,
            'duration': self.duration,
            'total_samples': self.total_samples,
            'fft_size': self.fft_size,
            'hop_length': self.hop_length,
            'frequencies': self._freq_bins.copy(),
            'num_time_frames': (self.total_samples - self.fft_size) // self.hop_length + 1
        }

    def stop(self) -> None:
        """Stop the streaming analysis."""
        if not self.is_running:
            return

        self._stop_event.set()
        self.is_running = False

        # Wait for threads to finish
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2.0)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    def _reader_worker(self) -> None:
        """
        Reader thread that loads audio data in chunks and feeds it to the FFT worker.
        """
        try:
            # Buffer for overlapping windows
            chunk_size = self.hop_length * 50  # Process 50 frames at a time

            # Stream audio in chunks
            stream = librosa.stream(self.path, block_length=1, frame_length=chunk_size, 
                                  hop_length=chunk_size, mono=True)

            buffer = np.array([])
            frame_index = 0

            for chunk in stream:
                if self._stop_event.is_set():
                    break

                # Flatten chunk if needed
                if chunk.ndim > 1:
                    chunk = chunk.flatten()

                # Add to buffer
                buffer = np.concatenate([buffer, chunk])

                # Process complete frames
                while len(buffer) >= self.fft_size and not self._stop_event.is_set():
                    # Extract frame
                    frame = buffer[:self.fft_size].copy()

                    # Put frame in queue (with timeout to avoid blocking)
                    try:
                        self._audio_queue.put((frame_index, frame), timeout=1.0)
                        frame_index += 1
                    except queue.Full:
                        # Skip this frame if queue is full (backpressure)
                        pass

                    # Advance buffer
                    buffer = buffer[self.hop_length:]

            # Signal end of data
            self._audio_queue.put(None)

        except Exception as e:
            print(f"Reader thread error: {e}")
            self._audio_queue.put(None)

    def _fft_worker(self) -> None:
        """
        Worker thread that performs FFT calculations and calls the callback.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Get audio frame from queue
                    item = self._audio_queue.get(timeout=1.0)
                    if item is None:  # End of data signal
                        break

                    frame_index, audio_frame = item

                    # Apply window function
                    windowed_frame = audio_frame * self._window_func

                    # Compute FFT
                    fft_result = np.fft.rfft(windowed_frame)

                    # Convert to magnitude in dB
                    magnitudes = np.abs(fft_result)
                    # Avoid log(0) by adding a small epsilon
                    magnitudes = np.maximum(magnitudes, 1e-10)
                    magnitudes_db = 20 * np.log10(magnitudes)

                    # Limit frequency range if specified
                    if self.max_freq and len(magnitudes_db) > len(self._freq_bins):
                        magnitudes_db = magnitudes_db[:len(self._freq_bins)]

                    # Call the callback with results
                    self.callback(frame_index, magnitudes_db)

                except queue.Empty:
                    continue  # Timeout, check stop event and continue

        except Exception as e:
            QMessageBox.critical(None, "Error", f"FFT worker thread error: {e}")
        finally:
            self.is_finished = True
            # Notify that processing is complete
            try:
                self.callback(-1, np.array([]))  # End signal
            except Exception:
                QMessageBox.critical(None, "Error", "Failed to send end signal to callback")
