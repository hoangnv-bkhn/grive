from builtins import str

import sys
from os import path
import os
from datetime import datetime
from pydrive.drive import GoogleDrive
from prettytable import PrettyTable

# list of parameters which require verification
require_auth = [
    "-st",
    "-by_cron",
    "-d", "-do", "-df", "-dfo",
    "-u", "-uf", "-uo",
    "-s", "-sr", "-rs", "-sw", "-ws", "-su", "-us",  # share file
    "-rm", "-rml", "-rmr",
    "-ls_files", "ls_files", "-laf",
    "-ls", "ls", "-l",
    "-ls_trash", "ls_trash", "-lt",
    "-ls_folder", "ls_folder", "-lf",
    "-restore", "restore",
    "-sync", "sync", "-synchronize",
    "-usage", "usage"
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
            gauth = auth_utils.drive_auth(0)  # parameter to reset Google Account permissions
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

        elif arguments[arg_index] == "-re":
            auth_utils.reset_account()

        elif arguments[arg_index] == "-st":
            jobs.cron_process("start")

        elif arguments[arg_index] == "-x":
            jobs.cron_process("stop")

        elif arguments[arg_index] == "-y":
            jobs.cron_process("status")

        elif arguments[arg_index] == "-c":
            config_utils.write_config()

        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-uf" or arguments[arg_index] == "-uo":
            folder_id = None
            mode = False
            if (arguments[arg_index] == "-uo"):
                mode = True
            if (arguments[arg_index] == "-uf"):
                folder_id = arguments[arg_index + 1]
                arg_index += 2
            else:
                arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_up(drive, folder_id, arguments[arg_index:len(arguments)], mode)
                arg_index = len(arguments)


        elif arguments[arg_index] == "-sync":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_sync(drive, arguments[arg_index])
                arg_index = len(arguments)

        elif arguments[arg_index] == "-d" or arguments[arg_index] == "-do" \
                or arguments[arg_index] == "-df" or arguments[arg_index] == "-dfo":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                if arguments[0] == "-df" or arguments[0] == "-dfo":
                    if os.path.exists(arguments[len(arguments) - 1]):
                        save_location = arguments[len(arguments) - 1]
                        for argument in arguments[arg_index: len(arguments) - 1]:
                            print(argument)
                            drive_utils.f_down(drive, arguments[0], argument, save_location)
                    else:
                        print('%s does not exist !' % arguments[len(arguments) - 1])

                elif arguments[0] == "-d" or arguments[0] == "-do":
                    for argument in arguments[arg_index: len(arguments)]:
                        save_location = common_utils.get_local_path(drive, argument,
                                                                    config_utils.get_dir_sync_location())
                        drive_utils.f_down(drive, arguments[0], argument, save_location)

                arg_index = len(arguments)  # all arguments used up by download
                # if not drive_utils.is_valid_id(drive, arguments[len(arguments) - 1]) and len(arguments) > 2:

        elif arguments[arg_index] == "-s" or arguments[arg_index] == "-sr" or arguments[arg_index] == "-rs" or \
                arguments[arg_index] == "-ws" or arguments[arg_index] == "-sw" or \
                arguments[arg_index] == "-su" or arguments[arg_index] == "-us":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                # share to anyone
                if len(arguments) == 2:
                    drive_utils.share_link(drive, arguments[arg_index - 1], arguments[arg_index], "")
                else:
                    # share for specified users
                    for argument in arguments[arg_index + 1: len(arguments)]:
                        # print(argument)
                        drive_utils.share_link(drive, arguments[0], arguments[1], argument)

                arg_index = len(arguments)  # all arguments used up by share

        elif arguments[arg_index] == "-rm" or arguments[arg_index] == "-rml" or arguments[arg_index] == "-rmr":
            mode = "all"
            if (arguments[arg_index] == "-rml"):
                mode = "local"
            elif (arguments[arg_index] == "-rmr"):
                mode = "remote"
            arg_index += 1
            # in case of less arguments than required
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_remove(drive, mode, arguments[arg_index:len(arguments)])
                arg_index = len(arguments)

        elif arguments[arg_index] == "-o" or arguments[arg_index] == "-open" or arguments[arg_index] == "open":
            drive_utils.f_open(arguments[arg_index])

        elif arguments[arg_index] == "-ls" or arguments[arg_index] == "-l" or arguments[arg_index] == "ls":
            # if (arg_index + 1) < len(arguments):
            #     if arguments[arg_index + 1] == "remote":
            #         arg_index += 1
            #         files_list = drive_utils.f_list(drive, "all", 0)
            #         for file in files_list:
            #             print('Title: %s \t Modified Date: %s' % (file['title'],
            #                                                       datetime.utcfromtimestamp(file['modifiedDate'])))
            #         print(u'\u2620')
            #     # list of files in downloads directory
            #     elif arguments[arg_index + 1] == "local":
            #         arg_index += 1
            #         files_list = drive_utils.f_list_local(config_utils.get_dir_sync_location(), False)
            #         for file in files_list:
            #             print('Title: %s \t Modified Date: %s' % (file['title'],
            #                                                       datetime.utcfromtimestamp(file['modifiedDate'])))

            # # no argument after -ls
            # else:
            #     drive_utils.f_list(drive, "all", 0)

            remote_files_list = drive_utils.f_list(drive, "all", 0)
            local_files_list = drive_utils.f_list_local(config_utils.get_dir_sync_location(), False)

            for remote_file in remote_files_list:
                for local_file in local_files_list:
                    if remote_file['title'] == local_file['title']:
                        if remote_file['type'] == 'application/vnd.google-apps.folder':
                            if drive_utils.check_remote_dir_files_sync(drive,remote_file['id'],local_file['canonicalPath']):
                                remote_file['typeShow'] = "dongbo"
                            else:
                                remote_file['typeShow'] = "notdongbo"
                        else:
                            if remote_file['md5Checksum']:
                                if remote_file['isFolder']  == local_file['type']:
                                    remote_file['typeShow'] = "dongbo"
                                else:
                                    remote_file['typeShow'] = "notdongbo"
                            else:
                                if remote_file['fileSize']  == local_file['fileSize']:
                                    remote_file['typeShow'] = "dongbo"
                        break
                if remote_file['typeShow'] is None:
                    remote_file['typeShow'] = "dammay"

            result=[]
            for local_file in local_files_list:
                for remote_file in remote_files_list:
                    isHave = False
                    if remote_file['title'] == local_file['title']:
                        if remote_file['isFolder'] == local_file['type']:
                            isHave = True
                            break
                if not isHave:
                    local_file['typeShow']='maytinh'
                    result.append(local_file)

            table = PrettyTable()
            table.field_names = ['Name', 'id', 'status', 'Date Modified', 'Type' , 'Size']
            for file in remote_files_list:
                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                  datetime.utcfromtimestamp(file['modifiedDate']), file['type'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
            for file in result:
                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], '', common_utils.renderTypeShow(file['typeShow']),
                                                                  datetime.utcfromtimestamp(file['modifiedDate']), file['type'], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
            table.align = "l"
            print(table)

        elif arguments[arg_index] == "-usage" or arguments[arg_index] == "usage":
            driveAudioUsage, drivePhotoUsage, driveMoviesUsage, driveDocumentUsage, driveOthersUsage = drive_utils.f_calculateUsageOfFolder(drive)
            table = PrettyTable()
            table.field_names = ['Name', 'Size(MB)']
            table.add_row(['Audio', common_utils.sizeof_fmt(driveAudioUsage)])
            table.add_row(['Photo', common_utils.sizeof_fmt(drivePhotoUsage)])
            table.add_row(['Movies', common_utils.sizeof_fmt(driveMoviesUsage)])
            table.add_row(['Document', common_utils.sizeof_fmt(driveDocumentUsage)])
            table.add_row(['Others', common_utils.sizeof_fmt(driveOthersUsage)])

            table.align = "l"
            print(table)

        elif arguments[arg_index] == "-ls_files" or arguments[arg_index] == "-laf" or \
                arguments[arg_index] == "ls_files":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                files_list = drive_utils.f_list(drive, arguments[arg_index], 1)
                for file in files_list:
                    print('title: %s, id: %s' % (file['title'], file['id']))

        elif arguments[arg_index] == "-ls_trash" or arguments[arg_index] == "-lt" or arguments[arg_index] == "ls_trash":
            trash_files_list = drive_utils.f_list(drive, "trash", 0)
            print('%-30s | %50s | %30s | %10s' % ('Name', 'id', 'Date Modified', 'Size'))
            # print('---------------------------------------------------------------------------------------------------------------------------')
            for file in trash_files_list:
                print('%-30s | %50s | %30s | %10s' % (file['title'], file['id'], datetime.utcfromtimestamp(file['modifiedDate']), file['fileSize']))

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
                # add the Id to same directory on gDrive
                jobs.by_cron(drive, arguments[arg_index])
            else:
                jobs.by_cron(drive)

        elif arguments[arg_index] == "-restore" or arguments[arg_index] == "restore":
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
