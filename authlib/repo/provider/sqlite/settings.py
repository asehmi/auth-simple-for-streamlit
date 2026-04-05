import os
from os import environ as osenv
from collections import namedtuple

base_dir = osenv.get('BASE_DIR', '.')
db_path = osenv.get('SQLITE_DB_PATH', 'db-temp')

SQLITE_SETTINGS = namedtuple('sql_settings', ['DB_PATH', 'DB', 'USERS_TABLE', 'PENDING_USERS_TABLE'])(
    DB_PATH=os.path.join(base_dir, db_path),
    DB=osenv.get('SQLITE_DB', 'auth-temp.db'),
    USERS_TABLE=osenv.get('USERS_TABLE', 'USERS').upper(),
    PENDING_USERS_TABLE=osenv.get('PENDING_USERS_TABLE', 'PENDING_USERS').upper()
)

ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')
