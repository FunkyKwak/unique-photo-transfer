import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui import MainWindow


def resource_path(relative_path):
    current_path = Path(__file__).parent
    if hasattr(sys, "_MEIPASS"):
        current_path = Path(sys._MEIPASS)

    return str(current_path / relative_path)


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/unique-photo-transfer.ico"))
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()