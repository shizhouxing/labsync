import sys
import logging
import argparse
import subprocess
import labkit.utils
from labkit.utils import user_data_dir, get_config

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=str)
    parser.add_argument('server', type=str)
    parser.add_argument('path_remote', type=str)
    parser.add_argument('path_local', type=str)
    parser.add_argument('--config', type=str, default='config.json', help='Path of the configuration JSON file')
    return parser

def file_transfer():
    args = get_parser().parse_args(sys.argv[1:])
    config = get_config(args.config)
    if not args.server in config['watchfs']['servers']:
        raise ValueError('Unknown server {}'.format(args.server))
    server = config['watchfs']['servers'][args.server]
    scp_args = ['scp']
    if 'jump' in server:
        scp_args += ['-J', server['jump']]
    if 'port' in server:
        scp_args += ['-P', str(server['port'])]
    remote = '{}@{}:{}'.format(server['username'], server['host'], args.path_remote)
    if args.method == 'get':
        scp_args += [remote, args.path_local]
    elif args.method == 'put':
        scp_args += [args.path_local, remote]
    else:
        raise NotImplementedError('Unknown method {}'.format(args.method))
    scp_args.append(args.path_local)
    subprocess.run(scp_args)
