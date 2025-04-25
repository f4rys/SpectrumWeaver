"""A module containing the custom drop widget for the SpectrumWeaver application."""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
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
