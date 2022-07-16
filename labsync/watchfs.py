import os
import sys
import time
import logging
import argparse
from .sync import Synchronizer
from .fsevent import FSEventHandler
from .server import Server
from watchdog.observers import Observer
from threading import Thread

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--path', '-p', type=str, default=None, help='Path of the working directory on remote servers')
    return parser

class WatchFS(Thread):
    def __init__(self, config):
        super().__init__()

        args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])

        path = '.'
        self.servers = []
        for server, conf in config['servers'].items():
            if conf.get('enable', True):
                path_remote = conf.get('remote_path') or config.get('remote_path')
                if args.path:
                    path_remote = os.path.join(path_remote, args.path)
                self.servers.append(Server(server, conf, path_remote))

        synchronizer = Synchronizer(self.servers)
        self.event_handler = FSEventHandler(
            synchronizer, 
            patterns=config.get('patterns', None), 
            ignore_patterns=config.get('ignore_patterns', None),
            ignore_patterns_re=config.get('ignore_patterns_re', []),
        )
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path, recursive=True)

    def run(self):
        self.observer.start()
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def pause(self):
        self.event_handler.pause()
        logger.info('WatchFS paused')

    def resume(self):
        self.event_handler.resume()
        logger.info('WatchFS resumed')
