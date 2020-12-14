import sys
import time
import logging
import labkit.utils
from threading import Thread

logger = logging.getLogger(__name__)

class TaskManager(Thread):
    def __init__(self, config):
        super().__init__()

        self.db_dir = config['db_dir']

    def _find_device(n_gpus=1, memory=12000):
        stat = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.free,utilization.gpu', '--format=csv'], 
            stdout=subprocess.PIPE).stdout.decode().split('\n')[1:-1]
        gpus = []
        for i in range(len(stat)):
            # Format: "X MiB, Y %"
            gpu = stat[i].split()
            mem = int(gpu[0])
            if mem >= memory:
                gpus.append((i + 1, int(gpu[2])))
        gpus = [g[0] for g in sorted(gpus, key=lambda g: g[1])]
        return gpus[:n_gpus]

    def run(self):
        pass

if __name__ == '__main__':
    pass