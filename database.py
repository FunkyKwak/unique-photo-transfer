import sqlite3
from enum import IntEnum
from pathlib import Path
import datetime


class ResultStatus(IntEnum):
    ERROR = -1
    COPIED = 1
    ALREADY_EXISTS = 2
    HASH_PENDING = 3
    PARTIAL_MATCH = 4

class UserStatus(IntEnum):
    PENDING = 1
    CONFIRMED_DUPLICATE = 2
    CONFIRMED_DIFFERENT = 3


class Database:

    def __init__(self, filename=f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"):
        self.filename = Path(filename)
        self.connection = sqlite3.connect(self.filename)
        self.create_tables()


    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_size INTEGER,
                source_modified_time INTEGER,
                source_creation_time INTEGER,
                destination_path TEXT,
                result_status INTEGER NOT NULL,
                user_status INTEGER
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_result_status
            ON results(result_status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_status
            ON results(user_status)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS destination_index
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                destination_size INTEGER,
                destination_modified_time INTEGER,
                destination_creation_time INTEGER
            )
        """)
        self.connection.commit()



    def add_setting(self, key, value):
        self.connection.execute(
            """
            INSERT OR REPLACE INTO settings
            (
                key,
                value
            )
            VALUES (?, ?)
            """,
            (key, value)
        )
        self.connection.commit()

    def add_settings(self, settings):

        """
        settings = liste de tuples :

        (
            key,
            value
        )
        """

        self.connection.executemany(
            """
            INSERT OR REPLACE INTO settings
            (
                key,
                value
            )
            VALUES (?, ?)
            """,
            settings
        )
        self.connection.commit()


    def add_destination_index(
        self,
        filename,
        destination_path,
        destination_size,
        destination_modified_time,
        destination_creation_time
    ):

        self.connection.execute(
            """
            INSERT INTO destination_index
            (
                filename,
                destination_path,
                destination_size,
                destination_modified_time,
                destination_creation_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                filename,
                str(destination_path),
                destination_size,
                destination_modified_time,
                destination_creation_time
            )
        )

    def get_destination_index_exact(self, filename, size, modified_time):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                destination_path,
                destination_size,
                destination_modified_time,
                destination_creation_time
            FROM destination_index
            WHERE filename = ?
            AND destination_size = ?
            AND destination_modified_time = ?
            """,
            (filename, size, modified_time)
        )
        records = cursor.fetchall()
        if len(records) == 1:
            return records[0][1]  # Return the destination_path

        return None

    def add_result(
        self,
        source_path,
        source_size,
        source_modified_time,
        source_creation_time,
        result_status,
        user_status=None,
        destination_path=None,
    ):

        self.connection.execute(
            """
            INSERT INTO results
            (
                filename,
                source_path,
                source_size,
                source_modified_time,
                source_creation_time,
                result_status,
                user_status,
                destination_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                Path(source_path).name,
                str(source_path),
                source_size,
                source_modified_time,
                source_creation_time,
                int(result_status),
                int(user_status) if user_status else None,
                str(destination_path) if destination_path else None
            )
        )



    def add_results(self, results):

        """
        results = liste de tuples :

        (
            filename,
            source_path,
            source_size,
            source_modified_time,
            source_creation_time,
            result_status,
            user_status,
            destination_path
        )
        """

        self.connection.executemany(
            """
            INSERT INTO results
            (
                filename,
                source_path,
                source_size,
                source_modified_time,
                source_creation_time,
                result_status,
                user_status,
                destination_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            results
        )
        self.connection.commit()



    def commit(self):
        self.connection.commit()



    def get_results(self, result_status=None, user_status=None):
        cursor = self.connection.cursor()
        
        sql_where = ""
        if result_status and user_status:
            sql_where = "WHERE result_status = %(result_status)s AND user_status = %(user_status)s"
        elif result_status:
            sql_where = "WHERE result_status = %(result_status)s"
        elif user_status:
            sql_where = "WHERE user_status = %(user_status)s"
    
        cursor.execute(
            """
            SELECT
                filename,
                result_status,
                user_status,
                source_path,
                destination_path
            FROM results
            {sql_where}
            ORDER BY filename
            """
            .format(sql_where=sql_where),
            {
                "result_status": result_status,
                "user_status": user_status
            }
        )
        return cursor.fetchall()


    def open(self):
        self.connection = sqlite3.connect(self.filename)
    def close(self):
        self.connection.close()