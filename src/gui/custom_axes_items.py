"""A module defining custom axis items for PyQtGraph plots."""

import pyqtgraph as pg


class TimeAxisItem(pg.AxisItem):
    """Custom axis item for displaying time in minutes and seconds format."""
    def tickStrings(self, values, scale, spacing):
        return [f"{int(val // 60)}:{int(val % 60):02d}" for val in values]


class FreqAxisItem(pg.AxisItem):
    """Custom axis item for displaying frequency in kHz with unit."""
    def tickStrings(self, values, scale, spacing):
        out = []
        for val in values:
            if val >= 1000:
                out.append(f"{int(val/1000)} kHz")
            elif val > 0:
                out.append(f"{val/1000:.1f} kHz")
            else:
                out.append("0 kHz")
        return out