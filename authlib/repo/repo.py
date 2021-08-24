from os import environ as osenv
from dataclasses import dataclass
from datetime import datetime
import json

from .storage_factory import StorageFactory

STORAGE = osenv.get('STORAGE', 'SQLITE')

store = StorageFactory().get_provider(STORAGE, allow_db_create=False, if_table_exists='ignore')

from . import DatabaseError, tnow_iso , tnow_iso_str, dt_from_str, dt_from_ts, dt_to_str

def create_dummy_userinfo(username='test{}', key='', su=0):
    userinfo = { 'username': f'{username}'.format(key), 'password': 'pwd{}'.format(key),
                 'updated_at': dt_to_str(tnow_iso()), 'expires_at': dt_to_str(tnow_iso()), 'created_at': dt_to_str(tnow_iso()),
                 'active': 1, 'logins_count': 1, 'su': su }
    return userinfo

@dataclass
class User:
    username:       str = None
    password:       str = None
    updated_at:     datetime = tnow_iso()
    expires_at:     datetime = tnow_iso()
    created_at:     datetime = tnow_iso()
    active:         int = 0
    logins_count:   int = 0
    su:             int = 0

    def __repr__(self):
        return { "username": self.username,
                 "password": self.password,
                 "updated_at": dt_to_str(self.updated_at),
                 "expires_at": dt_to_str(self.expires_at), 
                 "created_at": dt_to_str(self.created_at), 
                 "active": self.active,
                 "logins_count": self.logins_count,
                 "su": self.su }

    def __str__(self):
        return json.dumps(self.__repr__())

    def dict(self):
        return self.__repr__()
    def json(self):
        return self.__str__()

    def update(self, userinfo=None):
        if userinfo:
            self.username = userinfo.get('username', self.username)
            self.password = userinfo.get('password', self.password)
            self.updated_at = dt_from_str(userinfo['updated_at']) if userinfo.get('updated_at', None) else tnow_iso()
            self.expires_at = dt_from_str(userinfo['expires_at']) if userinfo.get('expires_at', None) else tnow_iso()
            self.created_at = dt_from_str(userinfo['created_at']) if userinfo.get('created_at', None) else tnow_iso()
            self.active = userinfo.get('active', self.active)
            self.logins_count = userinfo.get('logins_count', self.logins_count)
            self.su = userinfo.get('su', self.su)

        return self

    @classmethod
    def create_from_userinfo(cls, userinfo):
        assert(userinfo is not None)

        user = cls(
            username = userinfo.get('username', None),
            password = userinfo.get('password', None),
            updated_at = dt_from_str(userinfo['updated_at']) if userinfo.get('updated_at', None) else tnow_iso(),
            expires_at = dt_from_str(userinfo['expires_at']) if userinfo.get('expires_at', None) else tnow_iso(),
            created_at = dt_from_str(userinfo['created_at']) if userinfo.get('created_at', None) else tnow_iso(),
            active = userinfo.get('active', 0),
            logins_count = userinfo.get('logins_count', 0),
            su = userinfo.get('su', 0),
        )
        return user

    @classmethod
    def create_from_db_record(cls, fields):
        assert(fields is not None)

        user = cls(
            username = fields['username'],
            password = fields.get('password', None),
            updated_at = dt_from_str(fields.get('updated_at', tnow_iso_str())),
            expires_at = dt_from_str(fields.get('expires_at', tnow_iso_str())),
            created_at = dt_from_str(fields.get('created_at', tnow_iso_str())),
            active = fields.get('active', 0),
            logins_count = fields.get('logins_count', 0),
            sum = fields.get('su', 0)
        )
        return user

    @staticmethod
    def create_or_update_user(userinfo):
        assert(userinfo is not None)

        user = None
        try:
            user_record = store.query(fields="*", conds=f"username='{userinfo['username']}'")
            if not user_record:
                user = User.create_from_userinfo(userinfo)
            else:
                user = User.create_from_db_record(user_record)
                user.update(userinfo=userinfo)
            store.query_database(
                "INSERT INTO USERS(username, password, updated_at, created_at, expires_at, active, logins_count, su) " +
                "VALUES(" +
                f"{user['username']}," + 
                f"{user['password']}," + 
                f"{user['updated_at']}," + 
                f"{user['created_at']}," + 
                f"{user['expires_at']}," + 
                f"{user['active']}," + 
                f"{user['logins_count']}," + 
                f"{user['su']}" + 
                ")",
            )
        except Exception as ex:
            raise DatabaseError({
                "code": "Unplanned database rollback",
                "description": f"Creating update record for {user_record}",
                "message": str(ex),
            }, 500)
        
        return user

    @staticmethod
    def get_user(username):
        assert(username is not None)

        try:
            userinfo = store.query(fields="*", conds=f"username = '{username}'")
        except Exception as ex:
            raise DatabaseError({
                "code": "Database exception",
                "description": f"Reading record for {username}",
                "message": str(ex),
            }, 500)
        return User.create_from_userinfo(userinfo)

    @staticmethod
    def del_user(username):
        assert(username is not None)

        try:
            store.delete(conds=f"username = '{username}'")
        except Exception as ex:
            raise DatabaseError({
                "code": "Database exception",
                "description": f"Deleting record for {username}",
                "message": str(ex),
            }, 500)
        return True
