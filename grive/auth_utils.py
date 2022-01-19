import json
import sys
import os
from pydrive.auth import GoogleAuth

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
except ImportError:
    from . import common_utils


def drive_auth(reset):
    g_auth = GoogleAuth()

    g_auth.DEFAULT_SETTINGS['client_config_file'] = common_utils.client_secrets
    g_auth.DEFAULT_SETTINGS['client_config_backend'] = 'file'
    g_auth.DEFAULT_SETTINGS['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
    g_auth.DEFAULT_SETTINGS['get_refresh_token'] = True
    g_auth.DEFAULT_SETTINGS['save_credentials'] = True
    g_auth.DEFAULT_SETTINGS['save_credentials_backend'] = 'file'
    g_auth.DEFAULT_SETTINGS['save_credentials_file'] = common_utils.get_credential_file()
    g_auth.DEFAULT_SETTINGS['client_id'] = os.environ.get("CLIENT_ID")
    g_auth.DEFAULT_SETTINGS['client_secret'] = os.environ.get("CLIENT_SECRET")

    # Already authenticated
    g_auth.LoadCredentialsFile(common_utils.get_credential_file())

    if g_auth.credentials is None or reset:
        if reset:
            if g_auth.credentials is not None:
                print("Error: Couldn't reset account. Please report at tokyo.example@mail.com")
                sys.exit(1)
        g_auth.LocalWebserverAuth()

    elif g_auth.access_token_expired:
        # refresh authorisation if expired
        try:
            g_auth.Refresh()
        except:
            print("Please reconnect your account with -re option !")

    else:
        # initialise the saved data
        g_auth.Authorize()

    if os.path.exists(common_utils.get_credential_file()) and os.path.isfile(common_utils.get_credential_file()):
        token_file = {}
        with open(common_utils.get_credential_file()) as json_file:
            data = json.load(json_file)
            token_file['token'] = data['access_token']
            token_file['refresh_token'] = data['refresh_token']
            token_file['token_uri'] = data['token_uri']
            token_file['client_id'] = data['client_id']
            token_file['client_secret'] = data['client_secret']
            token_file['scopes'] = data['scopes']
            token_file['expiry'] = data['token_expiry']
            json_file.close()
        with open(common_utils.get_access_token(), 'w') as f:
            json.dump(token_file, f)

    creds = get_user_credential()

    return g_auth, creds


def reset_account():
    if os.path.isfile(common_utils.get_credential_file()):
        os.remove(common_utils.get_credential_file())
    if os.path.isfile(common_utils.get_access_token()):
        os.remove(common_utils.get_access_token())

    drive_auth(True)


def get_user_credential():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(common_utils.get_access_token()):
        creds = Credentials.from_authorized_user_file(common_utils.get_access_token(), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                common_utils.client_secrets, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(common_utils.get_access_token(), 'w') as token:
            token.write(creds.to_json())

    return creds


if __name__ == '__main__':
    pass
