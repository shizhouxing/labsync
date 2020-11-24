import sys
import logging
import argparse
import os
import time
import shutil
import labkit.utils
from labkit.utils import user_data_dir

logger = logging.getLogger(__name__)

tmp_dir = os.path.join(user_data_dir, 'tensorboard_logs')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab listen')
    parser.add_argument('-i', '--ids', type=str, default=[], nargs='*', help='Path of the configuration JSON file')
    parser.add_argument('-a', '--ssh-args', type=str, help='Arguments of SSH', required=True)    
    parser.add_argument('-p', '--prefix', type=str, help='Prefix of model directories', required=True)    
    parser.add_argument('-pi', '--prefix-id', type=str, default='', help='Prefix of ids')    
    parser.add_argument('-l', '--loop', type=int, help='Loop interval')
    return parser

def update(args, ids):
    for id in ids:
        source = '{}:{}{}/log'.format(args.ssh_args, args.prefix, id)
        logger.info('Updating {}'.format(source))
        tmp = os.path.join(tmp_dir, id)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        os.system('scp -r {} {}'.format(source, tmp.replace(' ', '\\ ')))
        shutil.copytree(tmp, id, dirs_exist_ok=True)

def tb_update():
    args = get_parser().parse_args(sys.argv[2:])
    logger.info('Updating Tensorboard logs...')
    if len(args.ids) == 0:
        ids = [args.prefix_id]
    else:
        ids = ['{}{}'.format(args.prefix_id, id) for id in args.ids]
    while True:
        update(args, ids)
        if args.loop:
            time.sleep(args.loop)
        else:
            break