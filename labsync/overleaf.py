import sys
import argparse
import os
import subprocess
from .utils import get_config

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=['update', 'clean'])
    return parser

def overleaf():
    args = get_parser().parse_args(sys.argv[2:])
    config = get_config()['overleaf']
    patterns = config['patterns']
    command = args.command
    if command == 'update':
        for p in patterns:
            subprocess.run(['git', 'add', p],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, check=True)
        os.system('git status')
        os.system('git commit -m "local update"')
        os.system('git pull origin master --no-edit')
        os.system('git push origin master')
    elif command == 'clean':
        os.system('rm -f *.log *.aux *.out *.bbl')
        print('Cleaned temporary files by Tex')
    elif command == 'compile':
        raise NotImplementedError(command)
    else:
        raise ValueError(f'Unknown command {command}')

    # TODO resolve conflicts
