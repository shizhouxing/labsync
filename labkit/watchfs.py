import sys
import time
import logging
import labkit.utils
from labkit.sync import Synchronizer
from labkit.fsevent import FSEventHandler
from labkit.server import Server
from watchdog.observers import Observer
from threading import Thread

logger = logging.getLogger(__name__)

class WatchFS(Thread):
    def __init__(self, config):
        super().__init__()

        path = '.'

        servers = []
        for server, conf in config['servers'].items():
            servers.append(Server(server, conf))

        synchronizer = Synchronizer(servers, path)
        event_handler = FSEventHandler(
            synchronizer, 
            patterns=config.get('patterns', None), 
            ignore_patterns=config.get('ignore_patterns', None)
        )
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)

    def run(self):
        self.observer.start()
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
