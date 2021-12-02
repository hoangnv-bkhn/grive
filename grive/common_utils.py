from pkg_resources import resource_filename
# stores default file address
import os
import ntpath
import errno
from pydrive import settings

import pwd

dir_path = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser("~")

try:
    config_file = os.path.join(dir_path, "config_dicts/config.json")
# when launched as package
except settings.InvalidConfigError or OSError:
    config_file = resource_filename(__name__, "config_dicts/config.json")

# returns current username
def get_username():
    return pwd.getpwuid(os.getuid())[0]

try:
    client_secrets = os.path.join(dir_path, "credential.json")
except settings.InvalidConfigError or OSError:
    client_secrets = resource_filename(__name__, "credential.json")

def get_credential_file():
    # when launched as non-package
    try:
        return os.path.join(home, "credential.json")
    # when launched as package
    except settings.InvalidConfigError or OSError:
        return os.path.join(home, "credential.json")

# Extracts file name or folder name from full path
def get_file_name(addr):
    if os.path.exists(addr):
        head, tail = ntpath.split(addr)
        print(tail)
        print(ntpath.basename(head))
        return tail or ntpath.basename(head)  # return tail when file, otherwise other one for folder
    else:
        raise TypeError("Address not valid")

def dir_exists(addr):
    if not os.path.exists(addr):
        try:
            os.makedirs(addr)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise