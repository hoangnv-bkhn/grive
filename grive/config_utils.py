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


def get_folder_sync_path():
    # Get address of sync folder
    config_file = read_config()
    sync_folder_path = os.path.join(os.path.expanduser('~'), config_file['Sync_Folder'])
    # Making folder if it doesn't exist
    common_utils.dir_exists(sync_folder_path)

    return sync_folder_path


def get_sync_cycle():
    config_file = read_config()
    cycle = config_file['Sync_Cycle']
    return cycle


def get_network_limitation(mode):
    config_file = read_config()
    if mode == "download":
        download_rate = config_file['Network_Speed_Limitation']['Download_Rate']
        return download_rate
    elif mode == "upload":
        upload_rate = config_file['Network_Speed_Limitation']['Upload_Rate']
        return upload_rate
    else:
        return None


def change_sync_dir(path):
    """
    changes address of sync folder
    Args:
        path: path of folder
    Returns:
        True if successful, False otherwise
    """
    if path is None:
        print("Error: missing parameter")
        return False

    if os.path.isdir(path):
        config['Sync_Dir'] = path
        return True

    else:
        print(" Error: Not a directory! Please check the address of directory.")
        return False


def set_sync_cycle(value):
    """
    set synchronous cycle
    Args:
        value: Synchronization period in minutes
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


def set_network_limitation(value):
    if value is None or len(value) < 2:
        print("Error: missing parameter")
        return False
    if len(value) == 2:
        try:
            rate = int(value[1])
            if value[0].lower() == 'upload' and 0 < rate < 5120:
                config['Network_Speed_Limitation']['Upload_Rate'] = rate
                return True
            elif value[0].lower() == 'download' and 0 < rate < 5120:
                config['Network_Speed_Limitation']['Download_Rate'] = rate
                return True
            else:
                print(" Error: Wrong parameter to change !")
                return False
        except:
            if value[0].lower() == 'upload' and value[1].lower() == 'n':
                config['Network_Speed_Limitation']['Upload_Rate'] = False
                return True
            elif value[0].lower() == 'download' and value[1].lower() == 'n':
                config['Network_Speed_Limitation']['Download_Rate'] = False
                return True
            else:
                print(" Error: Wrong parameter to change !")
                return False
    else:
        print(" Error: Wrong parameter to change !")
        return False


def set_run_startup(value):
    """
    set whether program run on startup
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
    3: set_network_limitation,
    4: set_run_startup,
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
    print("\t1. Change Sync Directory [Full path to folder]")
    print("\t2. Set synchronous cycle [Number]")
    print("\t3. Set network limitation [Mode Number/ Mode N]")
    print("\t4. Run at startup [Y/N]")
    print("\t5. List current settings [type \"5\"]")
    print("\n Input \"0\" at anytime to exit config edit")

    while True:
        user_input = str(input(' Choice: '))
        value = None  # define value to None to catch error
        opt = -1
        # print(user_input)
        try:
            elems = user_input.split()
            if len(elems) == 1:
                opt = int(user_input)
            elif len(elems) > 1:
                if len(elems) > 2:
                    opt = elems[0]
                    value = elems[1:]
                else:
                    opt, value = list(map(str, user_input.split()))

        except ValueError:
            print("Error: Please adhere to the input format")
            continue

        # if input is not acceptable by int
        try:
            if int(opt) == 0:
                break

            elif int(opt) == 5:
                print("\t\t---Configuration---")
                print("\tSync folder: " + config['Sync_Folder'])
                print("\tSynchronous cycle (minute): " + str(config['Sync_Cycle']))
                print("\tNetwork Speed Limitation (KB/s)")
                print("\t\tUpload Rate: %s" % str(config['Network_Speed_Limitation']['Upload_Rate']))
                print("\t\tDownload Rate: %s" % str(config['Network_Speed_Limitation']['Download_Rate']))
                print("\tRun at startup: " + str(config['Auto_Start']))

            elif int(opt) not in list(range(1, 5)):
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