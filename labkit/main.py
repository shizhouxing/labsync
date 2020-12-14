import sys
import logging
import argparse
import labkit.utils
from labkit.listen import listen
from labkit.tb_update import tb_update
from labkit.init import init

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen', 
                        choices=['listen', 'tb-update', 'init'], 
                        nargs='?', help='Command of this run')
    return parser

def cli_main():
    args, _ = get_global_parser().parse_known_args()
    if args.command == 'listen':
        listen()
    elif args.command == 'tb-update':
        tb_update()
    elif args.command == 'init':
        init()

if __name__ == '__main__':
    cli_main()
