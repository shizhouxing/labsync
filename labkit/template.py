"""
Template for creating new functionalities
"""

import logging
import argparse

logger = logging.getLogger(__name__)

def get_parser():
    parser = argparse.ArgumentParser(prog='lab new-func')
    return parser

def func():
    pass
