"""Tests for the custom axis items module."""

import pyqtgraph as pg
from pytestqt.qtbot import QtBot

from src.gui.custom_axes_items import TimeAxisItem, FreqAxisItem


class TestTimeAxisItem:
    """Test cases for the TimeAxisItem class."""

    def test_time_axis_item_initialization(self, qtbot: QtBot) -> None:
        """Test that TimeAxisItem can be initialized."""
        axis = TimeAxisItem(orientation='bottom')
        assert isinstance(axis, pg.AxisItem)
        assert isinstance(axis, TimeAxisItem)

    def test_tick_strings_formatting(self, qtbot: QtBot) -> None:
        """Test that tick strings are formatted correctly for time display."""
        axis = TimeAxisItem(orientation='bottom')

        # Test various time values
        test_values = [0, 30, 60, 90, 120, 150, 3600, 3661]
        expected = ["0:00", "0:30", "1:00", "1:30", "2:00", "2:30", "60:00", "61:01"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_with_fractional_seconds(self, qtbot: QtBot) -> None:
        """Test tick string formatting with fractional seconds."""
        axis = TimeAxisItem(orientation='bottom')

        # Test fractional values (should be truncated to integers)
        test_values = [0.5, 30.7, 59.9, 120.1]
        expected = ["0:00", "0:30", "0:59", "2:00"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_with_large_values(self, qtbot: QtBot) -> None:
        """Test tick string formatting with large time values."""
        axis = TimeAxisItem(orientation='bottom')

        # Test large values
        test_values = [7200, 86400]  # 2 hours, 24 hours
        expected = ["120:00", "1440:00"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_with_negative_values(self, qtbot: QtBot) -> None:
        """Test tick string formatting with negative values."""
        axis = TimeAxisItem(orientation='bottom')

        # Test negative values
        test_values = [-30, -60]
        expected = ["-0:30", "-1:00"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected


class TestFreqAxisItem:
    """Test cases for the FreqAxisItem class."""

    def test_freq_axis_item_initialization(self, qtbot: QtBot) -> None:
        """Test that FreqAxisItem can be initialized."""
        axis = FreqAxisItem(orientation='left')
        assert isinstance(axis, pg.AxisItem)
        assert isinstance(axis, FreqAxisItem)

    def test_tick_strings_formatting_hz(self, qtbot: QtBot) -> None:
        """Test that tick strings are formatted correctly for frequency in Hz."""
        axis = FreqAxisItem(orientation='left')

        # Test values below 1000 Hz
        test_values = [0, 100, 500, 999]
        expected = ["0 kHz", "0.1 kHz", "0.5 kHz", "1.0 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_formatting_khz(self, qtbot: QtBot) -> None:
        """Test that tick strings are formatted correctly for frequency in kHz."""
        axis = FreqAxisItem(orientation='left')

        # Test values at and above 1000 Hz
        test_values = [1000, 2000, 5500, 22050]
        expected = ["1 kHz", "2 kHz", "5 kHz", "22 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_with_zero(self, qtbot: QtBot) -> None:
        """Test tick string formatting with zero frequency."""
        axis = FreqAxisItem(orientation='left')

        test_values = [0]
        expected = ["0 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_with_fractional_khz(self, qtbot: QtBot) -> None:
        """Test tick string formatting with fractional kHz values."""
        axis = FreqAxisItem(orientation='left')

        # Test fractional kHz values (should show as integers for >= 1000)
        test_values = [1500, 2250, 8820]
        expected = ["1 kHz", "2 kHz", "8 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_mixed_values(self, qtbot: QtBot) -> None:
        """Test tick string formatting with mixed Hz and kHz values."""
        axis = FreqAxisItem(orientation='left')

        test_values = [0, 250, 500, 1000, 2000, 11025, 22050]
        expected = ["0 kHz", "0.2 kHz", "0.5 kHz", "1 kHz", "2 kHz", "11 kHz", "22 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected

    def test_tick_strings_precision(self, qtbot: QtBot) -> None:
        """Test tick string formatting precision for small Hz values."""
        axis = FreqAxisItem(orientation='left')

        # Test values that should show decimal precision
        test_values = [123, 456, 789]
        expected = ["0.1 kHz", "0.5 kHz", "0.8 kHz"]

        result = axis.tickStrings(test_values, scale=1, spacing=1)
        assert result == expected
