import os
from pathlib import Path
import time

from PySide6.QtCore import QObject, Signal

import config
from copier import copy_file
from database import Database, ResultStatus
from progress_event import ProgressEvent, ProgressPhase

import exiftool
import resources
from WorkerError import WorkerError



class ScannerWorker(QObject):

    filesDestScanned = Signal(ProgressEvent)
    finishedIndexation = Signal()

    filesSourceScanned = Signal(int)
    filesSourceTotal = Signal(int)
    filesCopied = Signal(int)

    error = Signal(Exception)
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
        try:
            self.do_work()
        except Exception as e:
            import traceback
            self.error.emit(
                WorkerError(
                    e,
                    traceback.format_exc()
                )
            )

    def do_work(self):

        self.database = Database(self.db_path)

        # ==========================================================
        # STEP 1 : destination folders indexation
        # ==========================================================
        self.message.emit("Indexation destination...")
        self.build_index([self.destination, self.destination2])
        self.finishedIndexation.emit()



        # ==========================================================
        # STEP 2 : Compare fiiles from the source folder
        # ==========================================================
        self.message.emit("Analyse source...")


        # Compte du nombre de fichiers source + mise à plat de l'arborescence
        files = []
        for root, _, filenames in os.walk(self.source):
            for filename in filenames:
                files.append(
                    os.path.join(root, filename)
                )
        self.filesSourceTotal.emit(len(files))

        self.nFilesCopied = 0
        nfilesSourceScanned = 0
        self.filesCopied.emit(self.nFilesCopied)
        for filepath in files:

            stat = os.stat(filepath)
            filename = os.path.basename(filepath)

            # Search for an exact match in the destination index
            destination_match_path = self.database.get_destination_index_exact(filename, stat.st_size, int(stat.st_mtime))


            # Exact match : mark as already exists, do not copy
            if destination_match_path:
                self.database.add_result(
                    result_status=ResultStatus.ALREADY_EXISTS,
                    source_path=filepath,
                    destination_path=destination_match_path,
                    source_size=stat.st_size,
                    source_modified_time=int(stat.st_mtime),
                    source_creation_time=int(stat.st_ctime)
                )

            else:
                result_id = self.database.add_result(
                    result_status=ResultStatus.PARTIAL_MATCH,
                    source_path=filepath,
                    destination_path=destination_match_path,
                    source_size=stat.st_size,
                    source_modified_time=int(stat.st_mtime),
                    source_creation_time=int(stat.st_ctime)
                )
                destination_partial_matches_with_name = self.database.get_destination_index_partials_with_name(result_id)


                if len(destination_partial_matches_with_name) == 0:
                    # If no partial matches found, copy the file to the copy destination
                    self.copy(filepath, filename, result_id)



            nfilesSourceScanned += 1
            self.filesSourceScanned.emit(nfilesSourceScanned)
            self.database.commit()  # Commit after each file to ensure data is saved

            #time.sleep(1) # Simulate a long-running operation


        # ==========================================================
        # STEP 3 : Compare EXIF info on partial matches
        # ==========================================================
        partial_source_files = self.database.get_results([ResultStatus.PARTIAL_MATCH])
        partial_dest_files = self.database.get_partial_matches()
        file_paths_to_search_exif = []
        file_paths_to_search_exif.extend([f[3] for f in partial_source_files])
        file_paths_to_search_exif.extend([f[3] for f in partial_dest_files])

        # Gather EXIF data
        BATCH_SIZE = 100
        with exiftool.ExifToolHelper(executable=resources.resource_path("tools/exiftool/exiftool.exe")) as et:
            source_metadata = []
            nb_files = len(partial_source_files)
            self.message.emit(f"Récupération des données EXIF de la source : {nb_files} fichiers")
            for i in range(0, nb_files, BATCH_SIZE):
                batch = partial_source_files[i:i + BATCH_SIZE]
                source_metadata.extend(et.get_metadata([f[3] for f in batch]))

                progress = min(i + len(batch), nb_files)
                self.message.emit(f"Récupération des données EXIF de la source : {progress} / {nb_files} fichiers")
    
            dest_metadata = []
            nb_files = len(partial_dest_files)
            self.message.emit(f"Récupération des données EXIF de la destination : {nb_files} fichiers")
            for i in range(0, nb_files, BATCH_SIZE):
                batch = partial_dest_files[i:i + BATCH_SIZE]
                dest_metadata.extend(et.get_metadata([f[3] for f in batch]))

                progress = min(i + len(batch), nb_files)
                self.message.emit(f"Récupération des données EXIF de la destination : {progress} / {nb_files} fichiers")


        self.message.emit(f"Insertion des données EXIF dans la base")
        # UPDATE results table with EXIF data
        source_updates = [
            (
                meta.get("EXIF:DateTimeOriginal"),
                source_part[0]
            )
            for source_part, meta in zip(partial_source_files, source_metadata)
        ]
        self.database.update_result_exifs(source_updates)
        
        # UPDATE partial_matches table with EXIF data
        self.database.update_partial_matches_exifs([
            (
                meta.get("EXIF:DateTimeOriginal"),
                meta.get("EXIF:DateTimeOriginal") == next((s[0] for s in source_updates if s[1] == dest_part[1])),
                dest_part[0]
            )
            for dest_part, meta in zip(partial_dest_files, dest_metadata)
        ])

        # Comparison
        self.message.emit(f"Comparaison des correspondances partielles avec les doonnées EXIF")
        source_files = self.database.get_results([ResultStatus.PARTIAL_MATCH])
        dest_files = self.database.get_partial_matches()
        for source in source_files:
            self.message.emit(f"Comparaison des correspondances partielles avec les doonnées EXIF : {source[1]}")
            result_id = source[0]
            same_exif_date_found = False
            for dest in (d for d in dest_files if d[1] == result_id):
                source_exif_date = source[9]
                destination_exif_date = dest[7]

                if not destination_exif_date or not source_exif_date:
                    pass
                elif source_exif_date == destination_exif_date:
                    same_exif_date_found = True

                    source_size = source[6]
                    destination_size = dest[4]
                    if source_size < 0.7 * destination_size:
                        self.database.update_result(result_id, ResultStatus.COMPRESSED_SOURCE)

            # If no corresponding exif found : new file = copy 
            if not same_exif_date_found:
                self.copy(filepath, filename, result_id)

        self.database.close()
        self.finished.emit()


    def copy(self, filepath, filename, result_id):
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
        self.nFilesCopied += 1
        self.database.update_result(
            result_id=result_id,
            result_status=ResultStatus.COPIED,
            destination_path=target
        )
        self.filesCopied.emit(self.nFilesCopied)


    def build_index(self, folders):

        self.index = set()

        for folder in folders:
            self.currRootFolder = folder
            self.nfilesDestIndexed = 0
            if self.currRootFolder != "":
                self.scan(self.currRootFolder)

        return self.index
    

    def scan(self, folder):
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_dir():
                    if entry.name not in config.EXCLUDED_DIRECTORIES:
                        self.scan(entry.path)

                elif entry.is_file():
                    self.handle_file(entry)
    

    def handle_file(self, entry):
        stat = entry.stat()
        self.database.add_destination_index(
            filename=entry.name,
            destination_path=entry.path,
            destination_size=stat.st_size,
            destination_modified_time=int(stat.st_mtime),
            destination_creation_time=int(stat.st_ctime)
        )
        self.nfilesDestIndexed += 1
        self.filesDestScanned.emit(
            ProgressEvent(
                phase=ProgressPhase.INDEX,
                root_folder=self.currRootFolder,
                current=self.nfilesDestIndexed
            )
        )

        #time.sleep(1) # Simulate a long-running operation