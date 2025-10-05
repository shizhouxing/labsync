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
    parser.add_argument('-r', action='store_true')
    parser.add_argument('files', type=str, nargs='+', help='File path')
    return parser


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

        file = drive.CreateFile({'title': os.path.basename(path)})
        file.SetContentFile(path)
        file.Upload()
        print(f'Successfully uploaded {path} to Google Drive')

        if isdir or path.startswith('/tmp/'):
            assert path.endswith('.tgz')
            print(f'Cleaning up temporary file: {path}')
            os.system(f'rm {path}')
