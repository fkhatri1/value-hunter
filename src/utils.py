import configparser
from typing import Dict
from datetime import datetime as dt

def get_config(path: str = '../config.ini') -> Dict:
    config = configparser.ConfigParser()
    config.read(path)
    return config._sections


def get_credentials(path: str = '../.credentials') -> Dict:
    config = configparser.ConfigParser()
    config.read(path)
    return config._sections['credentials']
