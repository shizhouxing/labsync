# LabSync

A development toolkit designed for university lab servers. Key functionalities include:

- **File Synchronization**: Monitor local file changes and synchronize them to multiple remote servers
- **LaTeX Tools**: Build and manage LaTeX documents with Git integration
- **Google Drive Integration**: Upload files directly to Google Drive
- **Cluster Shortcuts**: Shortcuts for working with SLURM clusters

## Getting Started

LabSync is developed in Python 3 (version 3.10+ recommended).

**Install from source:**
```bash
pip install .
```

**For development:**
```bash
pip install -e .
```

**Initialize configuration:**
```bash
lab init
```
This creates a configuration file at `~/.labsync.config.json` with your server details.

## File Synchronization

Start monitoring local changes and synchronizing them to remote servers:
```bash
lab [OPTIONS]
```

**Options:**
- `-p PATH` - Specify the working directory on remote servers (relative to the default server path)

## Google Drive Integration

Use `lab gd` to upload files directly from servers to Google Drive. This feature is powered by the `pydrive` library.

### Initial Setup

1. Create a project on [Google Cloud Console](https://console.cloud.google.com/)
2. Obtain a credential JSON file (Project → APIs and services → Credentials)
3. When prompted, copy and paste the credential file content into the console
4. Complete authentication through your web browser

**Note for remote servers:** If your system doesn't support interactive web browsers, the program will display a URL for manual authentication. Copy this URL and open it on your local machine. After authentication, you'll be redirected to a localhost callback URL. Return to the remote server and access this URL using `curl`.

### Usage

**Upload a single file:**
```bash
lab gd PATH
```

**Upload a directory:**
```bash
lab gd -r PATH
```
This archives the directory and uploads the compressed file.

## LaTeX Tools

```bash
lab tex COMMAND
```

**Available commands:**
- `git` - Synchronize changes with Git or Overleaf (pull and push)
- `build` - Compile LaTeX documents
- `clean` - Remove temporary files

## Cluster Shortcuts

View GPU status and usage on SLURM clusters:

```bash
lab cluster ls
# or use the shortcut:
lab ls
```

## HuggingFace

**Requirements:**
- `git-lfs` (if using conda: `conda install -c conda-forge git-lfs`)

**List repositories:**
```bash
lab hf ls
# or use the shortcut:
lab hf
```

**Delete a repository:**
```bash
lab hf rm REPO_NAME
```

**Copy a repository:**
```bash
lab hf cp ORIGINAL_REPO NEW_REPO
```
