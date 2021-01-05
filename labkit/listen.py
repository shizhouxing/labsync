import sys
import logging
import argparse
import os
import json
import labkit.utils
from labkit.watchfs import WatchFS
from labkit.tensorboard import Tensorboard

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

    tasks = {}
    tasks_all = ['WatchFS', 'Tensorboard', 'TaskManager']

    for item in tasks_all:
        if item.lower() in config:
            task = eval(item)(config[item.lower()])
            task.start()
            tasks[item] = task
            logger.info('Started task: {}'.format(item))

    while True:
        line = input().split()
        command = line[0].lower()
        if line[0] == 'pause':
            if 'WatchFS' in tasks:
                tasks['WatchFS'].pause()
        elif line[0] == 'resume':
            if 'WatchFS' in tasks:
                tasks['WatchFS'].resume()
        else:
            print('Unknown input')

    for task in tasks:
        task.join()
