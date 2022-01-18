from datetime import datetime
import time

from pkg_resources import resource_filename
# stores default file address
import os
import ntpath
import errno
import re
from pydrive import settings
from prettytable import PrettyTable

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
        dir_exists(os.path.join(home, ".grive"))
        return os.path.join(home, ".grive/grive_credential.json")
    # when launched as package
    except settings.InvalidConfigError or OSError:
        return os.path.join(home, ".grive/grive_credential.json")


def get_access_token():
    # when launched as non-package
    try:
        dir_exists(os.path.join(home, ".grive"))
        return os.path.join(home, ".grive/token.json")
    # when launched as package
    except settings.InvalidConfigError or OSError:
        return os.path.join(home, ".grive/token.json")


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
            elem = {}
            parent_folder = drive.CreateFile({'id': file['parents'][0]['id']})
            elem['name'] = parent_folder['title']
            elem['id'] = parent_folder['id']
            # print(parent_folder['title'])
            # path.append(parent_folder['title'])
            path.insert(0, elem)
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

            :returns: corresponding canonical path of instance locally
    """
    rel_path = []
    get_cloud_path(drive, instance_id, rel_path)
    check = False
    for p in rel_path:
        for file in os.listdir(sync_dir):
            # print(file)
            try:
                if os.getxattr(os.path.join(sync_dir, file), 'user.id').decode() == p['id']:
                    # print(123)
                    check = True
                    sync_dir = os.path.join(sync_dir, file)
                    # print(sync_dir)
            except:
                continue
        if not check:
            # print(456)
            if os.path.exists(os.path.join(sync_dir, p['name'])):
                sync_dir = get_dup_name(sync_dir, p['name'])
            else:
                sync_dir = os.path.join(sync_dir, p['name'])
            dir_exists(sync_dir)
            os.setxattr(sync_dir, 'user.id', str.encode(p['id']))

    # dir_exists(sync_dir)
    # print(sync_dir)
    return sync_dir


def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


def run_fast_scandir(folder):
    sub_folders, files = [], []

    for f in os.scandir(folder):
        if f.is_dir():
            sub_folders.append(f.path)
        if f.is_file():
            files.append(f.path)
            # if os.path.splitext(f.name)[1].lower() in ext:
            #     files.append(f.path)

    for folder in list(sub_folders):
        sf, f = run_fast_scandir(folder)
        sub_folders.extend(sf)
        files.extend(f)

    return sub_folders, files


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
    if num == "" or num == None:
        return num
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return '{:.1f} {}{}'.format(num, unit, suffix)
        num /= 1024.0
    return '{:.1f} {}{}'.format(num, 'Yi', suffix)


def renderTypeShow(type):
    switcher = {
        'dammay': u'\u2601',
        'maytinh': u'\U0001F5B3',
        'dongbo': u'\u2714',
        'notdongbo': u'\u27F3'
    }
    return switcher.get(type, 'error')


def isAudioFile(file):
    if re.compile('audio', re.IGNORECASE).search(file['mimeType']):
        return True
    else:
        return False


def isImageFile(file):
    if re.compile('image', re.IGNORECASE).search(file['mimeType']):
        return True
    else:
        return False


def isVideoFile(file):
    if re.compile('video', re.IGNORECASE).search(file['mimeType']):
        return True
    else:
        return False


def isDocument(file):
    if re.compile('document', re.IGNORECASE).search(file['mimeType']):
        return True
    else:
        return False


def getFileSize(file):
    if file.get("fileSize"): 
        size = file['fileSize']
        return int(size)
    else: 
        return ""

def is_parents_folder(id_parents, parents): 
    for elem in parents:
        if elem['id'] == id_parents:
            return True
    
    return False

def print_table_remote(arr_files):
    table = PrettyTable()
    table.field_names = ['Name', 'Id', 'Status', 'Date Modified', 'Type' , 'Size']
    if len(arr_files) > 0:
        for file in arr_files: 
            table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], renderTypeShow(file['typeShow']),
                                                                utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], sizeof_fmt(int(file['fileSize'])) if file['fileSize'] else "" ])
        print(table)
        


def get_dup_name(folder, name):
    if os.path.exists(os.path.join(folder, name)):
        tokens = name.split('_')
        try:
            no_copy = int(tokens[0])
            ver = no_copy + 1
            _name = ""
            for i in range(1, len(tokens)):
                _name += tokens[i]
            name = _name
            res = os.path.join(folder, str(ver) + "_" + name)
            if os.path.exists(res):
                return get_dup_name(folder, str(ver) + "_" + name)
            else:
                return res
        except:
            result = os.path.join(folder, "1_" + name)
            if os.path.exists(result):
                return get_dup_name(folder, "1_" + name)
            else:
                return result
    else:
        return os.path.join(folder, name)

def get_list_local_id(folder):
    ids = []
    if os.path.exists(folder):
        for file in os.listdir(folder):
            try:
                instance_id = os.getxattr(os.path.join(folder, file), 'user.id')
                ids.append(instance_id.decode())
            except:
                continue
    return ids

def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset
