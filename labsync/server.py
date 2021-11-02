import os
import time
import threading
import logging
import subprocess
from collections import deque
from threading import Thread, Lock

logger = logging.getLogger(__name__)

class Server(Thread):
    def __init__(self, name, config, path, refresh_interval=0.05):
        super().__init__()
        self.name = name
        self.path_root = path
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

    def _get_remote_path(self, path):
        return os.path.join(self.path_root, path)

    def _upload(self, path):
        logger.info(f'Server {self.name}: uploading {path}')
        path = self._get_remote_path(path)
        subprocess.run(['scp', path, f'{self.name}:{path}'])

    def _mkdir(self, path):
        logger.info(f'Server {self.name}: mkdir {path}')
        path = self._get_remote_path(path)
        subprocess.run(['ssh', f'{self.name}', f'mkdir {self._get_remote_path(path)}'])

    def _mv(self, src_path, dest_path):
        print('TODO mv', src_path, dest_path)
        #raise NotImplementedError
