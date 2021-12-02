from builtins import input, str, map, range

import json
import os
import sys

##huy
try:
    # set directory for relative import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
except ImportError:
    from . import common_utils

config = {}

def read_config():
    """
    reads the configuration
    Args:
        None
    Returns:
        temp: dictionary having configuration data
    """
    with open(common_utils.config_file, 'r') as f_input:
        temp = json.load(f_input)

    return temp

def down_addr():
    # Making file address for upload and downloads
    config = read_config()
    addr = os.path.join(os.path.expanduser('~'), config['Down_Dir'])
    # making directory if it doesn't exist
    common_utils.dir_exists(addr)
    return addr
