import logging
import argparse
import json

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab init')
    return parser

config = {
    'servers': {},
    'ignore_patterns': [
        '__pycache__',
        '.DS_Store',
        '.pytest_cache',
        '*.pyc'
    ],
    'latex': {
        'patterns': [
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
    }
}

def get_bool(question, default=True):
    yes = {'yes', 'y'}
    no = {'no', 'n'}
    while True:
        default_choice = 'yes' if default else 'no'
        print(f'{question} ({default_choice})', end=' ')
        line = input().lower()
        if line == '':
            return default
        elif line in yes:
            return True
        elif line in no:
            return False

def get_str(question, default=''):
    print(question, end='')
    ans = input()
    if ans == '':
        ans = default
    return ans

def init():
    print('This tool helps you to create a basic configuration file')
    print('Use `lab` afterwards to start the main program.')
    print()

    print('Please input the host of each server you want to use,',
          'separated by spaces.')
    print('These servers should have been used previously, and exist in the SSH'
        ' configuration file (typically ~/.ssh/config).')
    hosts = []
    for host in input('Hosts: ').split(' '):
        host = host.strip()
        if len(host) > 0:
            hosts.append(host)

    print('Please specify the working directory on the remote server(s)',
          '(do not use "~"):')
    config['remote_path'] = input('Path: ')
    for host in hosts:
        config['servers'][host] = { 'enable': True }


    path = '.labsync.config.json'
    with open(path, 'w') as file:
        file.write(json.dumps(config, indent=4))
    print(f'Configuration saved to {path}')
