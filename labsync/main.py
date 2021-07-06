import sys
import logging
import argparse
import labsync.utils
from labsync.listen import listen
from labsync.tb_update import tb_update
from labsync.init import init
from labsync.file_transfer import file_transfer
from labsync.taskmanager import task_manager_entry
from labsync.overleaf import overleaf
from labsync.google_drive import google_drive

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen', 
                        choices=['listen', 'tb', 'tb-update', 'init', 'get', 
                                'put', 'task', 'overleaf', 'ol', 'gd'], 
                        nargs='?', help='Command of this run')
    shortcuts = {
        'tb': 'tb-update',
        'ol': 'overleaf'
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
    elif args.command in ['get', 'put']:
        file_transfer()
    elif args.command == 'init':
        init()
    elif args.command == 'task':
        task_manager_entry()
    elif args.command == 'overleaf':
        overleaf()
    elif args.command == 'gd':
        google_drive()

if __name__ == '__main__':
    cli_main()
