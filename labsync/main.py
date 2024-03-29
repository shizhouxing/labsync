import logging
import argparse
from labsync.listen import listen
from labsync.tb_update import tb_update
from labsync.init import init
from labsync.taskmanager import task_manager_entry
from labsync.latex import latex
from labsync.google_drive import google_drive
from labsync.indent import indent

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen',
                        choices=['listen', 'tb', 'tb-update', 'init', 'get',
                                'put', 'task', 'tex', 'latex', 'google-drive',
                                'gd', 'indent'],
                        nargs='?', help='Command of this run')
    shortcuts = {
        'tb': 'tb-update',
        'tex': 'latex',
        'gd': 'google-drive'
    }
    return parser, shortcuts

def cli_main():
    parser, shortcuts = get_global_parser()
    args, _ = parser.parse_known_args()
    if args.command in shortcuts:
        args.command = shortcuts[args.command]
    if args.command == 'listen':
        listen()
    elif args.command == 'tb-update':
        tb_update()
    elif args.command == 'init':
        init()
    elif args.command == 'task':
        task_manager_entry()
    elif args.command == 'latex':
        latex()
    elif args.command == 'google-drive':
        google_drive()
    elif args.command == 'indent':
        indent()

if __name__ == '__main__':
    cli_main()
