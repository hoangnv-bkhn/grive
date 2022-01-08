from pydrive.auth import GoogleAuth
from dotenv import load_dotenv
load_dotenv()
import sys
import os

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

    return g_auth

def reset_account():
    if os.path.isfile(common_utils.get_credential_file()):
        os.remove(common_utils.get_credential_file())

    drive_auth(True)

if __name__ == '__main__':
    pass