from datetime import datetime
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLabel,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem
)

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex
)

from database import ResultStatus



# ==========================================================
# Modèle du tableau principal
# ==========================================================

class ResultsModel(QAbstractTableModel):


    headers = [
        "Nom",
        "Statut",
        "Source",
        "Destination",
        "Correspondances partielle"
    ]


    def __init__(self, data):
        super().__init__()
        self.data_list = data



    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)


    def data(self, index, role):

        if not index.isValid():
            return None

        row = self.data_list[index.row()]
        # Structure attendue :
        #
        # (
        #   id,
        #   filename,
        #   result_status,
        #   source,
        #   destination,
        #   partial_matches_count
        # )

        if role == Qt.DisplayRole:

            result_id, filename, result_status, source, destination, partial_matches = row

            if index.column() == 0:
                return filename

            if index.column() == 1:

                if result_status == ResultStatus.COPIED:
                    return "Copié"

                if result_status == ResultStatus.ALREADY_EXISTS:
                    return "Déjà présent"

                if result_status == ResultStatus.HASH_PENDING:
                    return "Hash en attente"

                if result_status == ResultStatus.PARTIAL_MATCH:
                    return "Correspondance partielle, à vérifier"

                return "Erreur"


            if index.column() == 2:
                return source

            if index.column() == 3:
                return destination
            
            if index.column() == 4:
                return partial_matches



    def headerData(self, section, orientation, role):
        if (orientation == Qt.Horizontal and role == Qt.DisplayRole):
            return self.headers[section]


    def get_result_id(self, row):
        return self.data_list[row][0]



# ==========================================================
# Widget des détails du fichier source
# ==========================================================
class SourceDetailsWidget(QTreeWidget):


    def __init__(self):
        super().__init__()
        self.setHeaderLabels(
            [
                "Fichier source",
                "Détails"
            ]
        )
        self.itemDoubleClicked.connect(self.open_path)


    def display_details(self, source_details):
        self.clear()

        id, filename, source_path, source_size, source_modified_time, source_creation_time = source_details
        
        root = QTreeWidgetItem(
            [
                source_path,
                ""
            ]
        )
        self.addTopLevelItem(root)
        root.setFirstColumnSpanned(True)

        root.addChild(QTreeWidgetItem([
            "Nom",
            filename
        ]))
        root.addChild(QTreeWidgetItem([
            "Taille",
            str(source_size)
        ]))
        root.addChild(QTreeWidgetItem([
            "Date modification",
            datetime.fromtimestamp(source_modified_time).strftime('%d/%m/%Y %H:%M:%S')
        ]))
        root.addChild(QTreeWidgetItem([
            "Date création",
            datetime.fromtimestamp(source_creation_time).strftime('%d/%m/%Y %H:%M:%S')
        ]))

        self.header().resizeSection(0, 200)
        self.resizeColumnToContents(1)
        self.expandAll()
        
    def open_path(self, item, column):
        path = item.text(0)
        if Path(path).exists():
            open_and_select_file(path)



# ==========================================================
# Widget des matchs partiels
# ==========================================================
class PartialMatchesWidget(QTreeWidget):


    def __init__(self):
        super().__init__()
        self.setHeaderLabels(
            [
                "Correspondance",
                "Détails"
            ]
        )
        self.itemDoubleClicked.connect(self.open_path)


    def display_matches(self, matches):
        self.clear()

        if not matches:
            root = QTreeWidgetItem(
                [
                    "Aucune correspondance",
                    ""
                ]
            )
            self.addTopLevelItem(root)
            root.setFirstColumnSpanned(True)
            return


        for match in matches:
            id, filename, destination_path, destination_size, destination_modified_time, destination_creation_time, match_filename, match_size, match_modified_time, match_creation_time = match
            
            root = QTreeWidgetItem(
                [
                    destination_path,
                    ""
                ]
            )
            self.addTopLevelItem(root)
            root.setFirstColumnSpanned(True)

            root.addChild(QTreeWidgetItem([
                "Nom",
                "✓" if match_filename else filename
            ]))
            root.addChild(QTreeWidgetItem([
                "Taille",
                "✓" if match_size else str(destination_size)
            ]))
            root.addChild(QTreeWidgetItem([
                "Date modification",
                "✓" if match_modified_time else datetime.fromtimestamp(destination_modified_time).strftime('%d/%m/%Y %H:%M:%S')
            ]))
            root.addChild(QTreeWidgetItem([
                "Date création",
                "✓" if destination_creation_time else datetime.fromtimestamp(destination_creation_time).strftime('%d/%m/%Y %H:%M:%S')
            ]))

        self.header().resizeSection(0, 200)
        self.resizeColumnToContents(1)
        self.expandAll()



    def open_path(self, item, column):
        path = item.text(0)
        if Path(path).exists():
            open_and_select_file(path)



