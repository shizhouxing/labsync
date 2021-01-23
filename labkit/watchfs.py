import sys
import time
import logging
import argparse
import labkit.utils
from labkit.sync import Synchronizer
from labkit.fsevent import FSEventHandler
from labkit.server import Server
from watchdog.observers import Observer
from threading import Thread

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--destination', '-d', type=str, default='~', help='Destination directory on the remote servers')
    return parser

class WatchFS(Thread):
    def __init__(self, config):
        super().__init__()

        args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])

        path = '.'
        destination = args.destination

        self.servers = []
        for server, conf in config['servers'].items():
            if conf.get('enable', True):
                self.servers.append(Server(server, conf, destination))

        synchronizer = Synchronizer(self.servers, path)
        self.event_handler = FSEventHandler(
            synchronizer, 
            patterns=config.get('patterns', None), 
            ignore_patterns=config.get('ignore_patterns', None)
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