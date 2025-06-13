import logging
import argparse
from labsync.listen import listen
from labsync.init import init
from labsync.latex import latex
from labsync.google_drive import google_drive
from labsync.cluster import cluster

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen',
                        choices=['listen', 'init', 'tex', 
                                'google-drive', 'gd', 'cluster'],
                        nargs='?', help='Command of this run')
    shortcuts = {
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
    elif args.command == 'init':
        init()
    elif args.command == 'tex':
        latex()
    elif args.command == 'google-drive':
        google_drive()
    elif args.command == 'cluster':
        cluster()

if __name__ == '__main__':
    cli_main()
