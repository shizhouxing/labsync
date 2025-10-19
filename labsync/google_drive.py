import sys
import logging
import argparse
import os
import json
import time
from multiprocessing import Pool
from .utils import user_data_dir
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from tqdm import tqdm
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


# silence error message "file_cache is only supported with oauth2client<4.0.0"
for name in logging.root.manager.loggerDict:
    if 'google' in name:
        logging.getLogger(name).setLevel(logging.WARNING)

credential_file = os.path.join(user_data_dir, 'google_drive_credential.txt')
client_config_file = os.path.join(user_data_dir, 'client_secrets.json')


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', action='store_true', help='Upload directory (will be archived)')
    parser.add_argument('-d', '--direct', action='store_true', help='Upload directory directly without archiving')
    parser.add_argument('-f', '--folder', type=str, default=None, help='Folder ID or folder name to upload to')
    parser.add_argument('-j', '--njobs', type=int, default=1, help='Number of parallel upload jobs (default: 1)')
    parser.add_argument('-c', '--continue', dest='continue_upload', action='store_true', help='Skip files that already exist in destination')
    parser.add_argument('--max-files', type=int, default=100, help='Maximum files in directory before auto-archiving (default: 100)')
    parser.add_argument('files', type=str, nargs='+', help='File path')
    return parser


def _count_files_in_directory(path):
    """Count total number of files in a directory recursively."""
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count


def _select_from_multiple_matches(matches, item_type, get_name, get_id, get_extra_info=None):
    """Helper to handle user selection when multiple matches are found."""
    if not matches:
        return None

    if len(matches) == 1:
        return get_id(matches[0])

    print(f'Warning: Multiple {item_type}s found:')
    for idx, item in enumerate(matches):
        extra = f', {get_extra_info(item)}' if get_extra_info else ''
        print(f'  [{idx}] {get_name(item)} (ID: {get_id(item)}{extra})')
    choice = input('Enter index to select, or press Enter to use first: ').strip()
    if choice.isdigit() and 0 <= int(choice) < len(matches):
        return get_id(matches[int(choice)])
    return get_id(matches[0])


def find_shared_drive_by_name(drive, drive_name):
    """Find shared drive by name and return its ID."""
    try:
        from googleapiclient.discovery import build
        service = build('drive', 'v3', credentials=drive.auth.credentials)
        results = service.drives().list(pageSize=100).execute()
        drives = results.get('drives', [])

        matches = [d for d in drives if drive_name.lower() in d['name'].lower()]

        if not matches:
            return None, None

        selected_id = _select_from_multiple_matches(
            matches,
            'shared drive',
            lambda d: d['name'],
            lambda d: d['id']
        )
        selected_name = next(d['name'] for d in matches if d['id'] == selected_id)
        return selected_id, selected_name
    except Exception as e:
        print(f'Error searching shared drives: {e}')
        return None, None


def find_folder_by_name(drive, folder_name):
    """Find folder in My Drive and shared drives by name and return its ID."""
    file_list = drive.ListFile({
        'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        'corpora': 'allDrives',
        'includeItemsFromAllDrives': True,
        'supportsAllDrives': True
    }).GetList()

    if not file_list:
        return None

    return _select_from_multiple_matches(
        file_list,
        'folder',
        lambda f: f['title'],
        lambda f: f['id'],
        lambda f: f'Location: {f.get("driveId", "My Drive")}'
    )


def file_exists_in_drive(drive, filename, parent_id=None, drive_id=None):
    """Check if a file with the given name already exists in the destination."""
    query = f"title='{filename}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    elif drive_id:
        query += f" and '{drive_id}' in parents"

    file_list = drive.ListFile({
        'q': query,
        'corpora': 'allDrives',
        'includeItemsFromAllDrives': True,
        'supportsAllDrives': True
    }).GetList()
    return len(file_list) > 0


