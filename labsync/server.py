import os
import time
import logging
import subprocess
from os.path import dirname
from threading import Thread, Lock
from subprocess import CalledProcessError

logger = logging.getLogger(__name__)

class Server(Thread):
    def __init__(self, name, path, refresh_interval=0.05):
        super().__init__()
        self.name = name
        self.path_root = path
        self.refresh_interval = refresh_interval
        self.tasks = []
        self.lock = Lock()
        logger.info('Server %s, root %s', self.name, self.path_root)

    def add_task(self, task):
        self.lock.acquire()
        existing = False
        for t in self.tasks:
            if t == task:
                existing = True
                break
        if not existing:
            self.tasks.append(task)
            logger.info('%s: %s', self.name, task)
        self.lock.release()

    def run(self):
        while True:
            self._check_tasks()

    def _check_tasks(self):
        while len(self.tasks) > 0:
            self.lock.acquire()
            task = self.tasks.pop(0)
            if task['action'] == 'upload':
                files = [task['path']]
                tasks_left = []
                for t in self.tasks:
                    if (t['action'] == 'upload'
                            and dirname(t['path']) == dirname(task['path'])):
                        # In the same directory. Merge it to one scp.
                        files.append(t['path'])
                    else:
                        tasks_left.append(t)
                self.tasks = tasks_left
            self.lock.release()
            if task['action'] == 'upload':
                self._upload(files)
            elif task['action'] == 'mkdir':
                self._mkdir(task['path'])
            elif task['action'] == 'mv':
                self._mv(task['src_path'], task['dest_path'])
            else:
                raise ValueError(f'Unknown action {task["action"]}')

            logger.info('%s: %d task(s) left', self.name, len(self.tasks))

        time.sleep(self.refresh_interval)

    def _get_remote_path(self, path):
        return os.path.join(self.path_root, path)

    def _upload(self, files):
        logger.info('%s: uploading %s', self.name, files)
        dn = dirname(files[0])
        remote_path = self._get_remote_path(dn)
        args_scp = ['scp'] + files + [f'{self.name}:{remote_path}']
        try:
            subprocess.check_output(args_scp, stderr=subprocess.STDOUT)
        except CalledProcessError as err:
            if 'No such file or directory' in err.output.decode():
                # Create the missing directory and retry
                self._mkdir(dn)
                subprocess.run(args_scp, stderr=subprocess.STDOUT, check=False)

    def _mkdir(self, path):
        logger.info('%s: mkdir %s', self.name, path)
        path = self._get_remote_path(path)
        mkdir_code = f"import os; os.makedirs('{path}',exist_ok=True)"
        subprocess.run(
            ['ssh', f'{self.name}', f'python3 -c "{mkdir_code}"'], check=False)

    def _mv(self, src_path, dest_path):
        print('TODO mv', src_path, dest_path)
        #raise NotImplementedError
