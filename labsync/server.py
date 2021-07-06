import os
import time
import threading
import logging
import subprocess
from collections import deque
from threading import Thread, Lock

logger = logging.getLogger(__name__)

class Server(Thread):
    def __init__(self, name, config, destination, refresh_interval=0.05):
        super().__init__()
        self.name = name
        self.username = config['username']
        self.host = config['host']
        self.jump = config.get('jump', None)
        self.port = config.get('port', 22)
        self.dest_root = destination
        self.refresh_interval = refresh_interval
        self.tasks = deque()
        self.lock = Lock()

    def add_task(self, task):
        self.lock.acquire()
        existing = False
        for t in self.tasks:
            if t == task:
                existing = True
                break
        if not existing:
            self.tasks.append(task)
        logger.info('Server {}: {} task {}, {} tasks in queue'.format(
            self.name, 'existing' if existing else 'new', task, len(self.tasks)))
        self.lock.release()

    def run(self):
        while True:
            while len(self.tasks) > 0:
                self.lock.acquire()
                task = self.tasks.pop()
                self.lock.release()

                if task['action'] == 'upload':
                    self._upload(task['path'])
                elif task['action'] == 'mkdir':
                    self._mkdir(task['path'])
                elif task['action'] == 'mv':
                    self._mv(task['src_path'], task['dest_path'])
                else:
                    raise ValueError('Unknown action {}'.format(task['action']))

                logger.info('Server {}: {} task(s) left'.format(self.name, len(self.tasks)))

            time.sleep(self.refresh_interval)

    def _upload(self, path):
        args = []
        if self.jump: 
            args += ['-J', self.jump]
        if self.port:
            args += ['-P', str(self.port)]
        args.append(path)
        args.append('{}@{}:{}'.format(
            self.username, self.host, os.path.join(self.dest_root, path)))
        logger.info('Server {}: executing scp {}'.format(self.name, args))
        subprocess.run(['scp'] + args)

    def _mkdir(self, path):
        print('TODO mkdir', path)
        #raise NotImplementedError

    def _mv(self, src_path, dest_path):
        print('TODO mv', src_path, dest_path)
        #raise NotImplementedError
