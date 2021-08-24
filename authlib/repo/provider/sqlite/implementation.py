import os
import platform
from typing import List, Literal
from pathlib import Path
import logging

import sqlite3 as sql

from ..base_provider import StorageProvider

from .settings import SQLITE_SETTINGS
from . import DatabaseError

class SQLiteProvider(StorageProvider):

    def __init__(self, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        db = SQLITE_SETTINGS.DB
        # Make a proper DB file name, unless in-memory DB.
        # Ignores any supplied database file path and pegs to DB_PATH. Also handles :memory: database correctly.
        database = ':memory:'
        if (db is not None) and (db != ':memory:'):
            db = db.lower()
            database = db if db.endswith('.db') else f'{db}.db'
            database = os.path.join(SQLITE_SETTINGS.DB_PATH, Path(database).name)

        self.db = database
        self.db_name = Path(database).stem.replace(':', '')

        self.con = SQLiteProvider._create_database(db=self.db, db_name=self.db_name, allow_db_create=allow_db_create)

        SQLiteProvider._create_table(
            con=self.con,
            db_name=self.db_name,
            table_name='USERS',
            col_spec='id INTEGER PRIMARY KEY, username UNIQUE ON CONFLICT REPLACE, password, su INTEGER',
            if_table_exists=if_table_exists
        )

    # --------------------------------------------------------------------------
    # Private helpers

    @staticmethod
    def _create_database(db, db_name, allow_db_create=False):
        """Create database."""
        # mode=ro throws if it doesn't exist
        # mode=rwc creates db if it doesn't exist, if_table_exists=if_table_exists
        mode = "rwc" if allow_db_create else "rw"
        if platform.system() == 'Windows':
            db_ = db.replace('\\', '/')
            file_uri = f'file:/{db_}?mode={mode}'
        else:
            file_uri = f'file:{db}?mode={mode}'

        # Database existence check and raise exception if necessary
        try:
            con = sql.connect(file_uri, uri=True, check_same_thread=False)
        except sql.OperationalError as ex:
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'`_create_database({db}, {db_name}, allow_db_create={allow_db_create})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

        # Database exists or will have been created at this point

        # Make database return dicts instead of tuples.
        # From: https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        con.row_factory = dict_factory

        return con

    @staticmethod
    def _create_table(con, db_name, table_name, col_spec, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        """Create table"""
        try:
            # Table existence check
            con.execute(f"SELECT * FROM {table_name} LIMIT 1")
            if if_table_exists == 'ignore':
                return
            elif if_table_exists == 'recreate':
                SQLiteProvider._delete_table(con, db_name, table_name)
        except sql.OperationalError:
            # table doesn't exist - continue to create it
            pass

        try:
            logging.info(f">>> Creating table `{table_name}` in database `{db_name}` <<<")
            con.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} ({col_spec})"
            )
            con.commit()
        except Exception as ex:
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'`create_table({db_name}, {table_name}, {col_spec}, if_table_exists={if_table_exists})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    @staticmethod
    def _delete_table(con, db_name, table_name):
        """Delete table with all data."""
        try:
            logging.info(f">>> Deleting table `{table_name}` from database `{db_name}` <<<")
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.commit()
        except Exception as ex:
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'`delete_table({db_name}, {table_name})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    # --------------------------------------------------------------------------
    # StorageProvider interface implementation

    def close_database(self) -> None:
        """Shuts down the database."""
        try:
            logging.info(f">>> Closing database `{self.db_name}` <<<")
            # Closing will delete the connection. An in-memory DB will lose all data permanently.
            # See https://stackoverflow.com/questions/48732439/deleting-a-database-file-in-memory
            self.con.commit()
            self.con.close()
        except Exception as ex:
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'Database: `{self.db_name}`\n`close_database()`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    # UPDATE or CREATE
    # Note, username is UNIQUE ON CONFLICT REPLACE, so we use INSERT to get UPSERT behaviour
    def upsert(self, context: dict=None) -> None:
        """Updates or inserts a new user record with supplied data (cols + value dict)."""
        assert(context.get('data', None) is not None)

        data = context.get('data', None)

        cols = ', '.join(list(data.keys()))
        # need to quote string values for SQLite
        # (assumes numeric values correspond to numeric columns)
        values_ = []
        for _k, v in data.items():
            if isinstance(v, int) or isinstance(v, float):
                values_.append(str(v))
            else:
                values_.append(f'"{v}"')
        values = ', '.join([v for v in values_])

        query = f"INSERT INTO USERS({cols}) VALUES({values})"

        logging.info(f"Upsert: {query}")
        try:
            self.con.execute(query)
            self.con.commit()
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'Database: `{self.db_name}`\n`upsert({data})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    # READ
    def query(self, context: dict=None) -> List[dict]:
        """Executes a query on users table and returns rows as list of dicts."""
        assert(context.get('fields', None) is not None)

        fields = context.get('fields', None)
        conds = context.get('conds', None)
        modifier = context.get('modifier', None)

        assert(fields is not None)

        select = f"SELECT {fields} FROM USERS "
        where = f"WHERE {conds} " if conds else ""
        mod = f"{modifier} " if modifier else ""

        query = f'{select}{where}{mod}'.strip()

        logging.info(f"Query: {query}")
        try:
            cur = self.con.execute(query)
            results = cur.fetchall()
            return results
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'Database: `{self.db_name}`\n`query({fields}, {conds}, {modifier})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    # DELETE
    def delete(self, context: dict=None) -> None:
        """Deletes record from users table."""
        assert(context.get('conds', None) is not None)

        conds = context['conds']

        select = f"DELETE FROM USERS "
        where = f"WHERE {conds} " if conds else "" 

        query = f'{select}{where}'.strip()

        logging.info(f"Delete: {query}")
        try:
            self.con.execute(query)
            self.con.commit()
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"SQLite exception",
                "description": f'Database: `{self.db_name}`\n`delete({conds})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

