import sys
import argparse
import tempfile
import fnmatch
import os
from huggingface_hub import HfApi, snapshot_download, upload_folder
from huggingface_hub.errors import RepositoryNotFoundError
from datasets import load_dataset, DatasetDict, concatenate_datasets

def get_repo_size(repo_info):
    """Calculates the total size of a repository from its file metadata."""
    size_in_bytes = 0
    if hasattr(repo_info, 'siblings') and repo_info.siblings:
        for file in repo_info.siblings:
            if file.size:
                size_in_bytes += file.size
    return size_in_bytes

def format_size(size_in_bytes):
    """Converts bytes to a human-readable format."""
    if size_in_bytes == 0:
        return "0.00 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"


def hf_concat(main_repo, source_repos):
    """
    Concatenates multiple dataset repositories into a new main repository.
    """

    print(f"Creating concatenated dataset: {main_repo}")
    print(f"Source repositories: {', '.join(source_repos)}")

    source_datasets = []
    all_splits = set()

    for source_repo in source_repos:
        print(f"Loading dataset: {source_repo}")
        dataset = load_dataset(source_repo)
        source_datasets.append(dataset)
        print(f"  Successfully loaded {source_repo}")
        all_splits.update(dataset.keys())

    if not source_datasets:
        print("No datasets were successfully loaded.")
        return

    concatenated_splits = {}
    for split_name in all_splits:
        datasets_for_split = []

        for dataset in source_datasets:
            if split_name in dataset:
                datasets_for_split.append(dataset[split_name])

        if datasets_for_split:
            print(f"Concatenating {split_name} split...")
            try:
                concatenated_splits[split_name] = concatenate_datasets(datasets_for_split)
                print(f"  {split_name} split has {len(concatenated_splits[split_name])} examples")
            except Exception as e:
                print(f"Error concatenating {split_name} split: {e}")
                return

    final_dataset = DatasetDict(concatenated_splits)
    print(f"Uploading concatenated dataset to {main_repo}...")
    final_dataset.push_to_hub(
        main_repo,
        commit_message=f"Concatenate datasets: {', '.join(source_repos)}",
        private=True
    )
    print(f"Successfully created concatenated dataset: {main_repo}")


def hf_replace(key, repo_A, repo_B):
    """
    Replace the column named "key" in repo_A with values from repo_B
    """
    print(f"Loading source dataset: {repo_B}")
    dataset_B = load_dataset(repo_B)

    print(f"Loading target dataset: {repo_A}")
    dataset_A = load_dataset(repo_A)

    # Check if the key column exists in both datasets
    for split_name in dataset_A.keys():
        if split_name not in dataset_B:
            print(f"Error: Split '{split_name}' not found in source dataset {repo_B}")
            return

        if key not in dataset_B[split_name].column_names:
            print(f"Error: Column '{key}' not found in source dataset {repo_B} split '{split_name}'")
            return

        if len(dataset_A[split_name]) != len(dataset_B[split_name]):
            print(f"Error: Split '{split_name}' has different lengths: {len(dataset_A[split_name])} vs {len(dataset_B[split_name])}")
            return

    updated_splits = {}
    for split_name in dataset_A.keys():
        print(f"Replacing column '{key}' in split '{split_name}'...")
        if key in dataset_A[split_name].column_names:
            dataset_split = dataset_A[split_name].remove_columns([key])
        else:
            dataset_split = dataset_A[split_name]
        dataset_split = dataset_split.add_column(key, dataset_B[split_name][key])
        updated_splits[split_name] = dataset_split

    updated_dataset = DatasetDict(updated_splits)

    print(f"Uploading updated dataset to {repo_A}...")
    updated_dataset.push_to_hub(
        repo_A,
        commit_message=f"Replace column '{key}' with values from {repo_B}",
        private=True
    )
    print(f"Successfully replaced column '{key}' in {repo_A}")


def hf_split_train_test(repo_name, test_ratio):
    """
    Split a dataset into train and test splits
    """
    print(f"Loading dataset {repo_name}...")
    dataset = load_dataset(repo_name)
    assert len(dataset) == 1 and "train" in dataset
    dataset = dataset["train"].train_test_split(test_size=test_ratio)
    print(f"Uploading split dataset to {repo_name}...")
    dataset.push_to_hub(
        repo_name,
        commit_message=f"Split dataset into train and test with ratio {test_ratio}",
    )


def hf_reset(repo_url, commit_id):
    """
    Reset a repository to a previous commit
    """
    print(f"Loading dataset {repo_url} at commit {commit_id}...")
    dataset = load_dataset(repo_url, revision=commit_id)
    print(f"Uploading dataset content from commit {commit_id}...")
    dataset.push_to_hub(
        repo_url,
        commit_message=f"Reset to commit {commit_id}",
        private=True
    )


