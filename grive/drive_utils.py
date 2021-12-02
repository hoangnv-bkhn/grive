from builtins import str
import json
import os
import sys
import shutil
import pyperclip
from pydrive import files

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
except ImportError:
    from . import common_utils
    from . import config_utils

def f_create(drive, addr, fold_id, rel_addr, show_update):
    # check whether address is right or not
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, check the address!")
        return

    # creating if it's a folder
    if os.path.isdir(addr):
        # print progress
        if show_update:
            print("creating folder " + rel_addr)
        # if folder to be added to root
        if fold_id is None:
            folder = drive.CreateFile()
        # if folder to be added to some other folder
        else:
            folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

        # folder['title'] = common_utils.get_f_name(addr)  # sets folder title
        folder['title'] = rel_addr  # sets folder title --Test
        folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
        folder.Upload()

        # traversing inside files/folders
        for item in os.listdir(addr):
            f_create(drive, os.path.join(addr, item), folder['id'], rel_addr + "/" +
                     str(common_utils.get_f_name(os.path.join(addr, item))), show_update)

    # creating file
    else:
        # print progress
        if show_update:
            print("uploading file " + rel_addr)
        # if file is to be added to root
        if fold_id is None:
            up_file = drive.CreateFile()
        # if file to be added to some folder in drive
        else:
            up_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

        up_file.SetContentFile(addr)
        # up_file['title'] = common_utils.get_f_name(addr)  # sets file title to original
        up_file['title'] = rel_addr  # sets file title to original
        up_file.Upload()

    return True

def share_link(drive, permission, file_id, to_print):
    if is_valid_id(drive, file_id):
        # create shared file
        share_file = drive.CreateFile({'id': file_id})
        # check file's permission
        if permission == "-r":
            role = "reader"
        elif permission == "-w":
            role = "writer"
        else:
            print("Permission is not a valid. Try again")
            return

        share_file.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': role
        })

        share_file.FetchMetadata(fields='alternateLink, title')

        if to_print:
            print("Share link copied to clipboard!")
            pyperclip.copy(share_file['alternateLink'])
            mess = pyperclip.paste()
            print(mess)


def is_valid_id(drive, file_id):
    try:
        r_file = drive.CreateFile({'id': file_id})
    except files.ApiRequestError:
        print("%s is an invalid file_id!" % file_id)
        return False
    return True

# List all files and folders in the downloads directory
def f_list_local():
    for f in os.listdir(config_utils.down_addr()):
        print(f)

# Operations for file list commands
def f_list(drive, keyword, recursive):
    if keyword == "all":
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        for f in file_list:
            print('title: %s, id: %s' % (f['title'], f['id']))

    # lists all files and folders inside folder given as argument in keyword
    else:
        q_string = "'%s' in parents and trashed=false" % keyword
        file_list = drive.ListFile({'q': q_string}).GetList()
        for f in file_list:
            print('title: %s, id: %s' % (f['title'], f['id']))