def create_folder(drive, folder_name, parent_id=None, drive_id=None):
    """Create a folder in Google Drive and return its ID."""
    metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'supportsAllDrives': True
    }
    if drive_id:
        metadata['parents'] = [{'kind': 'drive#driveId', 'id': drive_id}]
        metadata['driveId'] = drive_id
    elif parent_id:
        metadata['parents'] = [{'id': parent_id}]

    folder = drive.CreateFile(metadata)
    folder.Upload(param={'supportsAllDrives': True})
    return folder['id']


class ProgressFileWrapper:
    """Wrapper for file object that reports progress."""
    def __init__(self, file_path, pbar):
        self.file_path = file_path
        self.pbar = pbar
        self.file = open(file_path, 'rb')

    def read(self, size=-1):
        data = self.file.read(size)
        self.pbar.update(len(data))
        return data

    def seek(self, offset, whence=0):
        return self.file.seek(offset, whence)

    def tell(self):
        return self.file.tell()

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def upload_file_with_progress(drive_file, file_path):
    """Upload a file with progress bar using chunked resumable upload."""
    from pydrive2.files import ApiRequestError
    from googleapiclient import errors

    file_size = os.path.getsize(file_path)
    chunk_size = 256 * 1024 * 1024

    if drive_file.get('mimeType') is None:
        drive_file['mimeType'] = 'application/octet-stream'

    with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(file_path)) as pbar:
        retries = 0
        max_retries = 5

        while retries < max_retries:
            try:
                media_body = MediaFileUpload(
                    file_path,
                    mimetype=drive_file['mimeType'],
                    resumable=True,
                    chunksize=chunk_size
                )

                param = {'supportsAllDrives': True}
                param['body'] = drive_file.GetChanges()

                if drive_file.uploaded or drive_file.get('id') is not None:
                    request = drive_file.auth.service.files().update(
                        fileId=drive_file['id'],
                        media_body=media_body,
                        **param
                    )
                else:
                    request = drive_file.auth.service.files().insert(
                        media_body=media_body,
                        **param
                    )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        pbar.n = int(status.progress() * file_size)
                        pbar.refresh()

                drive_file.uploaded = True
                drive_file.UpdateMetadata(response)
                pbar.n = file_size
                pbar.refresh()
                break

            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    retries += 1
                    if retries < max_retries:
                        wait_time = 2 ** retries
                        pbar.write(f'Upload error (attempt {retries}/{max_retries}), retrying in {wait_time}s...')
                        time.sleep(wait_time)
                        pbar.n = 0
                        pbar.refresh()
                    else:
                        raise ApiRequestError(e)
                else:
                    raise ApiRequestError(e)
            except errors.HttpError as e:
                retries += 1
                if retries < max_retries:
                    wait_time = 2 ** retries
                    pbar.write(f'Connection error (attempt {retries}/{max_retries}), retrying in {wait_time}s...')
                    time.sleep(wait_time)
                    pbar.n = 0
                    pbar.refresh()
                else:
                    raise ApiRequestError(e)
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    wait_time = 2 ** retries
                    pbar.write(f'Connection error (attempt {retries}/{max_retries}), retrying in {wait_time}s...')
                    time.sleep(wait_time)
                    pbar.n = 0
                    pbar.refresh()
                else:
                    raise


