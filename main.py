import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import ctypes
import resources
from ui import MainWindow



def main():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FunkyKwak.UniquePhotoTransfer")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resources.resource_path("assets/unique-photo-transfer.ico")))
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()