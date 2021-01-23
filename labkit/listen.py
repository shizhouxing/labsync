import sys
import logging
import argparse
import os
import json
import labkit.utils
from labkit.utils import get_config
from labkit.watchfs import WatchFS
from labkit.tensorboard import Tensorboard

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--tensorboard', '-t', action='store_true', help='Start tensorboard server')
    return parser

def listen():
    args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])

    config = get_config()
    logger.info('Config: {}'.format(config))

    if not 'watchfs' in config:
        raise ValueError('Missing `watchfs` item in the configuration file')
    else:
        task_watchfs = WatchFS(config['watchfs'])
        task_watchfs.start()
        logger.info('Start listening for local file changes')

    if args.tensorboard:
        task_tensorboard = Tensorboard()
        task_tensorboard.start()

    while True:
        line = input().split()
        command = line[0].lower()
        if line[0] == 'pause':
            task_watchfs.pause()
        elif line[0] == 'resume':
            task_watchfs.resume()
        else:
            print('Unknown input')

    for task in tasks:
        task.join()
