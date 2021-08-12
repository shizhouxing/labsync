# LabSync

This is a toolkit for development on university lab servers. 
The major functionality is to watch local file changes and synchronize them to multiple remote servers.
This is particularly designed for the scenario when there are **multiple servers in a university lab without a unified system**, and one may want to keep files on all remote servers consistent with local changes, and they can later pick an available server and run the code on it.
Although one may utilize VSCode with SSH extension to develop on a remote server, sometimes it can frequently get disconnected and need a slow reconnection and IDE refreshing, and it does not synchronize changes to multiple server simultaneously.
This toolkit is also intended to include some other shortcuts that may be frequently used, such as synchronizing Tensorboard logs.

Currently we only have an initial implementation and it is under development for optimizing file synchronization and extending functionalities.

## Installation

The code is based on Python 3. To install it, run:

```bash
python setup.py install
```

Or run `python setup.py develop` for development.

## Getting Started

Initialize a configuration file:

```bash
lab init
```

Listen for local changes:

```bash
lab [-t] [CONFIG]
```
`-t` is optional for starting a Tensorboard server. `CONFIG` can be used to specify a configuration file. By default, it looks for a configuration file at `./.labsync-config.json` and `~/.labsync-config.json`. See the [format of configuration](https://github.com/shizhouxing/labsync/wiki/Configurations).

## Google Drive

There is a shortcut `lab gd` for uploading files to Google Drive based on `pydrive`. 
To use it, first create a project on  [Google Cloud Console](https://console.cloud.google.com/), and obtain a credential JSON file (Project -> APIs and services -> Credentials). 
For the first time to use this shortcut, you will be asked to copy and paste the content in the credential file to the console, and it will proceed to authentication using a web browser.

Upload a file:

```bash
lab gd FILE_PATH
```

Add `-r` to allow archiving directories to `.tgz` and upload them.

## Overleaf

Use Git to pull and push changes to Overleaf: 

```
lab ol update
```
