from os import environ as osenv
from collections import namedtuple

AIRTABLE_SETTINGS = namedtuple('air_settings', ['API_PAT', 'BASE_ID', 'USERS_TABLE'])

AIRTABLE_SETTINGS.API_PAT = osenv.get('AIRTABLE_PAT')
AIRTABLE_SETTINGS.BASE_ID = osenv.get('AIRTABLE_BASE_KEY')
AIRTABLE_SETTINGS.USERS_TABLE = osenv.get('USERS_TABLE')

ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')
