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
    parser.add_argument('path_src', type=str)
    parser.add_argument('path_dest', type=str)
    return parser

def get_scp_args(server):
    server = get_server(server)
    scp_args = ['scp']
    if 'jump' in server:
        scp_args += ['-J', server['jump']]
    if 'port' in server:
        scp_args += ['-P', str(server['port'])]
    return server, scp_args

def scp_file(method, server, path_src, path_dest, allow_directory=True):
    server, scp_args = get_scp_args(server)
    if allow_directory:
        scp_args.append('-r')
    if method == 'get':
        scp_args += ['{}@{}:{}'.format(server['username'], server['host'], path_src), path_dest]
    elif method == 'put':
        scp_args += [path_src, '{}@{}:{}'.format(server['username'], server['host'], path_dest)]
    else:
        raise NotImplementedError('Unknown method for scp_file: {}'.format(method))
    print(scp_args)
    subprocess.run(scp_args)

def file_transfer():
    args = get_parser().parse_args(sys.argv[1:])
    scp_file(args.method, args.server, args.path_src, args.path_dest)
