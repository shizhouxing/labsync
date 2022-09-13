import sys
import logging
import argparse
import os
import time
import shutil
import subprocess
from .utils import user_data_dir, get_server

logger = logging.getLogger(__name__)

tmp_dir = os.path.join(user_data_dir, 'tensorboard_logs')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', type=str, help='Server name')
    parser.add_argument('-p', '--prefix', type=str,
                        help='Prefix of model directories')
    parser.add_argument('-pi', '--prefix-id', type=str, default='',
                        help='Prefix of ids')
    parser.add_argument('-i', '--ids', type=str, default=[], nargs='*',
                        help='Path of the configuration JSON file')
    parser.add_argument('-l', '--loop', type=int, default=1,
                        help='Loop interval')

    # Not recommended to use
    parser.add_argument('-a', '--ssh-args', type=str, help='Arguments of SSH')

    return parser

def update_from_unknown_server(args, ids):
    """ SSH arguments must be specfied explicity and is not read
    from the configuration file. """
    for tid in ids:
        source = f'{args.ssh_args}:{args.prefix}{tid}/log'
        logger.info('Updating %s', source)
        tmp = os.path.join(tmp_dir, id)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        os.system('scp -r {} {}'.format(source, tmp.replace(' ', '\\ ')))
        shutil.copytree(tmp, id, dirs_exist_ok=True)

def update(args, ids):
    if not args.server:
        update_from_unknown_server(args, ids)
    else:
        server = get_server(args.server)
        if 'checkpoints' in server and not args.prefix:
            args.prefix = server['checkpoints']
        for tid in ids:
            path_remote = 'f{args.prefix}{tid}/log'
            logger.info('Updating %s', path_remote)
            tmp = os.path.join(tmp_dir, tid)
            if os.path.exists(tmp):
                shutil.rmtree(tmp)
            subprocess.run(
                ['ssh', f'{args.server}:{path_remote}', tmp], check=True)
            shutil.copytree(tmp, tid, dirs_exist_ok=True)

def tb_update():
    args = get_parser().parse_args(sys.argv[2:])
    if args.prefix:
        logger.warning('Hint: you are able to specify `--prefix` with a'
                       ' `checkpoints` item in the server configuration')
    logger.info('Updating Tensorboard logs...')
    if len(args.ids) == 0:
        ids = [args.prefix_id]
    else:
        ids = [f'{args.prefix_id}{tid}' for tid in args.ids]
    while True:
        update(args, ids)
        if args.loop == -1:
            return
        elif args.loop > 0:
            time.sleep(args.loop)
