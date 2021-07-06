import sys
import time
import logging
import subprocess
import argparse
from threading import Thread

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('--tb-port', type=int, default=9000, help='Port of tensorboard server')
    parser.add_argument('--tb-logdir', type=str, default='tensorboard', help='Directory of tensorboard log files')
    return parser

class Tensorboard(Thread):
    def __init__(self):
        super().__init__()
        args, _ = get_parser().parse_known_args(sys.argv[min(len(sys.argv), 1):])
        self.port = args.tb_port
        self.logdir = args.tb_logdir

    def run(self):
        subprocess.run(['tensorboard', '--logdir', self.logdir, '--port', str(self.port)])