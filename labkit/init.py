import logging
import argparse
import json

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab init')
    return parser

config = {
    "watchfs": {
        "servers": {},   
        "ignore_patterns": [
            "__pycache__"            
            "*/.git/*",
            "*/events.*",
            "./tensorboard/*",
            "log",            
        ]
    }
}

def get_bool(question, default=True):
    yes = {'yes', 'y'}
    no = {'no', 'n'}
    while True:
        print('{} ({})'.format(question, 'yes' if default else 'no'), end=' ')
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

def parse_ssh(command):
    ssh = {}
    args = command.split()
    i = 0
    while i < len(args):
        if args[i] == '-p':
            ssh['port'] = int(args[i + 1])
        elif args[i] == '-J':
            ssh['jump'] = args[i + 1]
        else:
            if i + 1 < len(args):
                raise ValueError('Failed to parse {}'.format(' '.join(args[i:])))
            ssh['username'] = args[i][:args[i].find('@')]
            ssh['host'] = args[i][args[i].find('@')+1:]
            return ssh
        i += 2
    return ssh

def init():
    print('This tool helps you to create a config.json file with common items.')
    print('Use `lab` afterwards to start.')
    print()

    while True:
        n = len(config['watchfs']['servers']) 

        if n == 0:
            add = get_bool('Add a server?', default=True)
        else:
            add = get_bool('Add one more server?', default=False)
        if not add:
            break
            
        ssh = get_str('SSH command: ssh ')
        dest = get_str('Destination directory: ')
        default_alias = 'Server{}'.format(n)
        alias = get_str('Server alias (default: {}): '.format(default_alias), default=default_alias)

        try:
            config['watchfs']['servers'][alias] = parse_ssh(ssh)
        except:
            raise ValueError('Failed to parse SSH command: {}'.format(ssh))
        config['watchfs']['servers'][alias]['dest'] = dest
        config['watchfs']['servers'][alias]['enable'] = True

    tb = get_bool('Use Tensorboard?', default=False)
    if tb:
        port = get_str('Tensorboard port (default: 9000): ', default='9000')
        logdir = get_str('Logdir (default: tensorboard): ', default='tensorboard')
        config['tensorboard'] = {
            'port': port,
            'logdir': logdir
        }
    
    with open('config.json', 'w') as file:
        file.write(json.dumps(config, indent=4))

    print('Configuration file saved to config.json')