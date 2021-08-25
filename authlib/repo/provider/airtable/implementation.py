from typing import List, Literal
import logging

# https://pyairtable.readthedocs.io/en/latest/index.html
from pyairtable import Api, Base, Table

from ..base_provider import StorageProvider

from .settings import AIRTABLE_SETTINGS
from . import DatabaseError

class AirtableProvider(StorageProvider):

    def __init__(self, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):

        logging.info('>>> AirtbleProvider: ignoring `allow_db_create` and `if_table_exists` args. <<<')
        logging.info('>>> Please manage database and table directly in the Airtable service. <<<')

        self.db_name = AIRTABLE_SETTINGS.BASE_ID
        air_api = Api(api_key=AIRTABLE_SETTINGS.API_KEY)
        air_base = Base(api_key=AIRTABLE_SETTINGS.API_KEY, base_id=AIRTABLE_SETTINGS.BASE_ID)
        air_table = Table(api_key=AIRTABLE_SETTINGS.API_KEY, base_id=AIRTABLE_SETTINGS.BASE_ID, table_name=AIRTABLE_SETTINGS.USERS_TABLE)
        self.api = air_api
        self.base = air_base
        self.table = air_table

    def close_database(self) -> None:
        """Shuts down the database."""
        self.api = None
        self.base = None
        self.table = None

    def upsert(self, context: dict=None) -> None:
        """Updates or inserts a new user record with supplied data (cols + value dict)."""
        assert(context.get('data', None) is not None)

        data = context.get('data', None)

        logging.info(f"Upsert: {data}")
        try:
            user_record = self.table.first(formula=f"username='{data['username']}'")
            user_id = user_record['id'] if user_record else None
            if user_id:
                self.table.update(user_id, fields=data, replace=True, typecast=True)
            else:
                self.table.create(fields=data, typecast=True)
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"Airtable exception",
                "description": f'Database: `{self.db_name}`\n`upsert({data})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)


    def query(self, context: dict=None) -> List[dict]:
        """Executes a query on users table and returns rows as list of dicts."""
        assert(context.get('fields', None) is not None)

        fields = context.get('fields', None)
        conds = context.get('conds', None)
        modifier = context.get('modifier', None)

        logging.info(f"Query: {fields}, {conds}, {modifier}")
        try:
            max_records = 1000
            if modifier and modifier.startswith('LIMIT '):
                max_records = int(modifier.replace('LIMIT ', ''))
            if fields == '*':
                user_records = self.table.all(formula=conds, sort=['username', 'su'], max_records=max_records)
            else:
                fields = fields.replace(' ', '').split(',')
                user_records = self.table.all(fields=fields, formula=conds, sort=['username', 'su'], max_records=max_records)
            results = [record['fields'] for record in user_records]
            return results
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"Airtable exception",
                "description": f'Database: `{self.db_name}`\n`query({fields}, {conds}, {modifier})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    def delete(self, context: dict=None) -> None:
        """Deletes record from users table."""
        assert(context.get('conds', None) is not None)

        conds = context['conds']

        logging.info(f"Delete: {conds}")
        try:
            user_record = self.table.first(formula=conds)
            user_id = user_record['id'] if user_record else None
            if user_id:
                self.table.delete(user_id)
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": f"Airtable exception",
                "description": f'Database: `{self.db_name}`\n`delete({conds})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)
