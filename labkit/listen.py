import sys
import logging
import argparse
import os
import json
import labkit.utils
from labkit.watchfs import WatchFS
from labkit.tensorboard import Tensorboard
from labkit.dashboard import Dashboard

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--config', type=str, default='config.json', help='Path of the configuration JSON file')
    return parser

def listen():
    args = get_parser().parse_args(sys.argv[2:])

    if not os.path.exists(args.config):
        raise ValueError('Configuration file {} does not exist'.format(args.config))
    with open(args.config) as file:
        config = json.load(file)
    logger.info('Config: {}'.format(config))

    tasks = []

    if 'watchfs' in config:
        watchfs = WatchFS(config['watchfs'])
        watchfs.start()
        tasks.append(watchfs)
        logger.info('Started WatchFS task')

    if 'tensorboard' in config:
        tensorboard = Tensorboard(config['tensorboard'])
        tensorboard.start()
        tasks.append(tensorboard)
        logger.info('Started Tensorboard task')
    else:
        tensorboard = None

    if 'dashboard' in config:
        dashboard = Dashboard(config['dashboard'], tensorboard=tensorboard)    
        dashboard.start()
        tasks.append(dashboard)
        logger.info('Started Dashboard task')

    for task in tasks:
        task.join()
