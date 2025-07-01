"""A module containing CustomContextMenu class for spectrum viewer actions."""

import os
from typing import Optional

import humanize
import numpy as np
from pyqtgraph import colormap
from mutagen import File as MutagenFile
from PySide6.QtCore import Qt
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import (QMenu, QWidget, QFileDialog, QTableWidget, QLabel, 
                               QComboBox, QTableWidgetItem, QVBoxLayout, QCheckBox)

from .custom_title_bar import CustomTitleBar


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
        colorbar,
        audio_path: str,
        spectrogram_data: Optional[np.ndarray],
        metadata: dict
    ):
        self.parent = parent
        self.plot_widget = plot_widget
        self.image_item = image_item
        self.colorbar = colorbar
        self.audio_path = audio_path
        self.spectrogram_data = spectrogram_data
        self.metadata = metadata
        self._show_grid = True  # Default state, can be loaded from config if needed
        self._colormap = 'viridis'  # Default colormap

    def exec(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self.parent)
        export_action = menu.addAction("Export spectrogram to PNG")
        details_action = menu.addAction("Show details")
        settings_action = menu.addAction("Settings")
        action = menu.exec(event.globalPos())

        if action == export_action:
            self._export_spectrogram_png()
        elif action == details_action:
            self._show_details_dialog()
        elif action == settings_action:
            self._show_settings_dialog()

    def _export_spectrogram_png(self):
        """Export the spectrogram as a PNG file."""
        if self.spectrogram_data is None:
            return

        name = os.path.basename(self.audio_path).split('.')[0] if self.audio_path else "spectrogram"
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, "Export Spectrogram", f"{name}.png", "PNG Files (*.png)")

        if not file_path:
            return

        qimg = self.image_item.getPixmap().toImage()
        if qimg is None:
            return

        # Flip the image vertically to match the expected orientation
        qimg_flipped = qimg.mirrored(False, True)
        qimg_flipped.save(file_path)

    def _show_details_dialog(self):
        """Show a dialog with audio file details."""
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
            for tag in ("title", "artist", "album", "date", "tracknumber", 
                        "genre", "composer", "albumartist", "comment"):
                val = mf.tags.get(tag)
                if val:
                    details.append((tag.capitalize(), ", ".join(val) if isinstance(val, list) else str(val)))

        # Create and show the details dialog
        dlg = QWidget(self.parent, Qt.Window | Qt.FramelessWindowHint)

        # Hide the original dialog title bar for a custom look
        title_bar = CustomTitleBar(dlg, show_min_max=False)

        # Main layout, no margins so title bar is flush
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)

        # Content widget with margins for the table
        content_widget = QWidget(dlg)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(10)

        table = QTableWidget(len(details), 2)
        table.setHorizontalHeaderLabels(["Parameter", "Value"])

        # Populate the table with details
        for i, (k, v) in enumerate(details):
            table.setItem(i, 0, QTableWidgetItem(str(k)))
            table.setItem(i, 1, QTableWidgetItem(str(v)))

        # Make headers occupy full width and hide the top-left corner
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setCornerButtonEnabled(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_layout.addWidget(table)
        content_widget.setLayout(content_layout)

        layout.addWidget(content_widget)
        dlg.setLayout(layout)
        dlg.show()

    def on_grid_toggled(self, checked):
        """Toggle the visibility of the grid on the plot."""
        self._show_grid = checked

        # Prevent errors if plot_widget is not set yet
        if self.plot_widget is not None:
            self.plot_widget.showGrid(x=checked, y=checked)

    def on_colormap_changed(self, name):
        """Change the colormap of the image item and colorbar."""
        self._colormap = name
        cmap = colormap.get(name)

        # Only update colormap if image_item and colorbar are both set
        if self.image_item is not None and self.colorbar is not None:
            self.image_item.setColorMap(cmap)
            self.colorbar.setColorMap(cmap)

    def _show_settings_dialog(self):
        """Show a settings dialog with a custom title bar and colormap selection."""
        dlg = QWidget(self.parent, Qt.Window | Qt.FramelessWindowHint)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        title_bar = CustomTitleBar(dlg, show_min_max=False)
        layout.addWidget(title_bar)

        # Content widget with its own layout and margins
        content_widget = QWidget(dlg)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(10)

        # Grid visibility checkbox
        grid_checkbox = QCheckBox("Show grid on plot")
        grid_checkbox.setChecked(self._show_grid)
        grid_checkbox.toggled.connect(self.on_grid_toggled)

        # Predefined list of colormaps
        colormaps = ["viridis", "plasma", "inferno", "magma", "cividis"]

        # Label for colormap selection
        colormap_label = QLabel("Colormap:")

        # Combo box for colormap selection
        colormap_combo = QComboBox()
        colormap_combo.addItems(colormaps)
        colormap_combo.setCurrentText(self._colormap)
        colormap_combo.currentTextChanged.connect(self.on_colormap_changed)

        # Add widgets to content layout
        content_layout.addWidget(grid_checkbox)
        content_layout.addWidget(colormap_label)
        content_layout.addWidget(colormap_combo)
        content_widget.setLayout(content_layout)

        # Add content widget to main layout
        layout.addWidget(content_widget)

        dlg.setLayout(layout)
        dlg.show()
