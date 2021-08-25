from os import environ as osenv
from collections import namedtuple

AIRTABLE_SETTINGS = namedtuple('air_settings', ['API_KEY', 'BASE_ID', 'USERS_TABLE', 'ACTIVITY_TABLE'])

AIRTABLE_SETTINGS.API_KEY = osenv.get('AIRTABLE_API_KEY')
AIRTABLE_SETTINGS.BASE_ID = osenv.get('AIRTABLE_PROFILE_BASE_ID')
AIRTABLE_SETTINGS.USERS_TABLE = osenv.get('USERS_TABLE')
AIRTABLE_SETTINGS.ACTIVITY_TABLE = osenv.get('ACTIVITY_TABLE')

ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')
