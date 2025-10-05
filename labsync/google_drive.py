import sys
import logging
import argparse
import os
import json
from .utils import user_data_dir
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# silence error message "file_cache is only supported with oauth2client<4.0.0"
for name in logging.root.manager.loggerDict:
    if 'google' in name:
        logging.getLogger(name).setLevel(logging.WARNING)

credential_file = os.path.join(user_data_dir, 'google_drive_credential.txt')
client_config_file = os.path.join(user_data_dir, 'client_secrets.json')


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', action='store_true', help='Upload directory (will be archived)')
    parser.add_argument('--folder', type=str, default=None, help='Folder ID or folder name to upload to')
    parser.add_argument('files', type=str, nargs='+', help='File path')
    return parser


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

        if len(matches) > 1:
            print(f'Warning: Multiple shared drives found matching "{drive_name}":')
            for idx, d in enumerate(matches):
                print(f'  [{idx}] {d["name"]} (ID: {d["id"]})')
            choice = input('Enter index to select, or press Enter to use first: ').strip()
            if choice.isdigit() and 0 <= int(choice) < len(matches):
                selected = matches[int(choice)]
                return selected['id'], selected['name']
            return matches[0]['id'], matches[0]['name']

        return matches[0]['id'], matches[0]['name']
    except Exception as e:
        print(f'Error searching shared drives: {e}')
        return None, None


def find_folder_by_name(drive, folder_name):
    """Find folder in My Drive and shared drives by name and return its ID."""
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    params = {
        'q': query,
        'corpora': 'allDrives',
        'includeItemsFromAllDrives': True,
        'supportsAllDrives': True
    }
    file_list = drive.ListFile(params).GetList()

    if not file_list:
        return None

    if len(file_list) > 1:
        print(f'Warning: Multiple folders found with name "{folder_name}":')
        for idx, f in enumerate(file_list):
            location = f.get('driveId', 'My Drive')
            print(f'  [{idx}] {f["title"]} (ID: {f["id"]}, Location: {location})')
        choice = input('Enter index to select, or press Enter to use first: ').strip()
        if choice.isdigit() and 0 <= int(choice) < len(file_list):
            return file_list[int(choice)]['id']
        return file_list[0]['id']

    return file_list[0]['id']


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
        except: # pylint: disable=bare-except
            print('Failed to refresh token. Re-authenticating...')
            import traceback; traceback.print_exc()
            gauth = GoogleAuth()
            gauth.LoadClientConfigFile(client_config_file)
            gauth.LocalWebserverAuth()
    else:
        print('Using existing credentials')
        gauth.Authorize()

    gauth.SaveCredentialsFile(credential_file)
    print('Authentication complete')
    return gauth


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

    for file in args.files:
        if file.endswith('/'):
            file = file[:-1]

        if not os.path.exists(file):
            print(f'Error: File {file} does not exist')
            continue

        isdir = os.path.isdir(file)
        if isdir:
            if not args.r:
                print(f'Skipping directory {file}')
                continue
            print(f'Archiving directory {file}...')
            file_z = os.path.abspath(f'{os.path.basename(file)}.tgz')
            os.system(f'cd {file} && tar -czvf {file_z} *')
            path = file_z
            print(f'Archive created: {path}')
        else:
            path = file
            file_size = os.path.getsize(path)
            print(f'Uploading file: {path} ({file_size} bytes)...')

        metadata = {
            'title': os.path.basename(path),
            'supportsAllDrives': True
        }
        if drive_id:
            metadata['parents'] = [{'kind': 'drive#driveId', 'id': drive_id}]
            metadata['driveId'] = drive_id
        elif folder_id:
            metadata['parents'] = [{'id': folder_id}]

        file = drive.CreateFile(metadata)
        file.SetContentFile(path)
        file.Upload(param={'supportsAllDrives': True})

        if drive_id:
            print(f'Successfully uploaded {path} to shared drive')
        elif folder_id:
            print(f'Successfully uploaded {path} to Google Drive folder')
        else:
            print(f'Successfully uploaded {path} to Google Drive (My Drive)')

        if isdir or path.startswith('/tmp/'):
            assert path.endswith('.tgz')
            print(f'Cleaning up temporary file: {path}')
            os.system(f'rm {path}')
