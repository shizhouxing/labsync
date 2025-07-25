"""Listen for chnages."""
import sys
import logging
import argparse
import os
from .utils import get_config
from .watchfs import WatchFS

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    return parser

def listen():
    args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])

    config = get_config()
    logger.info('Config: %s', config)

    if 'local_path' in config:
        working_dir = os.path.expanduser(config['local_path'])
        os.chdir(working_dir)
        logger.info('Local working directory: %s', working_dir)

    task_watchfs = WatchFS(config)
    task_watchfs.start()
    logger.info('Start listening for local file changes')


    while True:
        line = input().split()
        if line[0] == 'pause':
            task_watchfs.pause()
        elif line[0] == 'resume':
            task_watchfs.resume()
        else:
            print('Unknown input')
