# LabSync

This is a toolkit for development on university lab servers. 
The major functionality is to watch local file changes and synchronize them to multiple remote servers.
It is also intended to include some other shortcuts that may be frequently used
while working with remote servers, such as synchronizing Tensorboard logs, 
or uploading files to Google Drive.

## Installation

The program is based on Python 3 (3.7+ is recommended). To install it, run:
```bash
python setup.py install
```
Or run `python setup.py develop` for development.

Initialize a configuration file by inputing server information:
```bash
lab init
```
The configuration file will be stored at `~/.labsync.config.json`.
See the format of the [configuration file](https://github.com/shizhouxing/labsync/wiki/Configuration-file).

## Synchronizing Local Changes

Listen for local changes to be synchronized to all the remote servers:
```bash
lab [-t] [CONFIG] [-p PATH]
```
`-t` is optional for starting a Tensorboard server locally. 
`CONFIG` is also optional and can be used to specify an alternative configuration file. 
`-p PATH` is optional for specifying the working directory on remote servers relative
to the default path of the server.

## Google Drive

Shortcut `lab gd` can be used for directly uploading files (such as large checkpoint files)
from servers to Google Drive. This is based on the `pydrive` library. 

### Setup

For the first time to use this functionality, please create a project on  [Google Cloud Console](https://console.cloud.google.com/), and obtain a credential JSON file (Project -> APIs and services -> Credentials). You will be asked to copy and paste the content in the credential file to the console, and it will proceed to authentication using a web browser.

If you are using a terminal, the `webbrowser` Python library may proceed to a terminal browser, which may not work well for Google Could authentication. 
In this case, you may run `import webbrowser; print(webrowser)` in a Python terminal to check the path of `webbrowser.py`, and modify the code to disable registering terminal browsers (search for "console browsers" in the code). 
After this modification, the program is likely to print a URL instead of directly opening it. Please copy this URL and open it in your local machine to finish the authentication. In the end, it will redirect to a callback URL on localhost which does not work locally. Please return to the remote server to open this URL with `curl`.

### Upload a single file

```bash
lab gd PATH
```

### Upload a directory 

```bash
lab gd -r PATH
```
This will archive the directory and upload the archive.

## Overleaf

If you sometimes want to write in a local editor while also use Overleaf to store or share the document, 
you may use the following shortcut to pull remote changes 
and push local changes to Overleaf via Git.

```
lab ol update
```
