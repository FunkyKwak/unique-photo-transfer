import os
import time

from PySide6.QtCore import QObject, Signal

from copier import copy_file
from database import Database, ResultStatus



class ScannerWorker(QObject):

    filesDestScanned = Signal(int)
    finishedIndexation = Signal()

    filesSourceScanned = Signal(int)
    filesSourceTotal = Signal(int)
    filesCopied = Signal(int)

    message = Signal(str)
    finished = Signal()
    finishedIndexation = Signal()



    def __init__(self, source, destination, destination2, copy_destination, keep_structure, db_path):
        super().__init__()

        self.source = source
        self.destination = destination
        self.destination2 = destination2
        self.copy_destination = copy_destination
        self.keep_structure = keep_structure
        self.db_path = db_path



    def run(self):

        self.database = Database(self.db_path)

        self.message.emit("Indexation destination...")

        existing = self.build_index([self.destination, self.destination2])

        self.finishedIndexation.emit()



        self.message.emit("Analyse source...")


        files = []

        for root, _, filenames in os.walk(self.source):
            for filename in filenames:
                files.append(
                    os.path.join(root, filename)
                )


        self.filesSourceTotal.emit(len(files))

        nFilesCopied = 0
        nfilesSourceScanned = 0
        self.filesCopied.emit(nFilesCopied)
        for filepath in files:

            stat = os.stat(filepath)
            filename = os.path.basename(filepath)

            key = (
                filename,
                stat.st_size,
                int(stat.st_mtime)
            )

            if key not in existing:

                relative = os.path.relpath(
                    filepath,
                    self.source
                )

                if self.keep_structure:
                    target = os.path.join(
                        self.copy_destination,
                        relative
                    )
                else:
                    target = os.path.join(
                        self.copy_destination,
                        filename
                    )

                self.message.emit(
                    f"Copie : {relative}"
                )

                copy_file(
                    filepath,
                    target
                )
                nFilesCopied += 1
                self.database.add_result(
                    status=ResultStatus.COPIED,
                    source_path=filepath,
                    destination_path=target,
                    size=key[1],
                    modified_time=key[2]
                )
                self.filesCopied.emit(nFilesCopied)
            
            else:
                self.database.add_result(
                    status=ResultStatus.ALREADY_EXISTS,
                    source_path=filepath,
                    destination_path=None,  #TODO: stocker le chemin de destination dans le set "existing"
                    size=key[1],
                    modified_time=key[2]
                )

            nfilesSourceScanned += 1
            self.filesSourceScanned.emit(nfilesSourceScanned)
            self.database.commit()  # Commit after each file to ensure data is saved

            #time.sleep(1) # Simulate a long-running operation

        self.database.close()
        self.finished.emit()



    def build_index(self, folders):

        index = set()

        nfilesDestIndexed = 0

        for folder in folders:
            for root, _, filenames in os.walk(folder):

                for filename in filenames:

                    filepath = os.path.join(
                        root,
                        filename
                    )

                    stat = os.stat(filepath)

                    index.add(
                        (
                            filename,
                            stat.st_size,
                            int(stat.st_mtime)
                        )
                    )
                    nfilesDestIndexed += 1
                    self.filesDestScanned.emit(nfilesDestIndexed)

                    #time.sleep(1) # Simulate a long-running operation

        return index
        