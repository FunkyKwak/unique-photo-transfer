from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
)

from PySide6.QtCore import QThread, Signal

import config
from scanner import ScannerWorker


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Photo Sync")
        self.resize(600, 300)

        self.worker = None
        self.thread = None

        self.create_ui()


    def create_ui(self):

        layout = QVBoxLayout()


        self.source = QLineEdit()
        self.source.setText(config.DEFAULT_SOURCE)
        self.destination = QLineEdit()
        self.destination.setText(config.DEFAULT_DESTINATION)


        btn_source = QPushButton("Choisir source")
        btn_dest = QPushButton("Choisir destination")


        btn_source.clicked.connect(self.choose_source)
        btn_dest.clicked.connect(self.choose_destination)


        row1 = QHBoxLayout()
        row1.addWidget(self.source)
        row1.addWidget(btn_source)


        row2 = QHBoxLayout()
        row2.addWidget(self.destination)
        row2.addWidget(btn_dest)


        self.start_button = QPushButton("Démarrer")
        self.start_button.clicked.connect(self.start)


        self.progressIndexation = QProgressBar()
        self.progressIndexationLabel = QLabel()
        self.progressIndexationLabel.hide()

        self.progress = QProgressBar()

        self.progressCopy = QProgressBar()
        self.progressCopyLabel = QLabel()
        self.progressCopyLabel.hide()

        self.status = QLabel("Prêt")


        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progressIndexation)
        layout.addWidget(self.progressIndexationLabel)
        layout.addWidget(self.progress)
        layout.addWidget(self.progressCopy)
        layout.addWidget(self.progressCopyLabel)
        layout.addWidget(self.status)


        self.setLayout(layout)



    def choose_source(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.source.setText(folder)



    def choose_destination(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.destination.setText(folder)



    def start(self):

        self.start_button.setEnabled(False)

        self.thread = QThread()

        self.worker = ScannerWorker(
            self.source.text(),
            self.destination.text()
        )

        self.worker.moveToThread(self.thread)


        self.thread.started.connect(
            self.worker.run
        )

        self.progressIndexation.setRange(0, 0)
        self.progressIndexation.setFormat("Fichiers indexés dans le répertoire de destination : %v")
        self.progressIndexationLabel.show()
        self.worker.filesDestScanned.connect(
            self.update_indexation
        )
        self.worker.finishedIndexation.connect(
            self.doneIndexation
        )


        self.progress.setFormat("Fichiers scannés dans le répertoire d'origine : %v / %m")
        self.worker.filesSourceScanned.connect(
            self.progress.setValue
        )
        self.worker.filesSourceTotal.connect(
            self.progress.setMaximum
        )

        self.progressCopy.setFormat("Fichiers copiés : %v")
        self.progressCopyLabel.show()
        self.worker.filesCopied.connect(
            self.update_copy
        )

        self.worker.message.connect(
            self.status.setText
        )

        self.worker.finished.connect(
            self.done
        )

        self.thread.start()

    def update_indexation(self, count):
        self.progressIndexation.setValue(count+1)
        self.progressIndexationLabel.setText(f"Fichiers indexés : {count:,}")
    def update_copy(self, count):
        self.progressCopy.setValue(count)
        self.progressCopyLabel.setText(f"Fichiers copiés : {count:,}")


    def doneIndexation(self):
        self.progressIndexation.setRange(0, self.progressIndexation.value())
        self.progressIndexationLabel.hide()
        self.progressCopy.setRange(0, 0)

    def done(self):
        self.progressCopy.setRange(0, self.progressCopy.value())
        self.progressCopyLabel.hide()

        self.status.setText("Terminé")
        self.start_button.setEnabled(True)

        self.thread.quit()
        self.thread.wait()