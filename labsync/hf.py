import sys
import argparse
import tempfile
import shutil
import os
from huggingface_hub import HfApi, snapshot_download, upload_folder
from huggingface_hub.errors import RepositoryNotFoundError

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

def _copy_repo_via_clone(api, original_repo, new_repo, repo_type):
    """
    Copy a repository by downloading it and uploading to a new repo.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the original repository
        print(f"Downloading {original_repo}...")
        original_repo_path = snapshot_download(
            repo_id=original_repo,
            repo_type=repo_type,
            local_dir=temp_dir,
            local_dir_use_symlinks=False
        )
        
        # Create the new repository (private)
        print(f"Creating new repository {new_repo}...")
        api.create_repo(repo_id=new_repo, repo_type=repo_type, private=True, exist_ok=True)
        
        # Upload all files to the new repository
        print(f"Uploading to {new_repo}...")
        upload_folder(
            folder_path=temp_dir,
            repo_id=new_repo,
            repo_type=repo_type,
            commit_message=f"Copy of {original_repo}"
        )


def hf_copy(original_repo, new_repo):
    """
    Duplicates a repository under the authenticated user's name.
    """
    try:
        api = HfApi()
        username = api.whoami()["name"]
        
        # Handle original repo name
        if '/' in original_repo:
            original_full_name = original_repo
        else:
            original_full_name = f"{username}/{original_repo}"
            
        # Handle new repo name (always under current user)
        if '/' in new_repo:
            new_full_name = new_repo
        else:
            new_full_name = f"{username}/{new_repo}"
            
        print(f"Copying repository from {original_full_name} to {new_full_name}")
        
        # Try to copy as a model first
        try:
            _copy_repo_via_clone(api, original_full_name, new_full_name, "model")
            print(f"Successfully copied model: {original_full_name} -> {new_full_name}")
            return
        except Exception as model_error:
            print(f"Model copy failed: {model_error}", file=sys.stderr)
            
        # Try to copy as a dataset
        try:
            _copy_repo_via_clone(api, original_full_name, new_full_name, "dataset")
            print(f"Successfully copied dataset: {original_full_name} -> {new_full_name}")
            return
        except Exception as dataset_error:
            print(f"Dataset copy failed: {dataset_error}", file=sys.stderr)
            
        print(f"Error: Could not find repository {original_full_name} as either a model or dataset")
        print("Make sure the repository name is correct and you have permission to access it.")
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Please ensure you are logged in with 'huggingface-cli login'.", file=sys.stderr)


def hf_delete(repo_name):
    """
    Deletes a repository under the authenticated user's name.
    """
    try:
        api = HfApi()
        username = api.whoami()["name"]
        
        # Check if repo_name already includes username
        if '/' in repo_name:
            full_repo_name = repo_name
        else:
            full_repo_name = f"{username}/{repo_name}"
            
        print(f"Attempting to delete repository: {full_repo_name}")
        
        # Try to delete as a model first
        try:
            api.delete_repo(repo_id=full_repo_name, repo_type="model")
            print(f"Successfully deleted model: {full_repo_name}")
            return
        except Exception as model_error:
            pass
            
        # Try to delete as a dataset
        try:
            api.delete_repo(repo_id=full_repo_name, repo_type="dataset")
            print(f"Successfully deleted dataset: {full_repo_name}")
            return
        except Exception as dataset_error:
            pass
            
        print(f"Error: Could not find repository {full_repo_name} as either a model or dataset")
        print("Make sure the repository name is correct and you have permission to delete it.")
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Please ensure you are logged in with 'huggingface-cli login'.", file=sys.stderr)


def hf_ls():
    """
    Lists the space usage of each model and dataset under the authenticated
    Hugging Face user's name, sorted by size in descending order.
    """
    try:
        api = HfApi()
        username = api.whoami()["name"]

        print(f"Fetching repository information for user: {username}\n")

        # --- Process Models ---
        model_repos = api.list_models(author=username)
        model_data = []
        print("Analyzing model sizes...")
        for model in model_repos:
            try:
                model_info = api.model_info(repo_id=model.modelId, files_metadata=True)
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
                dataset_info = api.dataset_info(repo_id=dataset.id, files_metadata=True)
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
    
    # ls subcommand
    ls_parser = subparsers.add_parser('ls', help='List repositories and their sizes')
    
    # rm subcommand for delete
    rm_parser = subparsers.add_parser('rm', help='Delete a repository')
    rm_parser.add_argument('repo_name', help='Repository name to delete')
    
    # copy subcommand
    copy_parser = subparsers.add_parser('cp', help='Copy/duplicate a repository')
    copy_parser.add_argument('original_repo', help='Original repository name')
    copy_parser.add_argument('new_repo', help='New repository name')
    
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
        hf_delete(args.repo_name)
    elif args.subcommand == 'cp':
        hf_copy(args.original_repo, args.new_repo)