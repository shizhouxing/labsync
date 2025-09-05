import logging
import argparse
import sys
from labsync.listen import listen
from labsync.init import init
from labsync.latex import latex
from labsync.google_drive import google_drive
from labsync.cluster import cluster
from labsync.hf import hf

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='listen',
                        choices=['listen', 'init', 'tex', 
                                'google-drive', 'gd', 'cluster', 'ls', 'jobs', 'kill', 'hf'],
                        nargs='?', help='Command of this run')
    shortcuts = {
        'gd': 'google-drive',
        'ls': 'cluster ls',
        'jobs': 'cluster jobs',
        'kill': 'cluster kill',
        'hf': 'hf ls'
    }
    return parser, shortcuts

def cli_main():
    parser, shortcuts = get_global_parser()
    args, _ = parser.parse_known_args()
    # Apply shortcuts - special handling for kill which needs arguments
    if args.command in shortcuts and (len(sys.argv) == 2 or args.command == 'kill'):
        expanded = shortcuts[args.command]
        if ' ' in expanded:
            # Handle commands with subcommands like 'cluster ls'
            parts = expanded.split(' ', 1)
            args.command = parts[0]
            # Insert the subcommand into sys.argv
            sys.argv.insert(2, parts[1])
        else:
            args.command = expanded
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
    elif args.command == 'hf':
        hf()

if __name__ == '__main__':
    cli_main()
