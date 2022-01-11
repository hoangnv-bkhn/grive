from pkg_resources import resource_filename
# stores default file address
import os
import ntpath
import errno
import re
from pydrive import settings

import pwd

dir_path = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser("~")

try:
    config_file = os.path.join(dir_path, "config_dicts/config.json")
    client_secrets = os.path.join(dir_path, "credential.json")
    mime_dict = os.path.join(dir_path, "config_dicts/mime_dict.json")
    format_dict = os.path.join(dir_path, "config_dicts/formats.json")
    version_info_file = os.path.join(dir_path, "docs/version_info.txt")
    help_file = os.path.join(dir_path, "docs/readme.txt")
    config_folder = os.path.join(dir_path, "config_dicts")
# when launched as package
except settings.InvalidConfigError or OSError:
    config_file = resource_filename(__name__, "config_dicts/config.json")
    client_secrets = resource_filename(__name__, "credential.json")
    mime_dict = resource_filename(__name__, "config_dicts/mime_dict.json")
    format_dict = resource_filename(__name__, "config_dicts/formats.json")
    version_info_file = os.path.join(dir_path, "docs/version_info.txt")
    help_file = resource_filename(__name__, "docs/readme.txt")
    config_folder = resource_filename(__name__, "config_dicts")


# returns current username
def get_username():
    return pwd.getpwuid(os.getuid())[0]


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
        # return tail when file, otherwise other one for folder
        return tail or ntpath.basename(head)
    else:
        raise TypeError("Address not valid")


def dir_exists(addr):
    if not os.path.exists(addr):
        try:
            os.makedirs(addr)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise


def get_cloud_path(drive, instance_id, path=[]):
    """Get tree folder from cloud of this instance.

        :param drive: Google Drive instance
        :param instance_id: id of file or folder
        :param path: initial empty list

        :returns: path array contain tree folder from root
    """
    try:
        file = drive.CreateFile({'id': instance_id})
        if not file['parents'][0]['isRoot']:
            parent_folder = drive.CreateFile({'id': file['parents'][0]['id']})
            # print(parent_folder['title'])
            # path.append(parent_folder['title'])
            path.insert(0, parent_folder['title'])
            get_cloud_path(drive, parent_folder['id'], path)
        else:
            return path
    except:
        # print("%s is an invalid file_id!" % instance_id)
        return False


def get_local_path(drive, instance_id, sync_dir):
    """Get tree folder from cloud of this instance.

            :param drive: Google Drive instance
            :param instance_id: id of file or folder
            :param sync_dir: default sync directory

            :returns: corresponding canonical path of instance locally resp
    """
    rel_path = []
    get_cloud_path(drive, instance_id, rel_path)
    for p in rel_path:
        sync_dir = os.path.join(sync_dir, p)
    dir_exists(sync_dir)
    return sync_dir


def run_fast_scandir(dir):
    subfolders, files = [], []

    for f in os.scandir(dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            files.append(f.path)
            # if os.path.splitext(f.name)[1].lower() in ext:
            #     files.append(f.path)

    for dir in list(subfolders):
        sf, f = run_fast_scandir(dir)
        subfolders.extend(sf)
        files.extend(f)

    return subfolders, files


def check_option(option, char, length):
    """Check user's option contains wildcard for sub-function

        :param option: user's option
        :param char: wildcard for sub-function
        :param length: the length of 'option'

        :returns: True if option is valid and contains specified wildcard and vice versa
    """
    if len(option) == length and char in option:
        return True
    return False

def sizeof_fmt(num, suffix='B'):
        if num=="": return num
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return '{:.1f} {}{}'.format(num, unit, suffix)
            num /= 1024.0
        return '{:.1f} {}{}'.format(num, 'Yi', suffix)
    
def renderTypeShow(type):
    switcher= {
        'dammay': u'\u2601',
        'maytinh': u'\U0001F4BB',
        'dongbo':  u'\u2705',
        'notdongbo': u'\U0001F501'
    }
    return switcher.get(type,'error')

def isAudioFile(file): 
    if re.compile('audio', re.IGNORECASE).search(file['type']): 
        return True
    else: 
        return False

def isImageFile(file): 
    if re.compile('image', re.IGNORECASE).search(file['type']): 
        return True
    else: 
        return False

def isVideoFile(file): 
    if re.compile('video', re.IGNORECASE).search(file['type']): 
        return True
    else: 
        return False

def isDocument(file): 
    if re.compile('document', re.IGNORECASE).search(file['type']): 
        return True
    else: 
        return False

def getFileSize(file):
    if file['fileSize']=="": return ""
    size = file['fileSize']
    return int(size)
