import os
import sys
import time
import re
import logging
import argparse
from .server import Server
from watchdog.observers import Observer
from watchdog.events import (PatternMatchingEventHandler, DirCreatedEvent, FileCreatedEvent,
                             DirModifiedEvent, FileModifiedEvent)
from threading import Thread


logger = logging.getLogger(__name__)


class FSEventHandler(PatternMatchingEventHandler):
    def __init__(self, synchronizer, patterns=None, ignore_patterns=None,
                ignore_patterns_re=None):
        super().__init__(patterns=patterns, ignore_patterns=ignore_patterns)
        self.synchronizer = synchronizer
        self.paused = False
        if ignore_patterns_re is None:
            self.ignore_patterns_re = []
        else:
            self.ignore_patterns_re = [
                re.compile(pattern) for pattern in ignore_patterns_re]

    def dispatch(self, event):
        if self.paused:
            pass
        else:
            for pattern in self.ignore_patterns_re:
                if pattern.match(event.src_path):
                    return
            super().dispatch(event)

    def on_moved(self, event):
        self.synchronizer.mv(event.src_path, event.dest_path)

    def on_created(self, event):
        if isinstance(event, DirCreatedEvent):
            self.synchronizer.mkdir(event.src_path)
        elif isinstance(event, FileCreatedEvent):
            self.synchronizer.upload(event.src_path)
        else:
            raise TypeError

    def on_deleted(self, event):
        # Ignore the deletion event.
        pass

    def on_modified(self, event):
        if isinstance(event, DirModifiedEvent):
            # Handle specific files in the directory,
            # but not the directory itself
            pass
        elif isinstance(event, FileModifiedEvent):
            self.synchronizer.upload(event.src_path)
        else:
            raise TypeError

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False


class Synchronizer:
    def __init__(self, servers):
        self.servers = servers
        for server in self.servers:
            if not server.is_alive():
                server.start()

    def _add_task(self, task):
        for server in self.servers:
            server.add_task(task)

    def _parse_path(self, path):
        return os.path.relpath(path)

    def upload(self, path):
        self._add_task({
            'action': 'upload',
            'path': self._parse_path(path)
        })

    def mkdir(self, path):
        self._add_task({
            'action': 'mkdir',
            'path': self._parse_path(path)
        })

    def mv(self, src_path, dest_path):
        self._add_task({
            'action': 'mv',
            'src_path': self._parse_path(src_path),
            'dest_path': self._parse_path(dest_path)
        })


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
