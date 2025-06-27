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
                 fft_size: int = 2048, hop_length: Optional[int] = None):
        """
        Initialize the streaming spectrum analyzer.

        Args:
            path: Path to audio file
            callback: Function to call with (sample_index, fft_magnitudes) for each FFT result
            fft_size: Size of FFT window (power of 2)
            hop_length: Number of samples between successive frames
        """
        self.path = path
        self.callback = callback
        self.fft_size = fft_size
        self.hop_length = hop_length or fft_size // 4

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

            # Use Nyquist frequency
            self._freq_bins = np.fft.rfftfreq(self.fft_size, 1 / self.sample_rate)

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
        Sends batches of frames for vectorized FFT processing.
        """
        try:
            chunk_size = self.hop_length * 50  # Process 50 frames at a time
            stream = librosa.stream(self.path, block_length=1, frame_length=chunk_size, 
                                  hop_length=chunk_size, mono=True)
            buffer = np.array([])
            frame_index = 0
            batch_size = 16  # Number of frames per batch
            batch_frames = []
            batch_indices = []
            for chunk in stream:
                if self._stop_event.is_set():
                    break
                if chunk.ndim > 1:
                    chunk = chunk.flatten()
                buffer = np.concatenate([buffer, chunk])
                while len(buffer) >= self.fft_size and not self._stop_event.is_set():
                    frame = buffer[:self.fft_size].copy()
                    batch_frames.append(frame)
                    batch_indices.append(frame_index)
                    frame_index += 1
                    buffer = buffer[self.hop_length:]
                    if len(batch_frames) >= batch_size:
                        # Put batch in queue
                        try:
                            self._audio_queue.put((batch_indices.copy(), np.stack(batch_frames)), timeout=1.0)
                        except queue.Full:
                            pass
                        batch_frames.clear()
                        batch_indices.clear()
            # Put any remaining frames
            if batch_frames:
                try:
                    self._audio_queue.put((batch_indices.copy(), np.stack(batch_frames)), timeout=1.0)
                except queue.Full:
                    pass
            self._audio_queue.put(None)
        except Exception as e:
            print(f"Reader thread error: {e}")
            self._audio_queue.put(None)

    def _fft_worker(self) -> None:
        """
        Worker thread that performs FFT calculations and calls the callback.
        Processes batches of frames for vectorized FFT and dB conversion.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    item = self._audio_queue.get(timeout=1.0)
                    if item is None:
                        break
                    frame_indices, audio_frames = item
                    # audio_frames: shape (batch, fft_size)
                    windowed = audio_frames * self._window_func
                    fft_result = np.fft.rfft(windowed, axis=1)
                    power = np.abs(fft_result) ** 2
                    n2 = self.fft_size * self.fft_size
                    power = power / n2
                    power = np.maximum(power, 1e-12)
                    magnitudes_db = 10.0 * np.log10(power)
                    for idx, frame_index in enumerate(frame_indices):
                        self.callback(frame_index, magnitudes_db[idx])
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