def hf_upload(repo_path):
    """
    Upload a local repository to HuggingFace Hub.
    """
    api = HfApi()
    username = api.whoami()["name"]
    repo_name = os.path.basename(repo_path.rstrip('/'))
    hf_repo_id = f"{username}/{repo_name}"
    print(f"Uploading local repository: {repo_path}")
    print(f"Target HuggingFace repository: {hf_repo_id}")
    api.create_repo(repo_id=hf_repo_id, private=True, exist_ok=True)
    upload_folder(
        folder_path=repo_path,
        repo_id=hf_repo_id,
        commit_message=f"Upload local repository from {repo_path}"
    )


def hf_copy(original_repo, new_repo, commit_id=None):
    """
    Duplicates a repository under the authenticated user's name.
    """
    try:
        api = HfApi()

        if commit_id:
            print(f"Copying repository from {original_repo} to {new_repo} at commit {commit_id}")
        else:
            print(f"Copying repository from {original_repo} to {new_repo}")

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_download(
                repo_id=original_repo, repo_type="dataset",
                local_dir=temp_dir, local_dir_use_symlinks=False, revision=commit_id
            )

            print(f"Creating new repository {new_repo}...")
            api.create_repo(repo_id=new_repo, repo_type="dataset", private=True, exist_ok=True)

            print(f"Uploading to {new_repo}...")
            commit_msg = f"Copy of {original_repo}"
            if commit_id:
                commit_msg += f" at commit {commit_id}"
            upload_folder(
                folder_path=temp_dir, repo_id=new_repo, repo_type="dataset",
                commit_message=commit_msg
            )

        copy_type = f"dataset at commit {commit_id}" if commit_id else "dataset"
        print(f"Successfully copied {copy_type}: {original_repo} -> {new_repo}")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Please ensure you are logged in with 'huggingface-cli login'.", file=sys.stderr)


def hf_delete(repo_patterns):
    """
    Deletes repository(ies) matching the patterns under the authenticated user's name.
    Supports glob patterns like 'rl_202504*' and multiple patterns.
    """
    try:
        api = HfApi()
        username = api.whoami()["name"]

        print("Fetching repository list...")
        all_repos = _get_all_repositories(api, username)

        matching_repos = set()
        for pattern in repo_patterns:
            for repo_name, repo_type in all_repos:
                # Check if pattern matches the repo name (with or without username)
                if fnmatch.fnmatch(repo_name, pattern) or fnmatch.fnmatch(repo_name.split('/')[-1], pattern):
                    matching_repos.add((repo_name, repo_type))

        matching_repos = list(matching_repos)

        if not matching_repos:
            print(f"No repositories found matching patterns: {', '.join(repo_patterns)}")
            return

        # Check if any patterns contain glob characters
        has_glob_patterns = any('*' in pattern or '?' in pattern or '[' in pattern for pattern in repo_patterns)

        print(f"\nFound {len(matching_repos)} repository(ies) matching patterns {repo_patterns}:")
        print("-" * 81)
        for repo_name, repo_type in sorted(matching_repos):
            print(f"{repo_name:<70} ({repo_type})")
        print("-" * 81)

        # Only ask for confirmation if glob patterns are used
        if has_glob_patterns:
            confirm = input(f"\nAre you sure you want to delete these {len(matching_repos)} repository(ies)? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Deletion cancelled.")
                return

        deleted_count = 0
        for repo_name, repo_type in sorted(matching_repos):
            try:
                print(f"Deleting {repo_type}: {repo_name}...")
                api.delete_repo(repo_id=repo_name, repo_type=repo_type)
                print(f"Successfully deleted {repo_type}: {repo_name}")
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {repo_type} {repo_name}: {e}", file=sys.stderr)

        print(f"\nDeleted {deleted_count} out of {len(matching_repos)} repositories.")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Please ensure you are logged in with 'huggingface-cli login'.", file=sys.stderr)


def _get_all_repositories(api, username):
    """
    Get all repositories (models and datasets) for a user.
    Returns a list of tuples: (repo_name, repo_type)
    """
    repositories = []

    try:
        model_repos = api.list_models(author=username)
        for model in model_repos:
            repositories.append((model.modelId, "model"))
    except Exception as e:
        print(f"Warning: Could not fetch models: {e}", file=sys.stderr)

    try:
        dataset_repos = api.list_datasets(author=username)
        for dataset in dataset_repos:
            repositories.append((dataset.id, "dataset"))
    except Exception as e:
        print(f"Warning: Could not fetch datasets: {e}", file=sys.stderr)

    return repositories


