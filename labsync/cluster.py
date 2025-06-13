import argparse
import sys


def get_parser():
    parser = argparse.ArgumentParser(prog='labsync cluster')
    subparsers = parser.add_subparsers(dest='subcommand', help='Cluster management commands')
    return parser


def cluster():
    """Main entry point for cluster management"""
    parser = get_parser()
    args = parser.parse_args(sys.argv[2:])
    
    # Placeholder for future subcommands
    pass