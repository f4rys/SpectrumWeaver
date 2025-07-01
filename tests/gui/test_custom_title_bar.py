"""Tests for the CustomTitleBar class."""

from collections.abc import Generator

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from src.gui.custom_title_bar import CustomTitleBar


@pytest.fixture
def parent(qtbot: QtBot) -> Generator[QWidget, None, None]:  # noqa: ARG001
    """Fixture to create a simple parent QWidget instance."""
    # Create a parent QWidget for the CustomTitleBar
    widget = QWidget()
    yield widget

    # Cleanup
    try:
        # Close the widget if it's still open
        widget.close()
        widget.deleteLater()
    except RuntimeError:
        # The widget is already closed
        # Exception can be ignored
        pass

@pytest.fixture
def title_bar(parent: QWidget) -> CustomTitleBar:
    """Fixture to create a CustomTitleBar instance with a QWidget parent."""
    return CustomTitleBar(parent)

def test_custom_title_bar_init(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test the initialization of the CustomTitleBar."""
    assert title_bar is not None
    assert title_bar.height() == 48  # noqa: PLR2004
    assert title_bar.parent() is parent

    # Check if default buttons are removed from the main horizontal layout
    assert title_bar.minBtn.parent() is title_bar
    assert title_bar.maxBtn.parent() is title_bar
    assert title_bar.closeBtn.parent() is title_bar

    # Check they are NOT in the main hBoxLayout directly
    assert title_bar.hBoxLayout.indexOf(title_bar.minBtn) == -1
    assert title_bar.hBoxLayout.indexOf(title_bar.maxBtn) == -1
    assert title_bar.hBoxLayout.indexOf(title_bar.closeBtn) == -1

    # Check if icon and title labels are added
    assert isinstance(title_bar.iconLabel, QLabel)
    assert isinstance(title_bar.titleLabel, QLabel)
    assert title_bar.hBoxLayout.indexOf(title_bar.iconLabel) != -1
    assert title_bar.hBoxLayout.indexOf(title_bar.titleLabel) != -1
    assert title_bar.titleLabel.objectName() == "titleLabel"

    # Check if the custom button layout exists and contains the buttons
    assert hasattr(title_bar, "vBoxLayout")
    assert hasattr(title_bar, "buttonLayout")
    assert title_bar.buttonLayout.indexOf(title_bar.minBtn) != -1
    assert title_bar.buttonLayout.indexOf(title_bar.maxBtn) != -1
    assert title_bar.buttonLayout.indexOf(title_bar.closeBtn) != -1
    assert title_bar.vBoxLayout.itemAt(0) is title_bar.buttonLayout

def test_set_title(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test the _set_title method."""
    test_title = "Test Widget Title"

    # Simulate the parent widget title changing, which should trigger the slot
    parent.setWindowTitle(test_title)
    assert title_bar.titleLabel.text() == test_title

def test_set_icon(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test the _set_icon method."""
    # Create a dummy icon
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.GlobalColor.red)
    test_icon = QIcon(pixmap)

    # Simulate the parent widget icon changing
    parent.setWindowIcon(test_icon)

    # Check if the iconLabel has a pixmap set
    assert title_bar.iconLabel.pixmap() is not None
    assert not title_bar.iconLabel.pixmap().isNull()
    # Icon gets scaled to 28x28 as per the implementation
    assert title_bar.iconLabel.pixmap().size() == QSize(28, 28)

def test_fixed_height(title_bar: CustomTitleBar) -> None:
    """Test that the title bar has the correct fixed height."""
    assert title_bar.height() == 48  # noqa: PLR2004
    assert title_bar.minimumHeight() == 48  # noqa: PLR2004
    assert title_bar.maximumHeight() == 48  # noqa: PLR2004

def test_icon_label_properties(title_bar: CustomTitleBar) -> None:
    """Test the icon label properties."""
    assert title_bar.iconLabel.size() == QSize(32, 32)
    assert title_bar.iconLabel.minimumSize() == QSize(32, 32)
    assert title_bar.iconLabel.maximumSize() == QSize(32, 32)

def test_button_layout_properties(title_bar: CustomTitleBar) -> None:
    """Test the button layout properties."""
    assert title_bar.buttonLayout.spacing() == 0
    assert title_bar.buttonLayout.contentsMargins().left() == 0
    assert title_bar.buttonLayout.contentsMargins().top() == 0
    assert title_bar.buttonLayout.contentsMargins().right() == 0
    assert title_bar.buttonLayout.contentsMargins().bottom() == 0
    assert title_bar.buttonLayout.alignment() == Qt.AlignmentFlag.AlignTop

def test_vbox_layout_structure(title_bar: CustomTitleBar) -> None:
    """Test the vertical box layout structure."""
    assert title_bar.vBoxLayout.count() == 2  # noqa: PLR2004
    assert title_bar.vBoxLayout.itemAt(0) is title_bar.buttonLayout

    # Check that the second item is a stretch
    stretch_item = title_bar.vBoxLayout.itemAt(1)
    assert stretch_item is not None
    assert stretch_item.widget() is None  # Stretch items don't have widgets

def test_signal_connections(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test that signal connections work properly."""
    # Test title change signal
    initial_title = "Initial Title"
    parent.setWindowTitle(initial_title)
    assert title_bar.titleLabel.text() == initial_title

    # Test title change again
    new_title = "New Title"
    parent.setWindowTitle(new_title)
    assert title_bar.titleLabel.text() == new_title

def test_layout_widget_order(title_bar: CustomTitleBar) -> None:
    """Test the order of widgets in the main horizontal layout."""
    # The layout should have: spacing, iconLabel, titleLabel, vBoxLayout
    layout = title_bar.hBoxLayout

    # Check that iconLabel comes before titleLabel
    icon_index = layout.indexOf(title_bar.iconLabel)
    title_index = layout.indexOf(title_bar.titleLabel)
    vbox_index = layout.indexOf(title_bar.vBoxLayout)

    assert icon_index != -1
    assert title_index != -1
    assert vbox_index != -1
    assert icon_index < title_index < vbox_index

def test_title_label_adjusts_size(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test that the title label adjusts its size when title changes."""
    # Set a short title
    short_title = "Short"
    parent.setWindowTitle(short_title)
    short_width = title_bar.titleLabel.width()

    # Set a longer title
    long_title = "This is a much longer title"
    parent.setWindowTitle(long_title)
    long_width = title_bar.titleLabel.width()

    # The width should increase for the longer title
    assert long_width >= short_width

def test_empty_title_handling(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test handling of empty title."""
    parent.setWindowTitle("")
    assert title_bar.titleLabel.text() == ""

def test_empty_icon_handling(title_bar: CustomTitleBar, parent: QWidget) -> None:
    """Test handling of empty icon."""
    empty_icon = QIcon()
    parent.setWindowIcon(empty_icon)

    # Should handle empty icon gracefully
    pixmap = title_bar.iconLabel.pixmap()
    assert pixmap is not None
