from os import environ as osenv
from collections import namedtuple

AIRTABLE_SETTINGS = namedtuple('air_settings', ['API_PAT', 'BASE_ID', 'USERS_TABLE', 'PENDING_USERS_TABLE'])(
    API_PAT=osenv.get('AIRTABLE_PAT'),
    BASE_ID=osenv.get('AIRTABLE_BASE_KEY'),
    USERS_TABLE=osenv.get('USERS_TABLE', 'USERS').upper(),
    PENDING_USERS_TABLE=osenv.get('PENDING_USERS_TABLE', 'PENDING_USERS').upper()
)

ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')
