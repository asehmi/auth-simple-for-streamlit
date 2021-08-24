from typing import Literal

class StorageFactory():

    def __init__(self):
        pass

    def get_provider(self, storage, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):
        assert(storage in ['SQLITE', 'AIRTABLE'])

        if storage == 'SQLITE':
            from .provider.sqlite.implementation import SQLiteProvider
            provider = SQLiteProvider(allow_db_create=allow_db_create, if_table_exists=if_table_exists)
        elif storage == 'AIRTABLE':
            from .provider.airtable.implementation import AirtableProvider
            provider = AirtableProvider()
        else:
            raise ValueError(storage)

        return provider
