# LabSync

A development toolkit designed for university lab servers. Key functionalities include:

- **Cluster Shortcuts**: Shortcuts for working with SLURM clusters
- **HuggingFace Shortcuts**: Shortcuts for working with HuggingFace repositories.
- **LaTeX Tools**: Build and manage LaTeX documents with Git integration
- **Google Drive Integration**: Upload files directly to Google Drive

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
* **List your SLURM jobs:** `lab cluster jobs` or use the shortcut `lab jobs`
* **Kill SLURM jobs by ID range:** `lab cluster kill START_JOB_ID END_JOB_ID` or use the shortcut `lab kill START_JOB_ID END_JOB_ID`
* **Connect to a job with bash:** `lab cluster bash JOB_ID` or use the shortcut `lab bash JOB_ID`
* **Submit a SLURM job:** `lab cluster submit PARTITION [OPTIONS] -- COMMAND`

### Submit Job Options:
* `--gpus N`: Number of GPUs to request (default: 1)
* `--cpus N`: Number of CPUs per task (default: 12)
* `--mem SIZE`: Memory to request (default: 128G)
* `--conda ENV`: Conda environment to activate before running command
* `--path PATH`: Prepend PATH to environment PATH variable
* `--account ACCOUNT`: SLURM account to use
* `--dependency JOB_ID`: Job dependency (runs after specified job completes successfully)

**Example:**
```bash
lab cluster submit gpu --gpus 2 --cpus 16 --mem 256G --conda myenv -- python train.py
```

## HuggingFace

**Requirements:**
- `git-lfs` (if using conda: `conda install -c conda-forge git-lfs`)

**Commands:**
* **List repositories:** `lab hf ls` or use the shortcut `lab hf`
* **Delete a repository:** `lab hf rm REPO_NAME`
* **Copy a repository:** `lab hf cp ORIGINAL_REPO NEW_REPO [--commit COMMIT_ID]`
* **Rename/move a repository:** `lab hf mv ORIGINAL_REPO NEW_REPO`
* **Upload a local repository:** `lab hf upload REPO_PATH`
* **Concatenate multiple repositories:** `lab hf concat MAIN_REPO SOURCE_REPO1 SOURCE_REPO2 ...`
* **Replace a column in one repository with values from another:** `lab hf replace COLUMN_NAME TARGET_REPO SOURCE_REPO`
* **Reset a repository to a previous commit:** `lab hf reset REPO_NAME COMMIT_ID`
* **Split dataset into train and test:** `lab hf split-train-test REPO_NAME TEST_RATIO`

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

**Usage:** `lab gd [OPTIONS] PATH...`

**Options:**
* `-r`: Upload directory as archive
* `-d, --direct`: Upload directory directly without archiving (preserves structure)
* `-f, --folder FOLDER_NAME`: Upload to a specific folder or shared drive
* `-j, --njobs NJOBS`: Number of parallel upload jobs (default: 1)
* `-c, --continue`: Skip files that already exist in destination
* `--max-files N`: Auto-archive directories with more than N files (default: 100)

