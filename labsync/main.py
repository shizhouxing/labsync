import logging
import argparse
import sys
from labsync.latex import latex
from labsync.google_drive import google_drive
from labsync.cluster import cluster
from labsync.hf import hf

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='cluster',
                        choices=['tex',
                                'google-drive', 'gd', 'cluster', 'ls', 'jobs', 'kill', 'bash', 'hf'],
                        nargs='?', help='Command of this run')
    shortcuts = {
        'gd': 'google-drive',
        'ls': 'cluster ls',
        'jobs': 'cluster jobs',
        'kill': 'cluster kill',
        'bash': 'cluster bash',
        'hf': 'hf ls'
    }
    return parser, shortcuts

def cli_main():
    parser, shortcuts = get_global_parser()
    args, _ = parser.parse_known_args()
    # Apply shortcuts
    if args.command in shortcuts:
        expanded = shortcuts[args.command]
        if ' ' in expanded:
            # Handle commands with subcommands like 'cluster ls'
            parts = expanded.split(' ', 1)
            args.command = parts[0]
            # Insert the subcommand into sys.argv
            sys.argv.insert(2, parts[1])
        else:
            args.command = expanded
    if args.command == 'tex':
        latex()
    elif args.command == 'google-drive':
        google_drive()
    elif args.command == 'cluster':
        cluster()
    elif args.command == 'hf':
        hf()

if __name__ == '__main__':
    cli_main()
