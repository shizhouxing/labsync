import logging
import appdirs
import os

logging.basicConfig(
    format='%(levelname)-8s %(asctime)-12s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

user_data_dir = appdirs.user_data_dir('labkit')
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)
