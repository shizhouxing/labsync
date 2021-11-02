import sys
import logging
import argparse
import os
import subprocess

patterns = [
    '*.tex',
    '*.bib',
    '*.bst',
    '*.sty',
    '*.pdf',
    'images',
    'figures',
    'image',
    'figure',
    'img'
]

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=['update'])
    return parser

def overleaf():
    args = get_parser().parse_args(sys.argv[2:])
    if args.command == 'update':
        for p in patterns:
            subprocess.run(['git', 'add', p],     
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.STDOUT)
        os.system('git status')
        os.system('git commit -m "local update"')
        os.system('git pull origin master --no-edit')
        os.system('git push origin master')
    elif args.command == 'compile':
        raise NotImplementedError(args.command)
    else:
        raise ValueError(f'Unknown command {command}')
    
    # TODO resolve conflicts