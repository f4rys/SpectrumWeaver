"""A module containing the custom title bar for the SpectrumWeaver application."""

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qframelesswindow import TitleBar

if TYPE_CHECKING:
    from spectrum_weaver import SpectrumWeaver


class CustomTitleBar(TitleBar):
    """
    Custom title bar for the application window.
    This class inherits from TitleBar and customizes the title bar
    by removing the default buttons and adding a custom icon and title label.
    It also sets up a layout for the title bar and handles the
    window icon and title changes. minBtn and maxBtn can be optionally disabled.
    """
    def __init__(self, parent: "SpectrumWeaver", show_min_max: bool = True) -> None:
        super().__init__(parent)

        self.setFixedHeight(48)

        # Remove default buttons
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # Add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(32, 32)
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.insertSpacing(0, 12)
        self.hBoxLayout.insertWidget(
            1, self.iconLabel, 0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.window().windowIconChanged.connect(self._set_icon)

        # Add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(
            2, self.titleLabel, 0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.titleLabel.setObjectName("titleLabel")
        self.window().windowTitleChanged.connect(self._set_title)

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if show_min_max:
            self.buttonLayout.addWidget(self.minBtn)
            self.buttonLayout.addWidget(self.maxBtn)
        else:
            self.minBtn.hide()
            self.maxBtn.hide()
        self.buttonLayout.addWidget(self.closeBtn)

        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addStretch(1)

        self.hBoxLayout.addLayout(self.vBoxLayout, 0)

    def _set_title(self, title: str) -> None:
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def _set_icon(self, icon: QIcon) -> None:
        pixmap = icon.pixmap(QSize(28, 28))  # Slightly smaller than label for padding
        self.iconLabel.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
