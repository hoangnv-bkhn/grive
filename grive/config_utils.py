from builtins import input, str, map, range

import json
import os
import sys

try:
    # set directory for relative import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
except ImportError:
    from . import common_utils

config = {}

# Import config file
def read_config():
    with open(common_utils.config_file, 'r') as f_input:
        temp = json.load(f_input)
    return temp

def down_addr():
    # Get address of upload and downloads folders
    config = read_config()
    addr = os.path.join(os.path.expanduser('~'), config['Sync_Dir'])
    # Making directory if it doesn't exist
    common_utils.dir_exists(addr)
    return addr
