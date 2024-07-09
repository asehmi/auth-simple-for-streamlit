import json
from typing import List, Literal
import logging

# https://pyairtable.readthedocs.io/en/stable/getting-started.html
# https://support.airtable.com/docs/formula-field-reference
from pyairtable import Api
# from pyairtable.formulas import match
from pyairtable.orm import Model, fields

from ..base_provider import StorageProvider

from .settings import AIRTABLE_SETTINGS
from . import DatabaseError

# ------------------------------------------------------------------------------
# USER

class User(Model):
    username = fields.TextField('username')
    password = fields.TextField('password')
    su = fields.IntegerField("su")

    def __repr__(self):
        return { 
            "username": self.username, 
            "password": self.password,
            "su": str(self.su)
        }

    def __str__(self):
        return json.dumps(self.__repr__())

    def to_dict(self):
        return self.__repr__()
    def to_json(self):
        return json.dumps(self.__str__())

    @classmethod
    def create(cls, username: str = None, password: str = None, su: int = None):
        assert(username is not None)
        assert(password is not None)
        assert(su is not None)
        
        try:
            user = cls(
                username = username,
                password = password,
                su = su,
            )
            user.save()
        except Exception as ex:
            raise DatabaseError({
                "code": "Unplanned database rollback",
                "description": "Adding user record",
                "message": str(ex),
            }, 500)

        return user

    @classmethod
    def batch_create(cls, user_dicts: list[dict[str, any]]):
        try:
            users = []
            for user_dict in user_dicts:
                user = User(**user_dict)
                users.append(user)
            User.batch_save(users)
        except Exception as ex:
            raise DatabaseError({
                "code": "Unplanned database rollback",
                "description": "Adding user records",
                "message": str(ex),
            }, 500)

        return users

    class Meta:
        base_id = AIRTABLE_SETTINGS.BASE_ID
        table_name = AIRTABLE_SETTINGS.USERS_TABLE
        api_key = AIRTABLE_SETTINGS.API_PAT
        timeout = (5, 5)
        typecast = True

# ------------------------------------------------------------------------------

class AirtableProvider(StorageProvider):

    def __init__(self, allow_db_create=False, if_table_exists: Literal['ignore', 'recreate'] = 'ignore'):

        logging.info('>>> AirtbleProvider: ignoring `allow_db_create` and `if_table_exists` args. <<<')
        logging.info('>>> Please manage database and table directly in the Airtable service. <<<')

        air_api = Api(AIRTABLE_SETTINGS.API_PAT)
        air_users_table = air_api.table(AIRTABLE_SETTINGS.BASE_ID, AIRTABLE_SETTINGS.USERS_TABLE)

        self.db_name = AIRTABLE_SETTINGS.BASE_ID
        self.api = air_api
        self.users_table = air_users_table

    def close_database(self) -> None:
        """Shuts down the database."""
        self.api = None
        self.users_table = None

    def upsert(self, context: dict=None) -> None:
        """Updates or inserts a new user record with supplied data (cols + value dict)."""
        assert(context.get('data', None) is not None)
        
        data = context['data']

        assert(data.get('username', None) is not None)
        assert(data.get('password', None) is not None)
        assert(data.get('su', None) is not None)
        
        logging.info(f"Upsert: {data}")
        try:
            username = data['username']
            user_record = self.users_table.first(formula=f"username=\'{username}\'")
            user_id = user_record['id'] if user_record else None
            if user_id:
                self.users_table.update(user_id, fields=data, replace=True, typecast=True)
            else:
                self.users_table.create(fields=data, typecast=True)
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": "Airtable exception",
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
                user_records = self.users_table.all(formula=conds, sort=['username', 'su'], max_records=max_records)
            else:
                fields = fields.replace(' ', '').split(',')
                user_records = self.users_table.all(fields=fields, formula=conds, sort=['username', 'su'], max_records=max_records)
            results = [record['fields'] for record in user_records]
            return results
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": "Airtable exception",
                "description": f'Database: `{self.db_name}`\n`query({fields}, {conds}, {modifier})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)

    def delete(self, context: dict=None) -> None:
        """Deletes record from users table."""
        assert(context.get('conds', None) is not None)

        conds = context['conds']

        logging.info(f"Delete: {conds}")
        try:
            user_record = self.users_table.first(formula=conds)
            user_id = user_record['id'] if user_record else None
            if user_id:
                self.users_table.delete(user_id)
        except Exception as ex:
            self.close_database()
            raise DatabaseError({
                "code": "Airtable exception",
                "description": f'Database: `{self.db_name}`\n`delete({conds})`\nEnsure DB entities exist',
                "message": str(ex),
            }, 500)