def upload_directory_direct(drive, local_path, parent_id=None, drive_id=None, continue_upload=False):
    """Recursively upload a directory and its contents to Google Drive."""
    dir_name = os.path.basename(local_path)

    if continue_upload and file_exists_in_drive(drive, dir_name, parent_id, drive_id):
        query = f"title='{dir_name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        elif drive_id:
            query += f" and '{drive_id}' in parents"
        file_list = drive.ListFile({
            'q': query,
            'corpora': 'allDrives',
            'includeItemsFromAllDrives': True,
            'supportsAllDrives': True
        }).GetList()
        folder_id = file_list[0]['id']

        items_to_upload = []
        for item in os.listdir(local_path):
            if not file_exists_in_drive(drive, item, folder_id, None):
                items_to_upload.append(item)

        if not items_to_upload:
            print(f'Skipping folder {dir_name} (all files already exist)')
            return folder_id

        print(f'Folder exists: {dir_name}, uploading {len(items_to_upload)} remaining files...')
    else:
        print(f'Creating folder: {dir_name}')
        folder_id = create_folder(drive, dir_name, parent_id, drive_id)

    items = os.listdir(local_path)
    items_with_sizes = []
    for item in items:
        item_path = os.path.join(local_path, item)
        if os.path.isfile(item_path):
            items_with_sizes.append((item, os.path.getsize(item_path)))
        else:
            items_with_sizes.append((item, 0))

    sorted_items = [item for item, size in sorted(items_with_sizes, key=lambda x: x[1], reverse=True)]

    for item in sorted_items:
        item_path = os.path.join(local_path, item)

        if os.path.isdir(item_path):
            upload_directory_direct(drive, item_path, folder_id, None, continue_upload)
        else:
            if continue_upload and file_exists_in_drive(drive, item, folder_id, None):
                print(f'Skipping {item} (already exists)')
                continue
            file = drive.CreateFile({
                'title': item,
                'parents': [{'id': folder_id}],
                'supportsAllDrives': True
            })
            upload_file_with_progress(file, item_path)

    return folder_id


def upload_single_file(drive, file, use_archive, use_direct, folder_id, drive_id, continue_upload=False, max_files=100):
    """Upload a single file or directory to Google Drive."""
    if file.endswith('/'):
        file = file[:-1]

    if not os.path.exists(file):
        return f'Error: File {file} does not exist'

    isdir = os.path.isdir(file)
    if isdir:
        if use_direct:
            file_count = _count_files_in_directory(file)
            if file_count > max_files:
                print(f'Directory {file} has {file_count} files (exceeds limit of {max_files}), switching to archive mode')
                use_archive = True
                use_direct = False
            else:
                upload_directory_direct(drive, file, folder_id, drive_id, continue_upload)
                if drive_id:
                    return f'Successfully uploaded directory {file} to shared drive'
                elif folder_id:
                    return f'Successfully uploaded directory {file} to Google Drive folder'
                else:
                    return f'Successfully uploaded directory {file} to Google Drive (My Drive)'

        if not use_direct and not use_archive:
            return f'Skipping directory {file}'

        if use_archive:
            file_z = os.path.abspath(f'{os.path.basename(file)}.tgz')
            os.system(f'cd {file} && tar -czvf {file_z} *')
            path = file_z
    else:
        path = file

    if continue_upload and file_exists_in_drive(drive, os.path.basename(path), folder_id, drive_id):
        if isdir:
            os.system(f'rm {path}')
        return f'Skipping {path} (already exists)'

    metadata = {
        'title': os.path.basename(path),
        'supportsAllDrives': True
    }
    if drive_id:
        metadata['parents'] = [{'kind': 'drive#driveId', 'id': drive_id}]
        metadata['driveId'] = drive_id
    elif folder_id:
        metadata['parents'] = [{'id': folder_id}]

    file_obj = drive.CreateFile(metadata)
    upload_file_with_progress(file_obj, path)

    if drive_id:
        result = f'Successfully uploaded {path} to shared drive'
    elif folder_id:
        result = f'Successfully uploaded {path} to Google Drive folder'
    else:
        result = f'Successfully uploaded {path} to Google Drive (My Drive)'

    if isdir or path.startswith('/tmp/'):
        assert path.endswith('.tgz')
        os.system(f'rm {path}')

    return result


def upload_worker(args_tuple):
    """Worker function for multiprocessing upload."""
    file, use_archive, use_direct, folder_id, drive_id, continue_upload, max_files = args_tuple

    import webbrowser
    webbrowser.get = lambda using=None: None
    webbrowser.open = lambda url, new=0, autoraise=True: None

    gauth = GoogleAuth()
    gauth.settings['client_config_backend'] = 'file'
    gauth.LoadClientConfigFile(client_config_file)
    gauth.LoadCredentialsFile(credential_file)

    if gauth.access_token_expired:
        try:
            gauth.Refresh()
        except:
            pass

    gauth.Authorize()
    drive = GoogleDrive(gauth)

    try:
        return upload_single_file(drive, file, use_archive, use_direct, folder_id, drive_id, continue_upload, max_files)
    except Exception as e:
        return f'Error uploading {file}: {str(e)}'