class ResultsDialog(QDialog):


    def __init__(self, database, status=None):
        super().__init__()

        self.database = database
        self.status = status

        self.setWindowTitle("Résultats")
        self.resize(1300, 900)
        self.create_ui()



    def create_ui(self):
        layout = QVBoxLayout()

        # --------------------------------------------------
        # Informations générales
        # --------------------------------------------------
        self.info = QLabel()

        # --------------------------------------------------
        # Tableau principal
        # --------------------------------------------------
        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.open_path)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.selectionModelChanged = None

        # --------------------------------------------------
        # Panneau détails
        # --------------------------------------------------
        self.details_title = QLabel("Correspondances partielles")
        self.source_details = SourceDetailsWidget()
        self.partial_details = PartialMatchesWidget()


        # --------------------------------------------------
        # Splitter
        # --------------------------------------------------
        splitter = QSplitter(Qt.Vertical)

        table_container = QVBoxLayout()
        table_container.addWidget(self.table)

        details_container = QVBoxLayout()
        details_container.addWidget(self.details_title)
        details_table_container = QHBoxLayout()
        details_table_container.addWidget(self.source_details)
        details_table_container.addWidget(self.partial_details)
        details_container.addLayout(details_table_container)

        from PySide6.QtWidgets import QWidget
        table_widget = QWidget()
        table_widget.setLayout(table_container)

        details_widget = QWidget()
        details_widget.setLayout(details_container)

        splitter.addWidget(table_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([600,300])


        # --------------------------------------------------
        # Boutons
        # --------------------------------------------------
        buttons = QHBoxLayout()
        close = QPushButton("Fermer")
        close.clicked.connect(self.close)
        buttons.addStretch()
        buttons.addWidget(close)


        # --------------------------------------------------
        # Assemblage
        # --------------------------------------------------
        layout.addWidget(self.info)
        layout.addWidget(splitter)

        layout.addLayout(buttons)

        self.setLayout(layout)

        self.refresh()



    def refresh(self):
        rows = self.database.get_results(self.status)
        self.info.setText(f"{len(rows)} résultat(s)")
        self.model = ResultsModel(rows)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        #
        # IMPORTANT :
        # le selectionModel n'existe qu'après setModel()
        #
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)



    def selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()

        if not indexes:
            self.partial_details.display_matches([])
            return

        row = indexes[0].row()
        result_id = self.model.get_result_id(row)

        self.source_details.display_details(self.database.get_source_details(result_id))
        self.partial_details.display_matches(self.database.get_partial_matches(result_id))



    def open_path(self, index):
        row = index.row()
        column = index.column()

        data = self.model.data_list[row]

        path = None

        if column == 2:
            path = data[3] # source
        elif column == 3:
            path = data[4] # destination
        elif column == 4:
            path = data[5] # correspondances

        if path:
            open_and_select_file(path)




# ==========================================================
# Utilitaires
# ==========================================================

def open_and_select_file(path):
    if not path:
        return
    path = str(Path(path).resolve())
    subprocess.Popen(
        [
            "explorer.exe",
            "/select,",
            path
        ]
    )