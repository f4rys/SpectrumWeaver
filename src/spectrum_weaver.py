"""A module containing the main application class for SpectrumWeaver."""

import sys
from pathlib import Path

from PySide6.QtCore import QFile, QTextStream
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QStackedWidget, QMessageBox
from qframelesswindow import FramelessWindow

from assets import resources  # noqa: F401
from gui.custom_title_bar import CustomTitleBar
from gui.spectrum_viewer import SpectrumViewer


class SpectrumWeaver(FramelessWindow):
    """
    Main application window for SpectrumWeaver.
    Inherits from FramelessWindow to provide a custom
    title bar and window frame. Sets up the layout and initializes
    the spectrum viewer for file handling.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 40, 20, 20)

        self.stacked_widget = QStackedWidget(self)
        self.spectrum_viewer = SpectrumViewer(self)
        self.stacked_widget.addWidget(self.spectrum_viewer)
        self.stacked_widget.setCurrentWidget(self.spectrum_viewer)

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
            # First try to load from Qt resources (works in both dev and packaged)
            qss_file = QFile(":/styles/styles.qss")
            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                stylesheet_content = stream.readAll()
                qss_file.close()
                self.setStyleSheet(stylesheet_content)
                print("Loaded stylesheet from Qt resources")
                return
            
            # Fallback to file system paths
            stylesheet_paths = [
                Path("assets/styles.qss"),  # Packaged environment
                Path("src/assets/styles.qss"),  # Development environment
                Path(__file__).parent / "assets" / "styles.qss",  # Relative to this file
            ]
            
            stylesheet_content = None
            for stylesheet_path in stylesheet_paths:
                if stylesheet_path.exists():
                    with stylesheet_path.open(encoding="utf-8") as f:
                        stylesheet_content = f.read()
                    print(f"Loaded stylesheet from file: {stylesheet_path}")
                    break
            
            if stylesheet_content:
                self.setStyleSheet(stylesheet_content)
            else:
                print("Warning: No stylesheet found, using default styling")
                # Apply basic dark theme as fallback
                self.setStyleSheet("""
                    QWidget {
                        background-color: rgb(32, 32, 32);
                        color: white;
                    }
                    SpectrumWeaver {
                        background-color: rgb(32, 32, 32);
                    }
                """)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            # Apply basic dark theme as fallback
            self.setStyleSheet("""
                QWidget {
                    background-color: rgb(32, 32, 32);
                    color: white;
                }
                SpectrumWeaver {
                    background-color: rgb(32, 32, 32);
                }
            """)

    def show_spectrum_viewer(self, path: str) -> None:
        """
        Show the spectrum viewer when a file is dropped.
        """
        try:
            self.spectrum_viewer.load_audio(path)
            self.stacked_widget.setCurrentWidget(self.spectrum_viewer)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load audio file:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    spectrum_weaver = SpectrumWeaver()
    spectrum_weaver.show()
    app.exec()
