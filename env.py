import os
from os import environ as osenv
from dotenv import load_dotenv, find_dotenv
import logging

# ======== GLOBAL SETTINGS ========

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
osenv['BASE_DIR'] = BASE_DIR

# ======== LOAD SECRET ENVIRONMENT VARS (from .env) ========

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

def verify():
    logging.info(f'>>> Environment loading status <<<')
    logging.info(f'--  Application base directory: {BASE_DIR}')
    logging.info(f'--  Dotenv file: {ENV_FILE}\n\n')

