import sys
import logging
import argparse
import os
import json
from .utils import get_config
from .watchfs import WatchFS
from .tensorboard import Tensorboard

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--tensorboard', '-t', action='store_true', help='Start tensorboard server')
    return parser

def listen():
    args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])

    config = get_config()
    logger.info('Config: {}'.format(config))

    if 'local_path' in config:
        working_dir = os.path.expanduser(config['local_path'])
        os.chdir(working_dir)
        logger.info(f'Local working directory: {working_dir}')

    task_watchfs = WatchFS(config)
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
