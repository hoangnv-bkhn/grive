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
    "-ls", "ls", "-l"
]

def main():
    # set path for relativistic imports if not launched as package
    try:
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import common_utils
        import auth_utils
        import config_utils
        import drive_utils

    # using relativistic imports directly if launched as package
    except ImportError:
        from . import common_utils
        from . import auth_utils
        from . import config_utils
        from . import drive_utils

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

        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-upload" or arguments[arg_index] == "upload":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_create(drive, arguments[arg_index], None,
                                     str(common_utils.get_file_name(arguments[arg_index])), True)

        elif arguments[arg_index] == "-d" or arguments[arg_index] == "-download" or arguments[arg_index] == "download":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                # download entire drive folder
                if arguments[arg_index] == "all":
                    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
                    # print(file_list)
                    for argument in file_list:
                        drive_utils.f_down(drive, argument, config_utils.get_dir_sync_location())
                # download only specified folder
                else:
                    for argument in arguments[arg_index: len(arguments)]:
                        # print(argument)
                        drive_utils.f_down(drive, argument, config_utils.get_dir_sync_location())
                arg_index = len(arguments)  # all arguments used up by download

        elif arguments[arg_index] == "-s" or arguments[arg_index] == "-share" or arguments[arg_index] == "share":
            arg_index += 2
            if is_matching(arg_index, len(arguments)):
                drive_utils.share_link(drive, arguments[arg_index - 1], arguments[arg_index], True)
                arg_index = len(arguments)

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