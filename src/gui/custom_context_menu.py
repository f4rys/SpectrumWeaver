"""A module containing CustomContextMenu class for spectrum viewer actions."""

import os
from typing import Optional

import numpy as np
import humanize
from mutagen import File as MutagenFile
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import (QMenu, QWidget, QFileDialog, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QPushButton, QDialog, QVBoxLayout)


class CustomContextMenu:
    """
    A reusable context menu for spectrum viewer actions.
    Handles export and details logic directly.
    """
    def __init__(
        self,
        parent: Optional[QWidget],
        plot_widget,
        image_item,
        audio_path: str,
        spectrogram_data: Optional[np.ndarray],
        metadata: dict
    ):
        self.parent = parent
        self.plot_widget = plot_widget
        self.image_item = image_item
        self.audio_path = audio_path
        self.spectrogram_data = spectrogram_data
        self.metadata = metadata

    def exec(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self.parent)
        export_action = menu.addAction("Export spectrogram to PNG")
        details_action = menu.addAction("Show details")
        action = menu.exec(event.globalPos())

        if action == export_action:
            self._export_spectrogram_png()
        elif action == details_action:
            self._show_details_dialog()

    def _export_spectrogram_png(self):
        if self.spectrogram_data is None:
            return

        name = os.path.basename(self.audio_path).split('.')[0] if self.audio_path else "spectrogram"
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Export Spectrogram", f"{name}.png", "PNG Files (*.png)")
        if not file_path:
            return

        qimg = self.image_item.getPixmap().toImage()
        if qimg is None:
            return

        # Flip the image vertically to match the expected orientation
        qimg_flipped = qimg.mirrored(False, True)
        qimg_flipped.save(file_path)

    def _show_details_dialog(self):
        if not self.audio_path or not os.path.isfile(self.audio_path):
            return

        # Attempt to read metadata using Mutagen
        try:
            mf = MutagenFile(self.audio_path, easy=True)
            mf_raw = MutagenFile(self.audio_path)
        except Exception:
            mf = None
            mf_raw = None

        # Prepare details to display
        details = []
        ext = os.path.splitext(self.audio_path)[1][1:].upper()
        details.append(("File name", os.path.basename(self.audio_path)))
        details.append(("Format", ext))

        duration = getattr(mf_raw.info, 'length', None) or self.metadata.get('duration', None)
        if duration:
            m, s = divmod(int(duration), 60)
            details.append(("Duration", f"{m}:{s:02d}"))

        sr = getattr(mf_raw.info, 'sample_rate', None) or self.metadata.get('sample_rate', None)
        if sr:
            details.append(("Sample rate", f"{sr} Hz"))

        br = getattr(mf_raw.info, 'bitrate', None)
        if br:
            details.append(("Bitrate", f"{br//1000} kbps"))

        ch = getattr(mf_raw.info, 'channels', None)
        if ch:
            details.append(("Channels", str(ch)))

        codec = getattr(mf_raw.info, 'codec', None)
        if codec:
            details.append(("Codec", str(codec)))

        bits = getattr(mf_raw.info, 'bits_per_sample', None)
        if bits:
            details.append(("Bits/sample", str(bits)))

        try:
            size = os.path.getsize(self.audio_path)
            details.append(("File size", humanize.naturalsize(size)))
        except Exception:
            pass

        if mf and hasattr(mf, 'tags') and mf.tags:
            for tag in ("title", "artist", "album", "date", "tracknumber", "genre", "composer", "albumartist", "comment"):
                val = mf.tags.get(tag)
                if val:
                    details.append((tag.capitalize(), ", ".join(val) if isinstance(val, list) else str(val)))

        # Create and show the details dialog
        dlg = QDialog(self.parent)
        dlg.setWindowTitle("File Details")

        # Create a layout and table to display the details
        layout = QVBoxLayout()
        table = QTableWidget(len(details), 2)
        table.setHorizontalHeaderLabels(["Parameter", "Value"])

        for i, (k, v) in enumerate(details):
            table.setItem(i, 0, QTableWidgetItem(str(k)))
            table.setItem(i, 1, QTableWidgetItem(str(v)))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)

        # Add a close button
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)

        dlg.setLayout(layout)
        dlg.exec()
