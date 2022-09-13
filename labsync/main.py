import logging
import argparse
from labsync.listen import listen
from labsync.tb_update import tb_update
from labsync.init import init
from labsync.taskmanager import task_manager_entry
from labsync.overleaf import overleaf
from labsync.google_drive import google_drive

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen',
                        choices=['listen', 'tb', 'tb-update', 'init', 'get',
                                'put', 'task', 'overleaf', 'ol', 'google-drive',
                                'gd'],
                        nargs='?', help='Command of this run')
    shortcuts = {
        'tb': 'tb-update',
        'ol': 'overleaf',
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
    elif args.command == 'overleaf':
        overleaf()
    elif args.command == 'google-drive':
        google_drive()

if __name__ == '__main__':
    cli_main()
