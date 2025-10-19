import logging
import argparse
import sys
from labsync.latex import latex
from labsync.google_drive import google_drive
from labsync.cluster import cluster
from labsync.hf import hf

logger = logging.getLogger(__name__)

def get_global_parser():
    parser = argparse.ArgumentParser(add_help=False)
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

    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']):
        full_parser = argparse.ArgumentParser(
            description='LabSync - A development toolkit for university lab servers'
        )
        full_parser.add_argument('command', type=str,
                                choices=['tex', 'google-drive', 'gd', 'cluster', 'ls', 'jobs', 'kill', 'bash', 'hf'],
                                nargs='?', help='Command to run')
        full_parser.print_help()
        return

    args, _ = parser.parse_known_args()

    if args.command in shortcuts:
        expanded = shortcuts[args.command]
        if ' ' in expanded:
            parts = expanded.split(' ', 1)
            args.command = parts[0]
            if len(sys.argv) < 3 or sys.argv[2] not in ['-h', '--help']:
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