def hf_ls():
    """
    Lists the space usage of each model and dataset under the authenticated
    Hugging Face user's name, sorted by size in descending order.
    """
    try:
        api = HfApi()
        username = api.whoami()["name"]

        print(f"Fetching repository information for user: {username}\n")

        model_repos = api.list_models(author=username)
        model_data = []
        print("Analyzing model sizes...")
        for model in model_repos:
            try:
                # Get the actual repository size including all commits
                model_info = api.model_info(repo_id=model.modelId, files_metadata=True)

                # Use usedStorage which includes total storage across all commits
                if hasattr(model_info, 'usedStorage') and model_info.usedStorage is not None:
                    total_size = model_info.usedStorage
                else:
                    # Fallback to calculating from current files only
                    total_size = get_repo_size(model_info)

                model_data.append({"id": model.modelId, "size": total_size})
            except RepositoryNotFoundError:
                print(f"Warning: Could not find repository {model.modelId}. It may have been deleted.", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not process model {model.modelId}. Error: {e}", file=sys.stderr)

        # Sort models by size in descending order
        model_data.sort(key=lambda x: x["size"], reverse=True)

        print("\nModels (sorted by size):")
        print("-" * 81)
        if not model_data:
            print("No models found.")
        else:
            for item in model_data:
                print(f"{item['id']:<70} {format_size(item['size']):>10}")

        # --- Process Datasets ---
        dataset_repos = api.list_datasets(author=username)
        dataset_data = []
        print("\nAnalyzing dataset sizes...")
        for dataset in dataset_repos:
            try:
                # Get the actual repository size including all commits
                dataset_info = api.dataset_info(repo_id=dataset.id, files_metadata=True)

                # Use usedStorage which includes total storage across all commits
                if hasattr(dataset_info, 'usedStorage') and dataset_info.usedStorage is not None:
                    total_size = dataset_info.usedStorage
                else:
                    # Fallback to calculating from current files only
                    total_size = get_repo_size(dataset_info)

                dataset_data.append({"id": dataset.id, "size": total_size})
            except RepositoryNotFoundError:
                print(f"Warning: Could not find repository {dataset.id}. It may have been deleted.", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not process dataset {dataset.id}. Error: {e}", file=sys.stderr)

        # Sort datasets by size in descending order
        dataset_data.sort(key=lambda x: x["size"], reverse=True)

        print("\n" + "=" * 81 + "\n")
        print("Datasets (sorted by size):")
        print("-" * 81)
        if not dataset_data:
            print("No datasets found.")
        else:
            for item in dataset_data:
                print(f"{item['id']:<70} {format_size(item['size']):>10}")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Please ensure you are logged in with 'huggingface-cli login'.", file=sys.stderr)

def hf():
    """Handle HuggingFace commands."""
    parser = argparse.ArgumentParser(prog='lab hf', description='HuggingFace utilities')
    subparsers = parser.add_subparsers(dest='subcommand', help='Available subcommands')

    ls_parser = subparsers.add_parser('ls', help='List repositories and their sizes')

    rm_parser = subparsers.add_parser('rm', help='Delete repository(ies)')
    rm_parser.add_argument('repo_patterns', nargs='+', help='Repository name(s) or pattern(s) to delete')

    copy_parser = subparsers.add_parser('cp', help='Copy/duplicate a repository')
    copy_parser.add_argument('original_repo', help='Original repository name')
    copy_parser.add_argument('new_repo', help='New repository name')
    copy_parser.add_argument('--commit', '--commit-id', dest='commit_id', help='Specific commit ID to copy from')

    concat_parser = subparsers.add_parser('concat', help='Concatenate multiple repositories into one')
    concat_parser.add_argument('main_repo', help='Main repository name to create')
    concat_parser.add_argument('source_repos', nargs='+', help='Source repository names to concatenate')

    replace_parser = subparsers.add_parser('replace', help='Replace a column in dataset A with values from dataset B')
    replace_parser.add_argument('key', help='Column name to replace')
    replace_parser.add_argument('repo_A', help='Target dataset repository (will be modified)')
    replace_parser.add_argument('repo_B', help='Source dataset repository (provides new values)')

    reset_parser = subparsers.add_parser('reset', help='Reset repository to a previous commit')
    reset_parser.add_argument('repo_url', help='Repository name (e.g., username/repo-name)')
    reset_parser.add_argument('commit_id', help='Commit ID to reset to')

    split_parser = subparsers.add_parser('split-train-test', help='Split dataset into train and test splits')
    split_parser.add_argument('repo_name', help='Repository name to split')
    split_parser.add_argument('test_ratio', type=float, help='Ratio for test split ')

    upload_parser = subparsers.add_parser('upload', help='Upload a local repository to HuggingFace Hub')
    upload_parser.add_argument('repo_path', help='Path to the local repository to upload')

    # Get the args starting from position 2
    hf_args = sys.argv[2:]

    # If no arguments provided, default to ls
    if not hf_args:
        args = parser.parse_args(['ls'])
    else:
        args = parser.parse_args(hf_args)

    if args.subcommand == 'ls' or args.subcommand is None:
        hf_ls()
    elif args.subcommand == 'rm':
        hf_delete(args.repo_patterns)
    elif args.subcommand == 'cp':
        hf_copy(args.original_repo, args.new_repo, args.commit_id)
    elif args.subcommand == 'concat':
        hf_concat(args.main_repo, args.source_repos)
    elif args.subcommand == 'replace':
        hf_replace(args.key, args.repo_A, args.repo_B)
    elif args.subcommand == 'reset':
        hf_reset(args.repo_url, args.commit_id)
    elif args.subcommand == 'split-train-test':
        hf_split_train_test(args.repo_name, args.test_ratio)
    elif args.subcommand == 'upload':
        hf_upload(args.repo_path)
