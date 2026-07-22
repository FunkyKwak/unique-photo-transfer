import sqlite3
from enum import IntEnum
from pathlib import Path
import datetime


class ResultStatus(IntEnum):
    ERROR = (-1, "Erreur")
    COPIED = (1, "Fichier copié")
    ALREADY_EXISTS = (2, "Déjà présent")
    HASH_PENDING = (3, "Hash en attente")
    PARTIAL_MATCH = (4, "Correspondance partielle, à vérifier")
    COMPRESSED_SOURCE = (5, "Fichier source identique mais compressé")

    def __new__(cls, value, description):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    @classmethod
    def description_from_value(cls, value: int):
        try:
            return cls(value).description
        except ValueError:
            return "Pas de ResultStatus correspondant"

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
                source_exif_DateTimeOriginal TEXT,
                destination_path TEXT,
                result_status INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_result_status
            ON results(result_status)
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partial_matches
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                destination_size INTEGER,
                destination_modified_time INTEGER,
                destination_creation_time INTEGER,
                destination_exif_DateTimeOriginal TEXT,
                match_score INTEGER NOT NULL,
                match_filename BOOLEAN NOT NULL CHECK (match_filename IN (0, 1)),
                match_size BOOLEAN NOT NULL CHECK (match_size IN (0, 1)),
                match_modified_time BOOLEAN NOT NULL CHECK (match_modified_time IN (0, 1)),
                match_creation_time BOOLEAN NOT NULL CHECK (match_creation_time IN (0, 1)),
                match_exif_DateTimeOriginal BOOLEAN CHECK (match_exif_DateTimeOriginal IN (0, 1)),
                FOREIGN KEY(result_id) REFERENCES results(id)  
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
            """,
            (filename, size)
        )
        records = cursor.fetchall()
        if len(records) == 1:
            return records[0][1]  # Return the destination_path
        else:
            for record in records:
                if same_time(
                    modified_time,
                    record[3]  # destination_modified_time
                ):
                    return record[1]  # Return the destination_path

        return None

    def get_destination_index_partials_with_name(self, result_id):
        cursor = self.connection.cursor()
        # Retourne les fichiers dans la destination, avec le même nom que le fichier source
        cursor.execute(
            """
            SELECT
                r.id as result_id,
                r.filename,
                d.destination_path,
                d.destination_size,
                d.destination_modified_time,
                d.destination_creation_time,
                case when r.filename = d.filename then 1 else 0 end as match_filename,
                case when r.source_size = d.destination_size then 1 else 0 end as match_size,
                case when r.source_modified_time = d.destination_modified_time then 1 else 0 end as match_modified_time,
                case when r.source_creation_time = d.destination_creation_time then 1 else 0 end as match_creation_time
            FROM results r
            INNER JOIN destination_index d ON r.filename = d.filename
            WHERE r.id = ?
            """,
            (result_id,)
        )

        partial_matches = cursor.fetchall()

        self.add_partial_matches(partial_matches)

        return partial_matches
    

    def add_partial_matches(
        self,
        partial_matches):
        
        """
        partial_matches = liste de tuples :
        
        (
            result_id,
            filename,
            destination_path,
            destination_size,
            destination_modified_time,
            destination_creation_time,
            match_filename,
            match_size,
            match_modified_time,
            match_creation_time,
        )
        """

        self.connection.executemany(
            """
            INSERT INTO partial_matches
            (
                result_id,
                filename,
                destination_path,
                destination_size,
                destination_modified_time,
                destination_creation_time,
                match_score,
                match_filename,
                match_size,
                match_modified_time,
                match_creation_time
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            partial_matches
        )
        self.connection.commit()


        # Update match_score after inserting all partial matches
        result_ids = [partial_match[0] for partial_match in partial_matches]
        result_ids = set(result_ids)  # Remove duplicates
        for result_id in result_ids:
            self.update_match_score(result_id)  

    def update_match_score(self, result_id):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE partial_matches
            SET match_score = (match_filename + match_size + match_modified_time + match_creation_time)
            WHERE result_id = ?
            """,
            (result_id,)
        )
        self.connection.commit()



    def add_result(
        self,
        source_path,
        source_size,
        source_modified_time,
        source_creation_time,
        result_status,
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
                destination_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                Path(source_path).name,
                str(source_path),
                source_size,
                source_modified_time,
                source_creation_time,
                int(result_status),
                str(destination_path) if destination_path else None
            )
        )
        return self.connection.execute("SELECT last_insert_rowid()").fetchone()[0]  # Return the last inserted row ID


    def update_result(
        self,
        result_id,
        result_status,
        destination_path=None,
    ):

        self.connection.execute(
            """
            UPDATE results
            SET result_status = ?,    
                destination_path = COALESCE(destination_path, ?)
            WHERE id = ?
            """,
            (result_status, destination_path,result_id)
        )
        self.connection.commit()

    def update_result_exifs(
        self,
        updates,
    ):
        query = """
            UPDATE results
            SET source_exif_DateTimeOriginal = ?
            WHERE id = ?
        """

        cursor = self.connection.cursor()
        cursor.executemany(
            query,
            updates
        )
        self.connection.commit()


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
                destination_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            results
        )
        self.connection.commit()



    def commit(self):
        self.connection.commit()



    def get_results(self, result_status=None):
        cursor = self.connection.cursor()
        
        sql_where = ""
        if result_status:
            sql_where = f"WHERE result_status = {result_status}"
    
        cursor.execute(
            f"""
            SELECT
                r.id,
                r.filename,
                r.result_status,
                r.source_path,
                r.destination_path,
                case 
                    WHEN (SELECT COUNT(*) FROM partial_matches p WHERE p.result_id = r.id) = 1 THEN (SELECT destination_path FROM partial_matches p WHERE p.result_id = r.id LIMIT 1)
                    ELSE (SELECT COUNT(*) FROM partial_matches p WHERE p.result_id = r.id)
                END as partial_matches,
                source_size,
                source_modified_time,
                source_creation_time,
                source_exif_DateTimeOriginal
            FROM results r
            {sql_where}
            ORDER BY filename
            """
        )
        return cursor.fetchall()
    
    def get_source_details(self, result_id):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                filename,
                source_path,
                source_size,
                source_modified_time,
                source_creation_time,
                source_exif_DateTimeOriginal
            FROM results
            WHERE id = ?
            ORDER BY id
            """,
            (result_id,)
        )
        return cursor.fetchone()
    
    def get_partial_matches(self, result_id=None):
        cursor = self.connection.cursor()
        sql_where = f"WHERE r.result_status = {ResultStatus.PARTIAL_MATCH}"
        if result_id:
            sql_where = f"WHERE r.id = {result_id}" 
        cursor.execute(
            f"""
            SELECT
                p.id,
                p.result_id,
                p.filename,
                p.destination_path,
                p.destination_size,
                p.destination_modified_time,
                p.destination_creation_time,
                p.destination_exif_DateTimeOriginal,
                p.match_filename,
                p.match_size,
                p.match_modified_time,
                p.match_creation_time,
                p.match_exif_DateTimeOriginal
            FROM partial_matches p
            INNER JOIN results r on p.result_id = r.id
            {sql_where} 
            ORDER BY p.id
            """
        )
        return cursor.fetchall()

    def update_partial_matches_exifs(
        self,
        updates,
    ):
        query = """
            UPDATE partial_matches
            SET destination_exif_DateTimeOriginal = ?,
                match_exif_DateTimeOriginal = ?
            WHERE id = ?
        """

        cursor = self.connection.cursor()
        cursor.executemany(
            query,
            updates
        )
        self.connection.commit()


    def open(self):
        self.connection = sqlite3.connect(self.filename)
    def close(self):
        self.connection.close()


        

def same_time(t1: int, t2: int) -> bool:
    delta = abs(t1 - t2)
    return (
        delta == 0
        or (
            delta <= 24 * 3600
            and delta % 3600 == 0
        )
    )