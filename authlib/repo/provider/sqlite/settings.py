import os
from os import environ as osenv
from collections import namedtuple

SQLITE_SETTINGS = namedtuple('sql_settings', ['DB_PATH', 'DB', 'PENDING_USERS_TABLE'])

base_dir = osenv.get('BASE_DIR', '.')
db_path = osenv.get('SQLITE_DB_PATH', 'db-temp')
SQLITE_SETTINGS.DB_PATH = os.path.join(base_dir, db_path)
SQLITE_SETTINGS.DB = osenv.get('SQLITE_DB', 'auth-temp.db')
SQLITE_SETTINGS.PENDING_USERS_TABLE = osenv.get('PENDING_USERS_TABLE', 'pending_users').upper()

ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')
