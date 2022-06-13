import sys
import logging
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
    if args.command == 'update':
        for p in patterns:
            subprocess.run(['git', 'add', p],     
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.STDOUT)
        os.system('git status')
        os.system('git commit -m "local update"')
        os.system('git pull origin master --no-edit')
        os.system('git push origin master')
    elif args.command == 'clean':
        os.system('rm -f *.log *.aux *.out *.bbl')
        print('Cleaned temporary files by Tex')
    elif args.command == 'compile':
        raise NotImplementedError(args.command)
    else:
        raise ValueError(f'Unknown command {command}')
    
    # TODO resolve conflicts