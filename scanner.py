import os
import time

from PySide6.QtCore import QObject, Signal

from copier import copy_file



class ScannerWorker(QObject):

    filesDestScanned = Signal(int)
    finishedIndexation = Signal()

    filesSourceScanned = Signal(int)
    filesSourceTotal = Signal(int)
    filesCopied = Signal(int)

    message = Signal(str)
    finished = Signal()
    finishedIndexation = Signal()



    def __init__(self, source, destination, copy_destination, keep_structure):
        super().__init__()

        self.source = source
        self.destination = destination
        self.copy_destination = copy_destination
        self.keep_structure = keep_structure



    def run(self):

        self.message.emit("Indexation destination...")

        existing = self.build_index(
            self.destination
        )

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
                self.filesCopied.emit(nFilesCopied)

    
            nfilesSourceScanned += 1
            self.filesSourceScanned.emit(nfilesSourceScanned)
            
            time.sleep(1) # Simulate a long-running operation


        self.finished.emit()



    def build_index(self, folder):

        index = set()

        nfilesDestIndexed = 0

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

                time.sleep(1) # Simulate a long-running operation

        return index
        