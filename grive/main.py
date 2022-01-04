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
    "-r", "-remove", "remove",
    "-ls_files", "ls_files", "-laf",
    "-ls", "ls", "-l",
    "-ls_trash", "ls_trash", "-lt",
    "-ls_folder", "ls_folder", "-lf",
    "-restore", "restore", "-rs",
    "-sync", "sync", "-synchronize"
]

def main():
    # set path for relativistic imports if not launched as package
    try:
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import common_utils
        import auth_utils
        import config_utils
        import drive_utils
        import jobs

    # using relativistic imports directly if launched as package
    except ImportError:
        from . import common_utils
        from . import auth_utils
        from . import config_utils
        from . import drive_utils
        from . import jobs

    arguments = sys.argv[1:]

    arg_index = 0

    while True:

        if arg_index >= len(arguments):
            break

        # if argument requires authentication
        if arguments[arg_index] in require_auth:
            gauth = auth_utils.drive_auth(0)  # parameter to reset GAccount permissions
            drive = GoogleDrive(gauth)
        # set drive to none for operations not requiring auth
        else:
            drive = None

        if arguments[arg_index] == "-v" or arguments[arg_index] == "-version" or arguments[arg_index] == "version":
            with open(common_utils.version_info_file) as p_file:
                if p_file is None:
                    print("Error reading version file. Please report at tokyo.example@gmail.com")
                    return
                p_data = p_file.read()
                print(p_data)

        elif arguments[arg_index] == "-h" or arguments[arg_index] == "-help" or arguments[arg_index] == "help":
            with open(common_utils.help_file) as p_file:
                if p_file is None:
                    print("Error reading user manual file.")
                    return
                p_data = p_file.read()
                print(p_data)

        elif arguments[arg_index] == "-re" or arguments[arg_index] == "-reset" or arguments[arg_index] == "reset":
            auth_utils.reset_account()

        elif arguments[arg_index] == "-st" or arguments[arg_index] == "-start" or arguments[arg_index] == "start":
            jobs.cron_process("start")

        elif arguments[arg_index] == "-x" or arguments[arg_index] == "-stop" or arguments[arg_index] == "stop":
            jobs.cron_process("stop")

        elif arguments[arg_index] == "-y" or arguments[arg_index] == "-status" or arguments[arg_index] == "status":
            jobs.cron_process("status")

        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-upload" or arguments[arg_index] == "upload":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_create(drive, arguments[arg_index], None,
                                     str(common_utils.get_file_name(arguments[arg_index])), True)

        elif arguments[arg_index] == "-sync" or arguments[arg_index] == "-synchronize" or arguments[arg_index] == "sync":
            drive_utils.f_sync(drive)

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

        elif arguments[arg_index] == "-r" or arguments[arg_index] == "-remove" or arguments[arg_index] == "remove":
            arg_index += 2
            # in case of less arguments than required
            if is_matching(arg_index, len(arguments)):
                drive_utils.file_remove(drive, arguments[arg_index - 1], arguments[arg_index:len(arguments)])
                arg_index = len(arguments)

        elif arguments[arg_index] == "-o" or arguments[arg_index] == "-open" or arguments[arg_index] == "open":
            drive_utils.f_open(arguments[arg_index])

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

        elif arguments[arg_index] == "-ls_files" or arguments[arg_index] == "-laf" or \
                arguments[arg_index] == "ls_files":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_list(drive, arguments[arg_index], 1)

        elif arguments[arg_index] == "-ls_trash" or arguments[arg_index] == "-lt" or arguments[arg_index] == "ls_trash":
            drive_utils.f_list(drive, "trash", 0)

        elif arguments[arg_index] == "-ls_folder" or arguments[arg_index] == "-lf" or \
                arguments[arg_index] == "ls_folder":
            print(drive)
            arg_index += 1  # increase arg_index to read the query argument
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_list(drive, arguments[arg_index], 0)

        elif arguments[arg_index] == "-by_cron":
            # modified to get the id and destiny directory
            if (arg_index + 1) < len(arguments):
                arg_index += 1
                # add the Id to same dicetory on gDrive
                jobs.by_cron(drive, arguments[arg_index])
            else:
                jobs.by_cron(drive)

        elif arguments[arg_index] == "-rs" or arguments[arg_index] == "-restore" or arguments[arg_index] == "restore":
            arg_index += 1
            # in case of less arguments than required
            if is_matching(arg_index, len(arguments)):
                drive_utils.file_restore(drive, arguments[arg_index:len(arguments)])
                arg_index = len(arguments)

        else:
            print(str(arguments[arg_index]) + " is an unrecognised argument. Please report if you know this is an error"
                                          ".\n\n")

        arg_index += 1

def is_matching(index, len_arg):
    if index >= len_arg:
        print("Error: arguments less than what expected")
        return False
    return True

if __name__ == "__main__" and __package__ is None:
    main()