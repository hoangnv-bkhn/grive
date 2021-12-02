from builtins import str
import json
import os
import sys
import shutil
import pyperclip
from pydrive import files


##huy
try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config_utils
except ImportError:
    from . import config_utils

# list all files and folders in the downloads directory
def f_list_local():
    for f in os.listdir(config_utils.down_addr()):
        print(f)

# Operations for file list commands
def f_list(drive, keyword, recursive):

    # get recursively all files in the folder
    if recursive:
        print("recursive")
    # lists all files and folder inside given folder
    else:
        if keyword == "all":
            file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
            for f in file_list:
                print('title: %s, id: %s' % (f['title'], f['id']))

        # # lists all files and folders inside trash
        # elif keyword == "trash":
        #     file_list = drive.ListFile({'q': "'root' in parents and trashed=true"}).GetList()
        #     for f in file_list:
        #         print('title: %s, id: %s' % (f['title'], f['id']))

        # # lists all files and folders inside folder given as argument in keyword
        # else:
        #     q_string = "'%s' in parents and trashed=false" % keyword
        #     file_list = drive.ListFile({'q': q_string}).GetList()
        #     for f in file_list:
        #         print('title: %s, id: %s' % (f['title'], f['id']))
