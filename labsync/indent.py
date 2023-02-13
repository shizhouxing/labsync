"""Modify indentation of Python files.

Only indentations with spaces are supported but not tabs.
"""

import sys
import argparse
import os

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('before', type=int, default=2,
                        help='Indentation before modification.')
    parser.add_argument('after', type=int, default=4,
                        help='Indetation after modification.')
    parser.add_argument('files', type=str, nargs='+', help='List of files.')
    parser.add_argument('--bak', action='store_true',
                        help='Generate backup files.')
    return parser

def indent_file(filename, before, after, bak=False):
    print(f'Processing {filename}')
    with open(filename) as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        count_indentation = 0
        while count_indentation < len(line) and line[count_indentation] == ' ':
            count_indentation += 1
        add_indentation = count_indentation // before * (after - before)
        lines[i] = ' ' * add_indentation + lines[i]
    if bak:
        os.system(f'cp {filename} {filename}.bak')
    with open(filename, 'w') as file:
        file.writelines(lines)

def indent():
    args = get_parser().parse_args(sys.argv[2:])
    for filename in args.files:
        indent_file(filename, args.before, args.after, args.bak)
