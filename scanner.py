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



    def __init__(self, source, destination):
        super().__init__()

        self.source = source
        self.destination = destination



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
        for i, filepath in enumerate(files):

            stat = os.stat(filepath)

            key = (
                os.path.basename(filepath),
                stat.st_size,
                int(stat.st_mtime)
            )


            if key not in existing:

                relative = os.path.relpath(
                    filepath,
                    self.source
                )

                target = os.path.join(
                    self.destination,
                    relative
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


            self.filesSourceScanned.emit(i + 1)
            
            time.sleep(1) # Simulate a long-running operation


        self.finished.emit()



    def build_index(self, folder):

        index = set()


        for root, _, filenames in os.walk(folder):

            for i, filename in enumerate(filenames):

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
                self.filesDestScanned.emit(i)

                time.sleep(1) # Simulate a long-running operation

        return index
        