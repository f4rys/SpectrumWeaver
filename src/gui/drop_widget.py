"""A module containing the custom drop widget for the SpectrumWeaver application."""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from spectrum_weaver import SpectrumWeaver


class DropWidget(QWidget):
    """
    A custom widget that allows users to drag and drop files onto it.
    This widget inherits from QWidget and sets up a layout with a label
    indicating that files can be dropped here. It also accepts drag and drop
    events and handles them accordingly.
    """
    def __init__(self, parent: "SpectrumWeaver") -> None:
        super().__init__(parent)

        self.label = QLabel("Drop file here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.addWidget(self.label)

        self.setLayout(self.vlayout)
        self.setAcceptDrops(True)

    def _handle_drag_event(self, event: QDragEnterEvent) -> None:
        """Handle common drag event logic."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        """Handle drag enter events."""
        self._handle_drag_event(event)

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        """Handle drag move events."""
        self._handle_drag_event(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        """Handle drop events to process the dropped file."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            url = event.mimeData().urls()[0]

            if url.isLocalFile():
                file_path = url.toLocalFile()
                self.parent().show_spectrum_viewer(file_path)
        else:
            event.ignore()