def authenticate():
    print('Checking Google Drive authentication...')

    import webbrowser
    webbrowser.get = lambda using=None: None
    webbrowser.open = lambda url, new=0, autoraise=True: None

    gauth = GoogleAuth()
    gauth.settings['client_config_backend'] = 'file'

    if not os.path.exists(client_config_file):
        print(f'Client config file {client_config_file} does not exist')
        print('Please get a new one from Google Cloud Console ',
              '(https://console.cloud.google.com/)')
        print('Project -> APIs and services -> Credentials')
        config = input('Copy and paste the configuration: ')
        try:
            config_json = json.loads(config)
            assert 'installed' in config_json
            installed = config_json['installed']
            for key in ['client_id', 'project_id', 'auth_uri', 'token_uri',
                        'auth_provider_x509_cert_url', 'client_secret',
                        'redirect_uris']:
                assert key in installed
        except: # pylint: disable=bare-except
            print('Invalid. Please check it again.')
            exit(0)
        print('Verified')
        with open(client_config_file, 'w') as file:
            file.write(config)
        print(f'Saved client config file to {client_config_file}')

    gauth.LoadClientConfigFile(client_config_file)
    gauth.LoadCredentialsFile(credential_file)

    if gauth.credentials is None:
        print('No credentials found. Starting authentication...')
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        print('Access token expired. Refreshing...')
        try:
            gauth.Refresh()
            print('Token refreshed successfully')
        except:
            print('Failed to refresh token. Re-authenticating...')
            import traceback; traceback.print_exc()
            gauth = GoogleAuth()
            gauth.LoadClientConfigFile(client_config_file)
            gauth.LocalWebserverAuth()
    else:
        from datetime import datetime, timedelta
        if gauth.credentials.token_expiry:
            time_until_expiry = gauth.credentials.token_expiry - datetime.now()
            if time_until_expiry < timedelta(minutes=5):
                print('Access token expiring soon. Refreshing...')
                try:
                    gauth.Refresh()
                    print('Token refreshed successfully')
                except:
                    print('Using existing credentials')
                    gauth.Authorize()
            else:
                print('Using existing credentials')
                gauth.Authorize()
        else:
            print('Using existing credentials')
            gauth.Authorize()

    gauth.SaveCredentialsFile(credential_file)
    print('Authentication complete')
    return gauth


def _get_file_size(file_path):
    """Get file size in bytes. For directories, return total size of all files."""
    if os.path.isdir(file_path):
        total_size = 0
        for root, dirs, files in os.walk(file_path):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    elif os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0


def google_drive():
    """Currently only simple uploading is supported"""
    args = get_parser().parse_args(sys.argv[2:])

    print('Authenticating with Google Drive...')
    gauth = authenticate()
    drive = GoogleDrive(gauth)
    print('Authentication successful')

    folder_id = None
    drive_id = None
    if args.folder:
        if '/' in args.folder or len(args.folder) > 50:
            folder_id = args.folder
            print(f'Using folder ID: {folder_id}')
        else:
            print(f'Searching for shared drive or folder: {args.folder}')
            drive_id, drive_name = find_shared_drive_by_name(drive, args.folder)
            if drive_id:
                print(f'Found shared drive "{drive_name}" (ID: {drive_id})')
            else:
                folder_id = find_folder_by_name(drive, args.folder)
                if folder_id:
                    print(f'Found folder ID: {folder_id}')
                else:
                    print(f'Error: Shared drive or folder "{args.folder}" not found')
                    return

    print(f'Using {args.njobs} parallel jobs for upload')

    gauth.SaveCredentialsFile(credential_file)

    sorted_files = sorted(args.files, key=_get_file_size, reverse=True)

    upload_tasks = [
        (file, args.r, args.direct, folder_id, drive_id, args.continue_upload, args.max_files)
        for file in sorted_files
    ]
    with Pool(processes=args.njobs) as pool:
        results = pool.map(upload_worker, upload_tasks)

    for result in results:
        print(result)
    return
