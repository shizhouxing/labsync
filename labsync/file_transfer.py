import sys
import logging
import argparse
import subprocess
from .utils import user_data_dir, get_server

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=str)
    parser.add_argument('server', type=str)
    parser.add_argument('path_remote', type=str)
    parser.add_argument('path_local', type=str)
    return parser

def get_remote_path(server, path):
    server = get_server(server)
    scp_args = []
    if 'jump' in server:
        scp_args += ['-J', server['jump']]
    if 'port' in server:
        scp_args += ['-P', str(server['port'])]
    path = '{}@{}:{}'.format(server['username'], server['host'], path)
    return scp_args, path

def scp_file(method, server, path_remote, path_local, allow_directory=True):
    scp_args, path_remote = get_remote_path(server, path_remote)
    if allow_directory:
        scp_args.append('-r')
    scp_args = ['scp'] + scp_args
    if method == 'get':
        scp_args += [path_remote, path_local]
    elif method == 'put':
        scp_args += [path_local, remote]
    else:
        raise NotImplementedError('Unknown method for scp_file: {}'.format(method))
    subprocess.run(scp_args)

def file_transfer():
    args = get_parser().parse_args(sys.argv[1:])
    scp_file(args.method, args.server, args.path_remote, args.path_local)
