"""Task manager for managing experiment tasks."""

import sys
import time
import logging
import os
import subprocess
import argparse
from threading import Thread
from oslo_concurrency import lockutils
from oslo_concurrency.lockutils import synchronized
from .utils import user_data_dir

logger = logging.getLogger(__name__)
lockutils.set_defaults(os.path.join(user_data_dir, 'task.lock'))

def get_parser():
    parser = argparse.ArgumentParser(prog='lab task')
    parser.add_argument('type', type=str, choices=['listen', 'new'])
    parser.add_argument('--time-recycle', type=int, default=60,
                        help='Time interval to recycle a previously allocated'
                        'GPU, to avoid consecutively allocating two tasks to a '
                        'same device while the first one is still starting')
    return parser

class TaskManager(Thread):
    def __init__(self, args):
        super().__init__()
        self._init_db()
        self.time_recycle = args.time_recycle
        self.device_last_used = {}

    def _init_db(self):
        self.dir_tasks = os.path.join(user_data_dir, 'task')
        self.file_count = os.path.join(self.dir_tasks, 'count')
        self.dir_pending = os.path.join(self.dir_tasks, 'pending')
        self.dir_running = os.path.join(self.dir_tasks, 'running')
        if not os.path.exists(self.dir_tasks):
            os.makedirs(self.dir_tasks)
            os.makedirs(self.dir_pending)
            os.makedirs(self.dir_running)
            self._set_current_id(0)

    def _find_device(self, n_gpus=1, memory=12000):
        stat = subprocess.run([
            'nvidia-smi',
            '--query-gpu=memory.free,utilization.gpu',
            '--format=csv'
        ], stdout=subprocess.PIPE, check=True).stdout.decode().split('\n')[1:-1]
        gpus = []
        for i in range(len(stat)):
            if (time.time() - self.device_last_used.get(i, 0)
                    < self.time_recycle):
                continue
            # Format: "X MiB, Y %"
            gpu = stat[i].split()
            mem = int(gpu[0])
            # TODO For now, only check memory usage
            if mem >= memory:
                gpus.append((i, int(gpu[2])))
        gpus = [g[0] for g in sorted(gpus, key=lambda g: g[1])]
        return gpus[:n_gpus]

    # @synchronized('task', external=True)
    def new_task(self):
        commands = []
        while True:
            line = input()
            if len(line) == 0:
                break
            commands.append(line)
        tid = self._get_next_id()
        self._add_task(tid, commands)
        self._set_current_id(tid)
        logger.info('New task created, id=%d', tid)

    @synchronized('task', external=True)
    def _add_task(self, tid, commands):
        with open(os.path.join(self.dir_pending, str(tid)), 'w') as file:
            file.write('\n'.join(commands) + '\n')

    @synchronized('task', external=True)
    def _get_next_id(self):
        with open(self.file_count) as file:
            count = int(file.read())
        return count + 1

    @synchronized('task', external=True)
    def _set_current_id(self, tid):
        with open(self.file_count, 'w') as file:
            file.write(str(tid))

    def _get_pending_id(self):
        pending_ids = sorted(os.listdir(self.dir_pending))
        if pending_ids:
            return pending_ids[0]
        else:
            return None

    def _run_task(self, device):
        tid = self._get_pending_id()
        if not tid:
            return
        path = os.path.join(self.dir_running, tid)
        os.rename(os.path.join(self.dir_pending, tid), path)
        logger.info('Start running task id=%d on cuda:%s', tid, device)
        env = os.environ
        env['CUDA_VISIBLE_DEVICES'] = str(device)
        subprocess.Popen(
            ['bash', path], env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)
        self.device_last_used[device] = time.time()

    def run(self):
        # TODO Currently, we always use one full GPU for each task
        logger.info('Task Manager listening')
        while True:
            devices = self._find_device(memory=11000)
            if len(devices) > 0:
                self._run_task(devices[0])
            else:
                time.sleep(5)


def task_manager_entry():
    args = get_parser().parse_args(sys.argv[2:])
    task_manager = TaskManager(args)
    if args.type == 'listen':
        task_manager.run()
    elif args.type == 'new':
        task_manager.new_task()
