"""A module defining custom axis items for PyQtGraph plots."""

import pyqtgraph as pg


class TimeAxisItem(pg.AxisItem):
    """Custom axis item for displaying time in minutes and seconds format."""
    def tickStrings(self, values, scale, spacing):
        result = []
        for val in values:
            if val < 0:
                # Handle negative values
                abs_val = abs(val)
                minutes = int(abs_val // 60)
                seconds = int(abs_val % 60)
                result.append(f"-{minutes}:{seconds:02d}")
            else:
                minutes = int(val // 60)
                seconds = int(val % 60)
                result.append(f"{minutes}:{seconds:02d}")
        return result


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