# LabSync

This is a toolkit for development on university lab servers. 
The major functionality is to watch local file changes and synchronize them to multiple remote servers.
This toolkit is also intended to include some other shortcuts that may be frequently used, such as synchronizing Tensorboard logs.

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
`-t` is optional for starting a Tensorboard server. `CONFIG` can be used to specify a configuration file. By default, it looks for a configuration file at `./.labsync-config.json` and `~/.labsync-config.json`. See the [format of configuration](https://github.com/shizhouxing/labsync/wiki/Configurations) (*to be updated*).

## Google Drive

There is a shortcut `lab gd` for directly uploading files to Google Drive from lab servers based on the `pydrive` library. 

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

Use Git to pull remote changes and push local changes to Overleaf: 

```
lab ol update
```
