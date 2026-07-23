import sys

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

from PySide6.QtCore import QThread, Qt, Signal
from progress_event import ProgressEvent
from results_dialog import ResultsDialog
from database import Database
import config
from scanner import ScannerWorker
from WorkerError import WorkerError


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
        self.destination.setText(config.DEFAULT_DESTINATION1)
        self.destination2 = QLineEdit()
        self.destination2.setText(config.DEFAULT_DESTINATION2)
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

        self.progressHeaders = [
            QLabel("Scan des répertoires de destination"),
            QLabel("Scan du répertoire d'origine"),
            QLabel("Copie des fichiers")
        ]

        row_progressIndexation = QHBoxLayout()
        self.progressIndexation = QProgressBar()
        self.progressIndexationLabel = QLabel()
        row_progressIndexation.addWidget(self.progressHeaders[0])
        row_progressIndexation.addWidget(self.progressIndexation)
        row_progressIndexation.addWidget(self.progressIndexationLabel)
        self.destinationProgressCounters = list()

        row_progress = QHBoxLayout()
        self.progress = QProgressBar()
        row_progress.addWidget(self.progressHeaders[1])
        row_progress.addWidget(self.progress)

        row_progressCopy = QHBoxLayout()
        self.progressCopy = QProgressBar()
        self.progressCopyLabel = QLabel()
        row_progressCopy.addWidget(self.progressHeaders[2])
        row_progressCopy.addWidget(self.progressCopy)
        row_progressCopy.addWidget(self.progressCopyLabel)

        headerWidth = max(progressHeader.sizeHint().width() for progressHeader in self.progressHeaders)
        for progressHeader in self.progressHeaders:
            progressHeader.setFixedWidth(headerWidth)

        self.status = QLabel("Prêt")
        self.status.setAlignment(Qt.AlignCenter)

        self.btn_results = QPushButton("Voir les résultats")
        self.btn_results.clicked.connect(self.show_results)
        self.btn_results.setEnabled(False)




        layout.addLayout(row_source)
        layout.addLayout(row_destination)
        layout.addLayout(row_destination2)
        layout.addLayout(row_copyDestination)
        layout.addWidget(self.cbx_keep_structure)

        layout.addWidget(self.start_button)

        layout.addLayout(row_progressIndexation)
        layout.addLayout(row_progress)
        layout.addLayout(row_progressCopy)

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

        self.database.add_settings(
            [
                ("source", self.source.text()),
                ("destination", self.destination.text()),
                ("destination2", self.destination2.text()),
                ("copy_destination", self.copyDestination.text()),
                ("keep_structure", str(self.cbx_keep_structure.isChecked())),
                ("EXCLUDED_DIRECTORIES", str(config.EXCLUDED_DIRECTORIES))
            ]
        )

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
        self.progressIndexation.setFormat("")
        self.worker.filesDestScanned.connect(
            self.update_indexation
        )
        self.worker.finishedIndexation.connect(
            self.doneIndexation
        )


        self.progress.setFormat("%v / %m")
        self.worker.filesSourceScanned.connect(
            self.progress.setValue
        )
        self.worker.filesSourceTotal.connect(
            self.progress.setMaximum
        )

        self.progressCopy.setFormat("")
        self.worker.filesCopied.connect(
            self.update_copy
        )

        self.worker.message.connect(
            self.status.setText
        )
        self.worker.error.connect(
            self.on_error
        )

        self.worker.finished.connect(
            self.done
        )

        if is_debug():
            self.worker.run()
        else:
            self.thread.start()

    def update_indexation(self, event: ProgressEvent):

        found = False
        progressIndexationTotal = 0
        for progressEvent in self.destinationProgressCounters:
            if (progressEvent.root_folder == event.root_folder and progressEvent.phase == event.phase):
                progressEvent.current = event.current
                found = True
            progressIndexationTotal += progressEvent.current
        self.progressIndexation.setValue(progressIndexationTotal)
        if not found:
            self.destinationProgressCounters.append(event)

        self.progressIndexationLabel.setText("")
        for i, progressEvent in enumerate(self.destinationProgressCounters):
            if i > 0:
                self.progressIndexationLabel.setText(f"{self.progressIndexationLabel.text()}<br>")
            self.progressIndexationLabel.setText(f"{self.progressIndexationLabel.text()}{progressEvent.root_folder} - {progressEvent.current:,}")
        self.progressIndexationLabel.parentWidget().layout().activate()
        #self.progressIndexationLabel.adjustSize()
            
    def update_copy(self, count):
        self.progressCopy.setValue(count)
        self.progressCopyLabel.setText(f"{count:,}")


    def doneIndexation(self):
        if self.progressIndexation.value() != 0:
            self.progressIndexation.setRange(0, self.progressIndexation.value())
        else:
            self.progressIndexation.setRange(0, 100)
        self.progressCopy.setRange(0, 0)

    def on_error(self, workerError: WorkerError):
        self.status.setText(str(workerError.exception))
        print(workerError.traceback)

    def done(self):
        if self.progressCopy.value() != 0:
            self.progressCopy.setRange(0, self.progressCopy.value())
        else:
            self.progressCopy.setRange(0, 100)

        self.status.setText("Terminé")
        self.btn_results.setEnabled(True)

        self.database.close()
        self.thread.quit()
        self.thread.wait()


    def show_results(self):
        self.database.open()
        dialog = ResultsDialog(self.database, [])
        dialog.exec()



def is_debug():
    return sys.gettrace() is not None