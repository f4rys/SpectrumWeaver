cd assets
pyside6-rcc resources.qrc | sed '0,/PySide6/s//PyQt6/' > resources.py