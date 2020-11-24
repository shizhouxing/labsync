# LabKit

This is a toolkit for development on university lab servers. 
The major functionality is to watch local file changes and synchronize them to multiple remote servers.
This is particularly designed for the scenario when there are **multiple servers in a university lab without a unified system**, and one may want to keep files on all remote servers consistent with local changes, and they can later pick an available server and run the code on it.
Although one may utilize VSCode with SSH extension to develop on a remote server, sometimes it can frequently get disconnected and need a slow reconnection and IDE refreshing, and it does not synchronize changes to multiple server simultaneously.
This toolkit is also intended to include some other shortcuts that may be frequently used, such as synchronizing Tensorboard logs.

Currently we only have an initial implementation and it is under development for optimizing file synchronization and extending functionalities.

## Installation

The code is based on Python 3. To install, run:

```bash
python setup.py install
```

Or run `python setup.py develop` for development.

## Usage

For major functionalities, run:

```
lab CONFIG_FILE_PATH
```

There should be a configuration JSON file at the `CONFIG_FILE_PATH` path.  The path is set to `config.json` by default. The configuration file contains several items where each corresponds to an integrated functionality. See details below.

## Functionalities

### WatchFS

Watch for changes in the local file system and synchronize them to multiple remote servers. To enable it, add an item to the configuration:

```
"watchfs": {
    "servers": {
        "server-name": {
            "username": "username",
            "host": "host",
            "port": 22,
            "jump": "username@host"
        }
    },
    "ignore_patterns": [
        "*/.git/*"
    ]
}
```

Each item in `servers` correspond to an SSH connection to a server: `ssh [-p PORT] [-J JUMP] USERNAME@HOST`, where `port` and `jump` are optional arguments. `ignore_patterns` stands for ignoring files that match any of the patterns.

### Tensorboard

Start a Tensorboard server locally. To enable it, add the following item to the configuration:

```Json
"tensorboard": {
    "port": 9000,
    "logdir": "tensorboard"
}
```

This configuration corresponds to starting a tensorboard server with `tensorboard --port PORT --logdir LOGDIR`.
