from typing import Literal
import streamlit as st
import sqlite3

from .provider.sqlite.settings import SQLITE_SETTINGS
def _sqlite_hash_func(allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
    path = SQLITE_SETTINGS.DB_PATH
    db = SQLITE_SETTINGS.DB
    hash_key = f'{path}|{db}|{allow_db_create}|{if_table_exists}'
    return hash_key

class StorageFactory():

    def __init__(self):
        pass

    @staticmethod
    @st.cache(hash_funcs={sqlite3.Connection: _sqlite_hash_func}) # @st.singleton << not yet released
    def _sqlite_provider(allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        print(f'_sqlite_provider(allow_db_create={allow_db_create}, if_table_exists={if_table_exists})')
        from .provider.sqlite.implementation import SQLiteProvider
        provider = SQLiteProvider(allow_db_create=allow_db_create, if_table_exists=if_table_exists)
        return provider

    @staticmethod
    @st.cache(allow_output_mutation=True) # @st.singleton << not yet released
    def _airtable_provider():
        print(f'_airtable_provider()')
        from .provider.airtable.implementation import AirtableProvider
        provider = AirtableProvider()
        return provider

    def get_provider(self, storage, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        assert(storage in ['SQLITE', 'AIRTABLE'])

        if storage == 'SQLITE':
            provider = StorageFactory._sqlite_provider(allow_db_create=allow_db_create, if_table_exists=if_table_exists)
        elif storage == 'AIRTABLE':
            provider = StorageFactory._airtable_provider()
        else:
            raise ValueError(storage)

        return provider
