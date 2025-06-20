"""Shortcuts for LaTex."""
import sys
import argparse
import os
import subprocess
from .utils import get_config

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=['git', 'clean', 'build'])
    parser.add_argument('--main_file', '--main', '-m', type=str, default='main')
    return parser

def latex():
    if len(sys.argv) == 2:
        args = get_parser().parse_args(['git'])
    else:
        args = get_parser().parse_args(sys.argv[2:])
    config = get_config()['latex']
    patterns = config['patterns']
    command = args.command
    if command == 'git':
        # overleaf updates
        for p in patterns:
            subprocess.run(['git', 'add', p],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, check=False)
        os.system('git status')
        os.system('git commit -m "local update"')
        os.system('git pull origin master --no-edit')
        os.system('git push origin master')
        # TODO resolve conflicts
    elif command == 'clean':
        os.system('rm -f *.log *.aux *.out *.bbl')
        print('Cleaned temporary files by Tex')
    elif command == 'build':
        os.system(f'pdflatex {args.main_file}.tex')
        os.system(f'bibtex {args.main_file}')
        os.system(f'pdflatex {args.main_file}.tex')
        os.system(f'pdflatex {args.main_file}.tex')
    else:
        raise ValueError(f'Unknown command {command}')
