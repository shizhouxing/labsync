"""Shortcuts for LaTex."""
import sys
import argparse
import os
import subprocess

def get_parser():
    parser = argparse.ArgumentParser(
        prog='lab tex',
        description='LaTeX document build and synchronization utilities'
    )
    parser.add_argument('command', type=str, choices=['git', 'clean', 'build'],
                        help='Command: git (sync with Git/Overleaf), clean (remove temp files), build (compile LaTeX)')
    parser.add_argument('--main_file', '--main', '-m', type=str, default='main',
                        help='Main LaTeX file name without extension (default: main)')
    return parser

def latex():
    if len(sys.argv) == 2:
        args = get_parser().parse_args(['git'])
    else:
        args = get_parser().parse_args(sys.argv[2:])
    command = args.command
    if command == 'git':
        # overleaf updates
        subprocess.run(['git', 'add', '.'],
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
