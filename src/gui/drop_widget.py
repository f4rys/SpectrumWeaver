"""A module containing the custom drop widget for the SpectrumWeaver application."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from spectrum_weaver import SpectrumWeaver


class DropWidget(QWidget):
    """
    A custom widget that allows users to drag and drop files onto it.
    This widget inherits from QWidget and sets up a layout with a label
    indicating that files can be dropped here. It also accepts drag and drop
    events and handles them accordingly.
    """
    SUPPORTED_FORMATS = {
        '.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', 
        '.wma', '.au', '.aiff', '.aif'
    }
    
    def __init__(self, parent_window: "SpectrumWeaver") -> None:
        super().__init__()
        self.parent_window = parent_window        
        self.label = QLabel("Drop file here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.vlayout = QVBoxLayout(self)
        self.vlayout.addWidget(self.label)
        
        self.setLayout(self.vlayout)
        self.setAcceptDrops(True)

    def _is_supported_audio_file(self, file_path: str) -> bool:
        """Check if the file has a supported audio format."""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            return file_extension in self.SUPPORTED_FORMATS
        except (AttributeError, IndexError):
            return False

    def _is_file_accessible(self, file_path: str) -> bool:
        """Check if the file exists and is readable."""
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and os.access(file_path, os.R_OK)
        except (OSError, PermissionError):
            return False

    def _show_error_message(self, title: str, message: str) -> None:
        """Display an error message to the user."""
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Icon.Warning)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_box.exec()

    def _validate_dropped_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validate the dropped file and return validation result.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self._is_file_accessible(file_path):
            return False, f"File not accessible or does not exist:\n{file_path}"
        
        if not self._is_supported_audio_file(file_path):
            supported_formats = ", ".join(sorted(self.SUPPORTED_FORMATS))
            return False, f"Unsupported file format.\n\nSupported formats: {supported_formats}"
        
        return True, ""

    def _handle_drag_event(self, event: QDragEnterEvent) -> None:
        """Handle common drag event logic with file validation."""
        if event.mimeData().hasUrls():
            # Check if at least one file has a supported format
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if self._is_supported_audio_file(file_path):
                        event.acceptProposedAction()
                        return
            
            # No supported files found
            event.ignore()
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
        try:
            if not event.mimeData().hasUrls():
                event.ignore()
                return

            event.acceptProposedAction()
            url = event.mimeData().urls()[0]

            if not url.isLocalFile():
                self._show_error_message(
                    "Invalid File", 
                    "Only local files are supported. Please drag a file from your computer."
                )
                event.ignore()
                return

            file_path = url.toLocalFile()
            
            # Validate the dropped file
            is_valid, error_message = self._validate_dropped_file(file_path)
            if not is_valid:
                self._show_error_message("File Error", error_message)
                event.ignore()
                return

            # File is valid, proceed to show spectrum viewer
            try:
                self.parent_window.show_spectrum_viewer(file_path)
            except Exception as e:
                self._show_error_message(
                    "Processing Error", 
                    f"Failed to process the audio file:\n{str(e)}"
                )
                event.ignore()

        except Exception as e:
            self._show_error_message(
                "Unexpected Error", 
                f"An unexpected error occurred while processing the dropped file:\n{str(e)}"
            )
            event.ignore()
