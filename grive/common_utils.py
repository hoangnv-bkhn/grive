from pkg_resources import resource_filename
# stores default file address
import os
import ntpath
import errno
from pydrive import settings

dir_path = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser("~")

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