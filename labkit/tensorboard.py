import sys
import time
import logging
import subprocess
import labkit.utils
from threading import Thread

logger = logging.getLogger(__name__)

class Tensorboard(Thread):
    def __init__(self, config):
        super().__init__()
        self.port = config.get('port', 8000)
        self.logdir = config.get('logdir', '.')

    def run(self):
        subprocess.run(['tensorboard', '--logdir', self.logdir, '--port', str(self.port)])