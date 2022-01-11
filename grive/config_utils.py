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


def get_dir_sync_location():
    # Get address of sync folder
    config = read_config()
    addr = os.path.join(os.path.expanduser('~'), config['Sync_Dir'])
    # Making directory if it doesn't exist
    common_utils.dir_exists(addr)

    return addr


def get_sync_cycle():
    config = read_config()
    cycle = os.path.join(os.path.expanduser('~'), config['Sync_Cycle'])
    return cycle


def change_sync_dir(addr):
    """
    changes address of sync directory
    Args:
        addr: path of folder
    Returns:
        True if successful, False otherwise
    """
    if addr is None:
        print("Error: missing parameter")
        return False

    if os.path.isdir(addr):
        config['Sync_Dir'] = addr
        return True

    else:
        print(" Error: Not a directory! Please check the address of directory.")
        return False


def set_sync_cycle(value):
    """
    set value for remove post upload
    Args:
        value: True if file to be removed, false otherwise
    Returns:
        True if successful, False otherwise
    """
    if value is None:
        print("Error: missing parameter")
        return False

    try:
        value = int(value)
        if 0 < value <= 60:
            config['Sync_Cycle'] = value
            return True
        else:
            print(" Error: Wrong parameter to change !")
            return False
    except:
        print(" Error: Wrong parameter to change !")
        return False


def set_run_startup(value):
    """
    set value for share link
    Args:
        value: True if share link to be stored, false otherwise
    Returns:
        True if successful, False otherwise
    """
    if value is None:
        print("Error: missing parameter")
        return False

    if value.lower() == 'n':
        config['Auto_Start'] = False
        return True

    elif value.lower() == 'y':
        config['Auto_Start'] = True
        return True

    else:
        print(" Error: Wrong parameter to change !")
        return False


option = {
    1: change_sync_dir,
    2: set_sync_cycle,
    3: set_run_startup,
}


def write_config():
    """
    displays console for editing and manages input
    """
    global config

    config = read_config()

    print("\n\t\t\tGRIVE")
    print("\n Please look below at the options which you wish to update: ")
    print(" (Enter the number followed by value, eg. \"1 input\")")
    print("\t1. Change Sync Directory [full path to folder]")
    print("\t2. Set synchronous cycle [number]")
    print("\t3. Run at startup [Y/N]")
    print("\t4. List current settings [type \"4 ls\"]")
    print("\n Input \"0 exit\" at anytime to exit config edit")

    while True:
        user_input = str(input(' Choice: '))
        value = None  # define value to None to catch error
        opt = -1
        try:
            if len(user_input.split()) == 1:
                opt = int(user_input)
            elif len(user_input.split()) > 1:
                opt, value = list(map(str, user_input.split()))
        except ValueError:
            print("Error: Please adhere to the input format")
            continue

        # if input is not acceptable by int
        try:
            if int(opt) == 0:
                break

            elif int(opt) == 4:
                print("\t\t---Current Configuration---")
                print("\tSync directory: " + config['Sync_Dir'])
                print("\tSynchronous cycle: " + str(config['Sync_Cycle']))
                print("\tRun at startup: " + str(config['Auto_Start']))

            elif int(opt) not in list(range(1, 4)):
                print("Error: Wrong parameters entered")

            elif option[int(opt)](value):
                print("Success")

        except ValueError:
            print("Error: invalid input")
            continue

    try:
        with open(common_utils.config_file, "w") as output:
            json.dump(config, output)
    except IOError:
        print("Permission Denied: please run with sudo")