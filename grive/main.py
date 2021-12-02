from builtins import str

import sys
from os import path
from pydrive.drive import GoogleDrive

# list of parameters which require verification
require_auth = [
    "-start", "start", "-st",
    "-by_cron",
    "-download", "download", "-d",
    "-upload", "upload", "-u",
    "-share", "share", "-s",
    "-ls", "ls", "-l",
]

def main():
    # set path for relativistic imports if not launched as package
    try:
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import common_utils
        import auth_utils
        # import edit_config
        # import file_ops
        # import cron_handle
        import drive_utils

    # using relativistic imports directly if launched as package
    except ImportError:
        from . import common_utils
        from . import auth_utils
        # from . import edit_config
        # from . import file_ops
        # from . import cron_handle
        import drive_utils


    arguments = sys.argv[1:]

    arg_index = 0

    while True:

        if arg_index >= len(arguments):
            break
        # cho den khi chay het cac tham so

        # if argument requires authentication
        if arguments[arg_index] in require_auth:
            gauth = auth_utils.drive_auth(0)  # parameter to reset GAccount permissions
            drive = GoogleDrive(gauth)
        # set drive to none for operations not requiring auth
        else:
            drive = None

        if arguments[arg_index] == "-v" or arguments[arg_index] == "-version" or arguments[arg_index] == "version":
            print("Grive 1.0.0")
        elif arguments[arg_index] == "-st" or arguments[arg_index] == "-start" or arguments[arg_index] == "start":
            common_utils.cron_process("start")
        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-upload" or arguments[arg_index] == "upload":
            arg_index += 1
            # To do...
        elif arguments[arg_index] == "-s" or arguments[arg_index] == "-share" or arguments[arg_index] == "share":
            arg_index += 1
            # To do...
        elif arguments[arg_index] == "-ls" or arguments[arg_index] == "-l" or arguments[arg_index] == "ls":
            if (arg_index + 1) < len(arguments):
                if arguments[arg_index + 1] == "remote":
                    arg_index += 1
                    drive_utils.f_list(drive, "all", 0)
                # list of files in downloads directory
                elif arguments[arg_index + 1] == "local":
                    arg_index += 1
                    drive_utils.f_list_local()
                # no argument matching -ls
                # else:
                #     drive_utils.f_list(drive, "all", 0)

            # no argument after -ls
            else:
                drive_utils.f_list(drive, "all", 0)

        else:
            print(str(arguments[arg_index]) + " is an unrecognised argument. Please report if you know this is an error"
                                          ".\n\n")
            print("ARGS")

        arg_index += 1

def is_matching(index, len_arg):
    if index >= len_arg:
        print("Error: arguments less than what expected")
        return False
    return True

if __name__ == "__main__" and __package__ is None:
    main()