"""Tests for the SpectrumAnalyzer class."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.analyzers.spectrum_analyzer import SpectrumAnalyzer


@pytest.fixture
def mock_audio_file() -> Generator[str, None, None]:
    """Fixture to create a temporary audio file path."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        yield tmp_file.name
    # Cleanup
    Path(tmp_file.name).unlink(missing_ok=True)


@pytest.fixture
def mock_callback():
    """Fixture to create a mock callback function."""
    return Mock()


@pytest.fixture
def mock_librosa_get_duration():
    """Fixture to mock librosa.get_duration function."""
    with patch('src.analyzers.spectrum_analyzer.librosa.get_duration') as mock:
        mock.return_value = 5.0  # 5 second duration
        yield mock


@pytest.fixture
def mock_librosa_load():
    """Fixture to mock librosa.load function."""
    with patch('src.analyzers.spectrum_analyzer.librosa.load') as mock:
        # Return dummy audio data and sample rate
        audio_data = np.random.random(44100)  # 1 second of random audio at 44100 Hz
        mock.return_value = (audio_data, 44100)
        yield mock


@pytest.fixture
def mock_librosa_stream():
    """Fixture to mock librosa.stream function."""
    with patch('src.analyzers.spectrum_analyzer.librosa.stream') as mock:
        # Create generator that yields chunks of audio data
        def stream_generator():
            for i in range(10):  # Yield 10 chunks
                yield np.random.random(2048)
        
        mock.return_value = stream_generator()
        yield mock


class TestSpectrumAnalyzer:
    """Test cases for the SpectrumAnalyzer class."""

    def test_spectrum_analyzer_init(self, mock_audio_file: str, mock_callback: Mock) -> None:
        """Test the initialization of the SpectrumAnalyzer."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        assert analyzer is not None
        assert analyzer.path == mock_audio_file
        assert analyzer.callback == mock_callback
        assert analyzer.fft_size == 2048  # default
        assert analyzer.hop_length == 512  # default (fft_size // 4)
        assert analyzer.batch_size == 16  # default
        assert analyzer.sample_rate is None  # not loaded yet
        assert not analyzer.is_running

    def test_spectrum_analyzer_init_with_custom_params(self, mock_audio_file: str, mock_callback: Mock) -> None:
        """Test initialization with custom parameters."""
        analyzer = SpectrumAnalyzer(
            path=mock_audio_file,
            callback=mock_callback,
            fft_size=4096,
            hop_length=1024,
            batch_size=32
        )

        assert analyzer.fft_size == 4096
        assert analyzer.hop_length == 1024
        assert analyzer.batch_size == 32

    def test_start_method(self, mock_audio_file: str, mock_callback: Mock, 
                         mock_librosa_get_duration: Mock, mock_librosa_load: Mock) -> None:
        """Test the start method loads metadata correctly."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        # Mock the metadata loading
        mock_librosa_get_duration.return_value = 10.0
        mock_librosa_load.return_value = (np.random.random(44100), 44100)

        metadata = analyzer.start()

        # Verify metadata structure
        assert 'sample_rate' in metadata
        assert 'duration' in metadata
        assert 'total_samples' in metadata
        assert 'fft_size' in metadata
        assert 'hop_length' in metadata
        assert 'frequencies' in metadata
        assert 'num_time_frames' in metadata

        # Verify values
        assert metadata['sample_rate'] == 44100
        assert metadata['duration'] == 10.0
        assert metadata['fft_size'] == 2048
        assert metadata['hop_length'] == 512

        # Verify librosa calls
        mock_librosa_get_duration.assert_called_once_with(path=mock_audio_file)
        mock_librosa_load.assert_called_once_with(mock_audio_file, sr=None, duration=0.1)

    def test_stop_method(self, mock_audio_file: str, mock_callback: Mock) -> None:
        """Test the stop method."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        # Should not raise error even if not running
        analyzer.stop()

        # Simulate running state
        analyzer.is_running = True
        analyzer.stop()

        assert not analyzer.is_running

    def test_already_running_error(self, mock_audio_file: str, mock_callback: Mock,
                                  mock_librosa_get_duration: Mock, mock_librosa_load: Mock) -> None:
        """Test that starting an already running analyzer raises error."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        # Mock first start
        mock_librosa_get_duration.return_value = 5.0
        mock_librosa_load.return_value = (np.random.random(22050), 22050)

        analyzer.start()

        # Try to start again - should raise error
        with pytest.raises(RuntimeError, match="Analyzer is already running"):
            analyzer.start()

    def test_metadata_loading_failure(self, mock_audio_file: str, mock_callback: Mock,
                                     mock_librosa_get_duration: Mock) -> None:
        """Test handling of metadata loading failure."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        # Mock failure
        mock_librosa_get_duration.side_effect = Exception("Failed to load")

        with pytest.raises(RuntimeError, match="Failed to load audio metadata"):
            analyzer.start()

    def test_properties_before_start(self, mock_audio_file: str, mock_callback: Mock) -> None:
        """Test analyzer properties before calling start."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback)

        assert analyzer.sample_rate is None
        assert analyzer.duration is None
        assert analyzer.total_samples is None
        assert not analyzer.is_running
        assert not analyzer.is_finished

    def test_hop_length_default_calculation(self, mock_audio_file: str, mock_callback: Mock) -> None:
        """Test that hop_length defaults to fft_size // 4."""
        analyzer = SpectrumAnalyzer(mock_audio_file, mock_callback, fft_size=8192)

        assert analyzer.hop_length == 2048  # 8192 // 4

    def test_different_file_paths(self, mock_callback: Mock) -> None:
        """Test initialization with different file paths."""
        test_paths = [
            "test.wav",
            "path/to/audio.mp3",
            "C:\\Users\\test\\audio.flac",
            "/usr/local/audio.ogg",
            "",  # Empty path
        ]

        for path in test_paths:
            analyzer = SpectrumAnalyzer(path, mock_callback)
            assert analyzer.path == path
