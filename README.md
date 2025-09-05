# LabSync

A development toolkit designed for university lab servers. Key functionalities include:

- **Cluster Shortcuts**: Shortcuts for working with SLURM clusters
- **HuggingFace Shortcuts**: Shortcuts for working with HuggingFace repositories.
- **LaTeX Tools**: Build and manage LaTeX documents with Git integration
- **Google Drive Integration**: Upload files directly to Google Drive
- File Synchronization (deprecated): Monitor local file changes and synchronize them to multiple remote servers

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

## Cluster Shortcuts

**Commands:**
* **View GPU status and usage:** `lab cluster ls` or use the shortcut `lab ls`
* **List your SLURM jobs:** `lab cluster jobs`
* **Kill SLURM jobs by ID range:** `lab cluster kill START_JOB_ID END_JOB_ID`

## HuggingFace

**Requirements:**
- `git-lfs` (if using conda: `conda install -c conda-forge git-lfs`)

**Commands:**
* **List repositories:** `lab hf ls` or use the shortcut `lab hf`
* **Delete a repository:** `lab hf rm REPO_NAME`
* **Copy a repository:** `lab hf cp ORIGINAL_REPO NEW_REPO`
* **Concatenate multiple repositories:** `lab hf concat MAIN_REPO SOURCE_REPO1 SOURCE_REPO2 ...`
* **Replace a column in one repository with values from another:** `lab hf replace COLUMN_NAME TARGET_REPO SOURCE_REPO`
* **Reset a repository to a previous commit:** `lab hf reset REPO_NAME COMMIT_ID`

## LaTeX Tools

**Commands:**
* **Synchronize changes with Git or Overleaf:** `lab tex git`
* **Compile LaTeX documents:** `lab tex build`
* **Remove temporary files:** `lab tex clean`


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

## File Synchronization

*(This functionality is not sufficiently documented and is no longer maintained as of 2025.)*

When using it for the first time, run:
```bash
lab init
```
This creates a configuration file at `~/.labsync.config.json` with your server details.

Start monitoring local changes and synchronizing them to remote servers:
```bash
lab [OPTIONS]
```

**Options:**
- `-p PATH` - Specify the working directory on remote servers (relative to the default server path)
