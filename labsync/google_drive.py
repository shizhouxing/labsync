import sys
import logging
import argparse
import os
import json
import logging
from .utils import user_data_dir
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# silence error message "file_cache is only supported with oauth2client<4.0.0"
for name in logging.root.manager.loggerDict:
    if 'google' in name:
        logging.getLogger(name).setLevel(logging.WARNING)

credential_file = os.path.join(user_data_dir, 'google_drive_credential.txt')
client_config_file = os.path.join(user_data_dir, 'client_secrets.json')

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='File path')
    return parser

def authenticate():
    gauth = GoogleAuth()
    if not os.path.exists(client_config_file):
        print(f'Client config file {client_config_file} does not exist')
        print('Please get a new one from Google Cloud Console (https://console.cloud.google.com/)')
        print('Project -> APIs and services -> Credentials')
        config = input('Copy and paste the configuration: ')
        try:
            config_json = json.loads(config)
            assert 'installed' in config_json
            installed = config_json['installed']
            for key in ['client_id', 'project_id', 'auth_uri', 'token_uri',
                        'auth_provider_x509_cert_url', 'client_secret', 'redirect_uris']:
                assert key in installed
        except:
            print('Invalid. Please check it again.')
            exit(0)
        print('Verified')
        with open(client_config_file, 'w') as file:
            file.write(config)
        print(f'Saved client config file to {client_config_file}')
    gauth.LoadClientConfigFile(client_config_file)      
    gauth.LoadCredentialsFile(credential_file)
    if gauth.credentials is None:
        print('Authenticating...')
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile(credential_file)
    return gauth

"""Currently only simple uploading is supported"""
def google_drive():
    args = get_parser().parse_args(sys.argv[2:])

    gauth = authenticate()
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({'title': os.path.basename(args.file)})
    file.SetContentFile(args.file)
    file.Upload()

    print(f'File {args.file} uploaded to Google Drive')