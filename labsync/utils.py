import logging
import appdirs
import os

logging.basicConfig(
    format='%(asctime)-10s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

user_data_dir = appdirs.user_data_dir('labsync')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)
