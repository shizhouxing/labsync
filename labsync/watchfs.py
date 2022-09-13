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
    parser.add_argument('--path', '-p', type=str, default=None,
                        help='Path of the working directory on remote servers')
    return parser

class WatchFS(Thread):
    def __init__(self, config):
        super().__init__()

        args, _ = get_parser().parse_known_args(
            sys.argv[min(len(sys.argv), 1):])

        path = '.'
        self.servers = []
        for server, conf in config['servers'].items():
            if conf.get('enable', True):
                path_remote = (conf.get('remote_path')
                    or config.get('remote_path'))
                if args.path:
                    path_remote = os.path.join(path_remote, args.path)
                self.servers.append(Server(server, path_remote))

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
        time.sleep(5)
        try:
            while True:
                time.sleep(10)
                self._check_tasks()
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def _check_tasks(self):
        for server in self.servers:
            server.lock.acquire()
        count_tasks = 0
        for server in self.servers:
            count_tasks += len(server.tasks)
        if count_tasks == 0:
            os.system('clear')
            logger.info('Up-to-date')
        for server in self.servers:
            server.lock.release()

    def pause(self):
        self.event_handler.pause()
        logger.info('WatchFS paused')

    def resume(self):
        self.event_handler.resume()
        logger.info('WatchFS resumed')
