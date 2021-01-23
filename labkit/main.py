import sys
import logging
import argparse
import labkit.utils
from labkit.listen import listen
from labkit.tb_update import tb_update
from labkit.init import init
from labkit.file_transfer import file_transfer
from labkit.taskmanager import task_manager_entry

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen', 
                        choices=['listen', 'tb-update', 'init', 'get', 'put', 'task'], 
                        nargs='?', help='Command of this run')
    return parser

def cli_main():
    args, _ = get_global_parser().parse_known_args()
    if args.command == 'listen':
        listen()
    elif args.command == 'tb-update':
        tb_update()
    elif args.command in ['get', 'put']:
        file_transfer()
    elif args.command == 'init':
        init()
    elif args.command == 'task':
        task_manager_entry()

if __name__ == '__main__':
    cli_main()
