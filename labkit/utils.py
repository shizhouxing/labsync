import logging
import appdirs
import os
import json

logging.basicConfig(
    format='%(levelname)-8s %(asctime)-12s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

user_data_dir = appdirs.user_data_dir('labkit')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

def get_config(path):
    if not os.path.exists(path):
        raise ValueError('Configuration file {} does not exist'.format(path))    
    with open(path) as file:
        config = json.load(file)
    return config
