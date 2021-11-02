import logging
import appdirs
import os
import json

logging.basicConfig(
    format='%(levelname)-6s %(asctime)-10s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

user_data_dir = appdirs.user_data_dir('labsync')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

def get_config():
    for path in [
            '.labsync.config.json'
            '.labsync-config.json', 
            '.labkit-config.json', 
            os.path.join(os.path.expanduser("~"), '.labsync.config.json'),
            os.path.join(os.path.expanduser("~"), '.labsync-config.json'),
            os.path.join(os.path.expanduser("~"), '.labkit-config.json')]:
        if os.path.exists(path):
            with open(path) as file:
                config = json.load(file)
            return config
    raise ValueError('Cannot find configuration file')

def get_server(server):
    config = get_config()
    if not server in config['servers']:
        raise ValueError('Unknown server {}'.format(server))
    return config['servers'][server]
