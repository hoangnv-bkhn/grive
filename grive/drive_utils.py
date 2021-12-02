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
    import file_add
    import edit_config
except ImportError:
    from . import common_utils
    from . import config_utils

def share_link(drive, file_id, permission, to_print):
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
            pyperclip.paste()


def is_valid_id(drive, file_id):
    try:
        r_file = drive.CreateFile({'id': file_id})
    except files.ApiRequestError:
        print("%s is an invalid file_id!" % file_id)
        return False
    return True
