import sqlite3
from enum import IntEnum
from pathlib import Path
import time


class ResultStatus(IntEnum):
    COPIED = 1
    ALREADY_EXISTS = 2
    ERROR = 3



class Database:

    def __init__(self, filename=f"session{time.time()}.db"):
        self.filename = Path(filename)
        self.connection = sqlite3.connect(self.filename)
        self.create_tables()


    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status INTEGER NOT NULL,
                filename TEXT NOT NULL,
                source_path TEXT NOT NULL,
                destination_path TEXT,
                size INTEGER,
                modified_time INTEGER
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON results(status)
        """)
        self.connection.commit()



    def clear(self):
        self.connection.execute(
            "DELETE FROM results"
        )
        self.connection.commit()



    def add_result(
        self,
        status,
        source_path,
        destination_path=None,
        size=None,
        modified_time=None
    ):

        self.connection.execute(
            """
            INSERT INTO results
            (
                status,
                filename,
                source_path,
                destination_path,
                size,
                modified_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(status),
                Path(source_path).name,
                str(source_path),
                str(destination_path)
                if destination_path else None,
                size,
                modified_time
            )
        )



    def add_results(self, results):

        """
        results = liste de tuples :

        (
            status,
            filename,
            source,
            destination,
            size,
            mtime
        )
        """

        self.connection.executemany(
            """
            INSERT INTO results
            (
                status,
                filename,
                source_path,
                destination_path,
                size,
                modified_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            results
        )
        self.connection.commit()



    def commit(self):
        self.connection.commit()



    def count_results(self, status=None):
        cursor = self.connection.cursor()
        if status:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM results
                WHERE status = ?
                """,
                (int(status),)
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM results
                """
            )
        return cursor.fetchone()[0]



    def get_results(self, status=None):
        cursor = self.connection.cursor()
        if status:
            cursor.execute(
                """
                SELECT
                    filename,
                    status,
                    source_path,
                    destination_path

                FROM results

                WHERE status = ?

                ORDER BY filename
                """,
                (int(status),)
            )
        else:
            cursor.execute(
                """
                SELECT
                    filename,
                    status,
                    source_path,
                    destination_path

                FROM results

                ORDER BY filename
                """
            )
        return cursor.fetchall()



    def close(self):
        self.connection.close()