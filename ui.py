from PySide6.QtWidgets import (
    QCheckBox,
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
from results_dialog import ResultsDialog
from database import Database
import config
from scanner import ScannerWorker


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Unique Photo Transfer")
        self.resize(700, 350)

        self.worker = None
        self.thread = None

        self.create_ui()


    def create_ui(self):

        layout = QVBoxLayout()


        self.source = QLineEdit()
        self.source.setText(config.DEFAULT_SOURCE)
        self.destination = QLineEdit()
        self.destination.setText(config.DEFAULT_DESTINATION)
        self.destination2 = QLineEdit()
        self.destination2.setText("")
        self.copyDestination = QLineEdit()
        self.copyDestination.setText(config.DEFAULT_COPY_DESTINATION)


        btn_source = QPushButton("Choisir source")
        btn_dest = QPushButton("Choisir destination")
        btn_dest2 = QPushButton("Choisir destination")
        btn_copyDest = QPushButton("Choisir destination des fichiers copiés")


        btn_source.clicked.connect(self.choose_source)
        btn_dest.clicked.connect(self.choose_destination)
        btn_dest2.clicked.connect(self.choose_destination2)
        btn_copyDest.clicked.connect(self.choose_copy_destination)


        row_source = QHBoxLayout()
        row_source.addWidget(self.source)
        row_source.addWidget(btn_source)


        row_destination = QHBoxLayout()
        row_destination.addWidget(self.destination)
        row_destination.addWidget(btn_dest)
        row_destination2 = QHBoxLayout()
        row_destination2.addWidget(self.destination2)
        row_destination2.addWidget(btn_dest2)

        row_copyDestination = QHBoxLayout()
        row_copyDestination.addWidget(self.copyDestination)
        row_copyDestination.addWidget(btn_copyDest)

        self.cbx_keep_structure = QCheckBox("Conserver la structure des dossiers")

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

        self.btn_results = QPushButton("Voir les résultats")
        self.btn_results.clicked.connect(self.show_results)



        layout.addLayout(row_source)
        layout.addLayout(row_destination)
        layout.addLayout(row_destination2)
        layout.addLayout(row_copyDestination)
        layout.addWidget(self.cbx_keep_structure)

        layout.addWidget(self.start_button)

        layout.addWidget(self.progressIndexation)
        layout.addWidget(self.progressIndexationLabel)
        layout.addWidget(self.progress)
        layout.addWidget(self.progressCopy)
        layout.addWidget(self.progressCopyLabel)
        layout.addWidget(self.status)

        layout.addWidget(self.btn_results)

        self.setLayout(layout)



    def choose_source(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.source.setText(folder)



    def choose_destination(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.destination.setText(folder)
    def choose_destination2(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.destination2.setText(folder)

    def choose_copy_destination(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.copyDestination.setText(folder)


    def start(self):

        self.start_button.setEnabled(False)

        self.database = Database()

        self.thread = QThread()

        self.worker = ScannerWorker(
            self.source.text(),
            self.destination.text(),
            self.destination2.text(),
            self.copyDestination.text(),
            self.cbx_keep_structure.isChecked(),
            self.database.filename
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

        # self.worker.run() # si besoin de debugger
        self.thread.start()

    def update_indexation(self, count):
        self.progressIndexation.setValue(count)
        self.progressIndexationLabel.setText(f"Fichiers indexés : {count:,}")
    def update_copy(self, count):
        self.progressCopy.setValue(count)
        self.progressCopyLabel.setText(f"Fichiers copiés : {count:,}")


    def doneIndexation(self):
        if self.progressIndexation.value() != 0:
            self.progressIndexation.setRange(0, self.progressIndexation.value())
        else:
            self.progressIndexation.setRange(0, 100)
        self.progressIndexationLabel.hide()
        self.progressCopy.setRange(0, 0)

    def done(self):
        if self.progressCopy.value() != 0:
            self.progressCopy.setRange(0, self.progressCopy.value())
        else:
            self.progressCopy.setRange(0, 100)
        self.progressCopyLabel.hide()

        self.status.setText("Terminé")
        self.start_button.setEnabled(True)

        self.database.close()
        self.thread.quit()
        self.thread.wait()


    def show_results(self):
        self.database.open()
        dialog = ResultsDialog(
            self.database,
            None,
        )
        dialog.exec()