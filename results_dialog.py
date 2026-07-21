import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableView,
    QPushButton,
    QHBoxLayout,
    QLabel
)

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QUrl
)

from PySide6.QtGui import QDesktopServices

from database import ResultStatus, UserStatus



class ResultsModel(QAbstractTableModel):


    headers = [
        "Nom",
        "Résultat analyse",
        "Traitement utilisateur",
        "Source",
        "Destination"
    ]



    def __init__(self, data):
        super().__init__()
        self.data_list = data



    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)



    def columnCount(self, parent=QModelIndex()):
        return 5



    def data(self, index, role):

        if not index.isValid():
            return None


        row = self.data_list[index.row()]


        if role == Qt.DisplayRole:

            filename, result_status, user_status, source, destination = row


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

                if not user_status:
                    return ""
                
                if user_status == UserStatus.PENDING:
                    return "En attente"

                if user_status == UserStatus.CONFIRMED_DUPLICATE:
                    return "Déjà présent"

                if user_status == UserStatus.CONFIRMED_DIFFERENT:
                    return "Copié"

                return "Erreur"


            if index.column() == 3:
                return source


            if index.column() == 4:
                return destination



    def headerData(
        self,
        section,
        orientation,
        role
    ):

        if (
            orientation == Qt.Horizontal
            and role == Qt.DisplayRole
        ):
            return self.headers[section]



class ResultsDialog(QDialog):


    def __init__(
        self,
        database,
        status=None
    ):

        super().__init__()


        self.database = database
        self.status = status


        self.setWindowTitle(
            "Résultats"
        )

        self.resize(
            1000,
            600
        )


        self.create_ui()



    def create_ui(self):

        layout = QVBoxLayout()


        self.info = QLabel()


        self.table = QTableView()

        self.table.setSortingEnabled(True)

        self.table.doubleClicked.connect(
            self.open_path
        )


        self.refresh()



        buttons = QHBoxLayout()


        close = QPushButton(
            "Fermer"
        )

        close.clicked.connect(
            self.close
        )


        buttons.addStretch()

        buttons.addWidget(
            close
        )


        layout.addWidget(
            self.info
        )

        layout.addWidget(
            self.table
        )

        layout.addLayout(
            buttons
        )


        self.setLayout(
            layout
        )



    def refresh(self):

        rows = self.database.get_results(
            self.status
        )


        self.info.setText(
            f"{len(rows)} résultat(s)"
        )


        self.model = ResultsModel(
            rows
        )


        self.table.setModel(
            self.model
        )


        self.table.resizeColumnsToContents()



    def open_path(self, index):

        row = index.row()
        column = index.column()


        data = self.model.data_list[row]


        path = None


        if column == 2:
            path = data[2]


        elif column == 3:
            path = data[3]


        if path:
            open_and_select_file(path)



def open_and_select_file(path):

    path = str(Path(path).resolve())

    subprocess.Popen(
        [
            "explorer.exe",
            "/select,",
            path
        ]
    )