import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/unique-photo-transfer.ico"))
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()