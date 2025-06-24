"""A module containing the main application class for SpectrumWeaver."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QStackedWidget
from qframelesswindow import FramelessWindow

from assets import resources  # noqa: F401
from gui.custom_title_bar import CustomTitleBar
from gui.drop_widget import DropWidget
from gui.spectrum_viewer import SpectrumViewer


class SpectrumWeaver(FramelessWindow):
    """
    Main application window for SpectrumWeaver.
    Inherits from FramelessWindow to provide a custom
    title bar and window frame. Sets up the layout and initializes
    the drop widget for file handling. Also includes a method to
    show the spectrum viewer when a file is dropped.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 40, 20, 20)

        self.stacked_widget = QStackedWidget(self)
        self.drop_widget = DropWidget(self)

        self.stacked_widget.addWidget(self.drop_widget)

        self._init_window()
        self._set_qss()

    def _init_window(self) -> None:
        self.setWindowTitle("SpectrumWeaver")
        self.setWindowIcon(QIcon(":/icon/icon.png"))

        self.hBoxLayout.addWidget(self.stacked_widget)
        self.setLayout(self.hBoxLayout)

        self.resize(640, 480)

    def _set_qss(self) -> None:
        try:
            stylesheet_path = Path("src/assets/styles.qss")
            if not stylesheet_path.exists():
                print(f"Warning: Stylesheet not found at {stylesheet_path}")
                return
                
            with stylesheet_path.open(encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except (OSError, IOError) as e:
            print(f"Warning: Could not load stylesheet: {e}")
        except Exception as e:
            print(f"Unexpected error loading stylesheet: {e}")

    def show_spectrum_viewer(self, path: str) -> None:
        """
        Show the spectrum viewer when a file is dropped.
        This method is called from the DropWidget when a file is dropped.
        It initializes the SpectrumViewer with the dropped file path
        and adds it to the stacked widget.

        Args:
            path (str): The file path of the dropped file.
        """
        try:
            self.spectrum_viewer = SpectrumViewer(self, path)
            self.stacked_widget.addWidget(self.spectrum_viewer)
            self.stacked_widget.setCurrentWidget(self.spectrum_viewer)
        except Exception as e:
            print(f"Error creating spectrum viewer: {e}")
            # Could also show an error dialog here
            raise  # Re-raise so the DropWidget can handle it


if __name__ == "__main__":
    app = QApplication(sys.argv)
    spectrum_weaver = SpectrumWeaver()
    spectrum_weaver.show()
    app.exec()
