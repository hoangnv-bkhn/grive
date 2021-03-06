import sys
from os import path
import os
from concurrent.futures.thread import ThreadPoolExecutor

from builtins import str
import socket

from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build
from pydrive.drive import GoogleDrive
from prettytable import PrettyTable

# list of parameters which require verification
require_auth = [
    "-st",
    "-by_cron",
    "-d", "-do", "-df", "-dfo",
    "-i", "-if",
    "-s", "-sr", "-sw", "-us",  # share file
    "-u", "-uo", "-uf", "-ufo"
                        "-da", "-dl", "-dr",
    "-l", "-lr", "-lp", "-lpr",
    "-lt",
    "-rt",
    "-sy",
    "-usage",
    "-e", "-ec",
    "-q"
]


def main():
    # set path for relativistic imports if not launched as package
    try:
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import common_utils
        import auth_utils
        import config_utils
        import drive_utils
        import drive_services
        import jobs
        import restore_default

    # using relativistic imports directly if launched as package
    except ImportError:
        from . import common_utils
        from . import auth_utils
        from . import config_utils
        from . import drive_utils
        from . import drive_services
        from . import jobs
        from . import restore_default

    arguments = sys.argv[1:]

    arg_index = 0

    while True:
        if arg_index >= len(arguments):
            break

        # if argument requires authentication
        if arguments[arg_index] in require_auth:
            g_auth, creds = auth_utils.drive_auth(0)  # parameter to reset Google Account permissions
            drive = GoogleDrive(g_auth)
            service = build('drive', 'v2', credentials=creds)
        # set drive to none for operations not requiring auth
        else:
            drive = None
            service = None

        if arguments[arg_index] == "-v":
            with open(common_utils.version_info_file) as p_file:
                if p_file is None:
                    print("Error reading version file. Please report at tokyo.example@gmail.com")
                    return
                p_data = p_file.read()
                print(p_data)

        elif arguments[arg_index] == "-o":
            drive_utils.f_open(arguments[arg_index])

        elif arguments[arg_index] == "-h":
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
            if is_connected():
                config_utils.write_config()

        elif arguments[arg_index] == '-z':
            if is_connected():
                restore_default.restore_default()

        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-uo" \
                or arguments[arg_index] == "-uf" or arguments[arg_index] == "-ufo":
            arg_index += 1
            if is_connected():
                if is_matching(arg_index, len(arguments)):
                    id_list = []
                    if arguments[0] == "-uf" or arguments[0] == "-ufo":
                        for argument in arguments[arg_index: len(arguments) - 1]:
                            if drive_utils.uploader(service, arguments[0], argument, arguments[len(arguments) - 1],
                                                    False,
                                                    id_list) is False:
                                print("'%s' is an invalid path !" % argument)
                        with ThreadPoolExecutor(5) as executor:
                            executor.map(drive_services.upload, id_list)

                    elif arguments[0] == "-u" or arguments[0] == "-uo":
                        for argument in arguments[arg_index: len(arguments)]:
                            if drive_utils.uploader(service, arguments[0], argument, None, False, id_list) is False:
                                print("'%s' is an invalid path !" % argument)
                        with ThreadPoolExecutor(5) as executor:
                            executor.map(drive_services.upload, id_list)

                    arg_index = len(arguments)

        elif arguments[arg_index] == "-e" or arguments[arg_index] == '-ec':
            arg_index += 1
            mode = True
            if arguments[0] == "-ec":
                mode = False
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_exclusive(arguments[arg_index], mode)
                arg_index = len(arguments)

        elif arguments[arg_index] == "-sy":
            arg_index += 1
            if is_connected():
                if is_matching(arg_index, len(arguments)):
                    drive_utils.f_sync(service, arguments[arg_index])
                    arg_index = len(arguments)

        elif arguments[arg_index] == "-d" or arguments[arg_index] == "-do" \
                or arguments[arg_index] == "-df" or arguments[arg_index] == "-dfo":
            arg_index += 1
            if is_connected():
                if is_matching(arg_index, len(arguments)):
                    id_list = []
                    if arguments[0] == "-df" or arguments[0] == "-dfo":
                        save_location = os.path.join(os.path.expanduser(Path().resolve()),
                                                     arguments[len(arguments) - 1])
                        if os.path.exists(save_location):
                            # save_location = arguments[len(arguments) - 1]
                            for argument in arguments[arg_index: len(arguments) - 1]:
                                if drive_utils.downloader(service, arguments[0], argument, save_location,
                                                          id_list) is False:
                                    print("'%s' is an invalid id !" % argument)
                            with ThreadPoolExecutor(5) as executor:
                                executor.map(drive_services.download, id_list)
                        else:
                            print('%s does not exist !' % arguments[len(arguments) - 1])

                    elif arguments[0] == "-d" or arguments[0] == "-do":
                        for argument in arguments[arg_index: len(arguments)]:
                            save_location, trashed = drive_services.get_local_path(service,
                                                                                   argument,
                                                                                   config_utils.get_folder_sync_path())
                            if save_location is not None:
                                drive_utils.downloader(service, arguments[0], argument, save_location, id_list)
                            else:
                                print("'%s' is an invalid id !" % argument)
                        # for elem in id_list:
                        #     print(elem)
                        with ThreadPoolExecutor(5) as executor:
                            executor.map(drive_services.download, id_list)

                    arg_index = len(arguments)  # all arguments used up by download

        elif arguments[arg_index] == "-s" or arguments[arg_index] == "-sr" \
                or arguments[arg_index] == "-sw" or arguments[arg_index] == "-us":
            arg_index += 1
            if is_connected():
                if is_matching(arg_index, len(arguments)):
                    # share to anyone
                    if len(arguments) == 2:
                        drive_utils.sharer(service, arguments[arg_index - 1], arguments[arg_index], "")
                    else:
                        # share for specified users
                        for argument in arguments[arg_index + 1: len(arguments)]:
                            drive_utils.sharer(service, arguments[0], arguments[1], argument)

                    arg_index = len(arguments)  # all arguments used up by share

        elif arguments[arg_index] == "-da" or arguments[arg_index] == "-dl" or arguments[arg_index] == "-dr":
            mode = "all"
            if arguments[arg_index] == "-dl":
                mode = "local"
            elif arguments[arg_index] == "-dr":
                mode = "remote"
            arg_index += 1
            # in case of less arguments than required
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_remove(drive, mode, arguments[arg_index:len(arguments)])
                arg_index = len(arguments)

        elif arguments[arg_index] == "-i" or arguments[arg_index] == "-if":
            arg_index += 1
            if is_connected():
                if is_matching(arg_index, len(arguments)):
                    info_local, info_remote = drive_utils.get_info(service, arguments[0], arguments[arg_index])
                    status = None
                    if info_local is None:
                        status = 'dammay'
                    else:
                        if info_remote['mimeType'] == "application/vnd.google-apps.folder":
                            if drive_utils.check_remote_dir_files_sync(service, info_remote['id'],
                                                                       info_local['canonicalPath']):
                                status = "dongbo"
                            else:
                                status = "notdongbo"
                        else:
                            if info_remote['md5Checksum']:
                                if info_remote['md5Checksum'] == info_local['md5Checksum']:
                                    status = "dongbo"
                                else:
                                    status = "notdongbo"
                            else:
                                if info_remote.get('fileSize') is not None and info_remote.get(
                                        'fileSize') == info_local.get('fileSize'):
                                    status = "dongbo"
                                elif info_remote['modifiedDate'] == datetime.utcfromtimestamp(
                                        info_local['modifiedDate']).timestamp():
                                    info_remote['typeShow'] = "dongbo"
                                else:
                                    info_remote['typeShow'] = "notdongbo"
                    if info_remote is not None and len(info_remote) > 0:
                        print()
                        # print('General\n'.rjust(60))
                        print("\033[92m {}\033[00m".format('General\n'.rjust(60)))

                        shared = False
                        owned_by_me = False
                        if info_remote.get('shared'):
                            shared = True
                        if info_remote.get('ownedByMe'):
                            owned_by_me = True

                        x = PrettyTable()
                        # x.field_names = ["", "General"]
                        # x.title = "General"
                        # x.add_row(["Status", info_remote.get('title'), '', ''])
                        x.add_row(["Title", info_remote.get('title'), '\n'])
                        x.add_row(["ID", info_remote.get('id'), '\n'])
                        x.add_row(["Status", common_utils.renderTypeShow(status) + "   " + (
                            u'\U0001F464' if info_remote['shared'] else ""), '\n'])
                        x.add_row(["Type", info_remote.get('mimeType'), '\n'])
                        x.add_row(["Modified Date", info_remote.get('modifiedDate'), '\n'])
                        x.add_row(["Created Date", info_remote.get('createdDate'), '\n'])
                        x.add_row(["Remote Path", info_remote.get('remotePath'), '\n'])
                        if owned_by_me:
                            x.add_row(["Owner", 'Me', '\n'])
                        for i, elem in enumerate(info_remote.get('userPermission')):
                            if elem.get('name') is None:
                                if elem.get('id') == 'anyone':
                                    user_name = "Everyone"
                                else:
                                    user_name = "Unavailable"
                            else:
                                user_name = elem.get('name')

                            if elem.get('emailAddress') is None:
                                user_mail = ''
                            else:
                                user_mail = elem.get('emailAddress')

                            if i == 0:
                                x.add_row(
                                    ["Permission", user_name.ljust(30) + elem.get('role').ljust(15) + user_mail, '\n'])
                            else:
                                x.add_row(["", user_name.ljust(30) + elem.get('role').ljust(15) + user_mail, '\n'])
                        if shared:
                            x.add_row(["Share Link", info_remote.get('alternateLink'), '\n'])
                        x.align = "l"
                        # x.set_style(prettytable.MSWORD_FRIENDLY)
                        x.header = False
                        x.border = False
                        x.left_padding_width = 5
                        print(x)

        elif arguments[arg_index] == "-l" or arguments[arg_index] == "-lr" or arguments[arg_index] == "-lp" or \
                arguments[arg_index] == "-lpr":
            if is_connected():
                root = drive_utils.get_tree_folder(service)

                if (arg_index + 1) < len(arguments):
                    if arguments[arg_index] == "-l":
                        arg_index += 1
                        drive_utils.show_folder(service, arguments[len(arguments) - 1])

                    elif arguments[arg_index] == "-lr":
                        arg_index += 1
                        drive_utils.show_folder_recusive(service, arguments[len(arguments) - 1], None, root)

                    elif arguments[arg_index] == "-lp":
                        arg_index += 1
                        drive_utils.show_folder_by_path(service, arguments[len(arguments) - 1])

                    elif arguments[arg_index] == "-lpr":
                        arg_index += 1
                        drive_utils.show_folder_recusive_by_path(service, arguments[len(arguments) - 1], root)

                else:  # not have argument
                    if arguments[arg_index] == "-l":
                        drive_utils.show_folder(service, "root")

                    elif arguments[arg_index] == "-lr":
                        drive_utils.show_folder_recusive(service, None, "Grive", root)

                    elif arguments[arg_index] == "-lp":
                        drive_utils.show_folder_by_path(service, config_utils.get_folder_sync_path())

                    elif arguments[arg_index] == "-lpr":
                        drive_utils.show_folder_recusive_by_path(service, config_utils.get_folder_sync_path(), root)
            # /home/tadanghuy/Documents/sync_grive

        elif arguments[arg_index] == "-q":
            if is_connected():
                grive_total = common_utils.sizeof_fmt(
                    int(service.about().get(fields='quotaBytesTotal').execute()['quotaBytesTotal']))
                grive_usage = common_utils.sizeof_fmt(
                    int(service.about().get(fields='quotaBytesUsed').execute()['quotaBytesUsed']))
                grive_trash = common_utils.sizeof_fmt(
                    int(service.about().get(fields='quotaBytesUsedInTrash').execute()['quotaBytesUsedInTrash']))

                drive_audio_usage, drive_photo_usage, drive_movies_usage, drive_document_usage, drive_others_usage = drive_utils.f_calculate_usage_of_folder(
                    service)
                total_usage = drive_audio_usage + drive_photo_usage + drive_movies_usage + drive_document_usage + drive_others_usage

                print("Used %s of %s" % ((common_utils.sizeof_fmt(total_usage)), grive_total))
                table = PrettyTable()
                table.field_names = ['Name', 'Size']
                table.add_row(['Audio', common_utils.sizeof_fmt(drive_audio_usage)])
                table.add_row(['Photo', common_utils.sizeof_fmt(drive_photo_usage)])
                table.add_row(['Movies', common_utils.sizeof_fmt(drive_movies_usage)])
                table.add_row(['Document', common_utils.sizeof_fmt(drive_document_usage)])
                table.add_row(['Others', common_utils.sizeof_fmt(drive_others_usage)])
                table.add_row(['Total', common_utils.sizeof_fmt(total_usage)])

                table.align = "l"
                print(table)

        elif arguments[arg_index] == "-lt":
            if is_connected():
                table = PrettyTable()
                table.field_names = ['Name', 'id', 'Date Modified', 'Type', 'Size']

                trash_files_list = drive_utils.get_all_data(service, "trash", 0)
                for file in trash_files_list:
                    table.add_row(
                        [(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                         common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime(
                             "%m/%d/%Y %H:%M"),
                         file['mimeType'].split(".")[-1],
                         common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                table.align = 'l'
                print(table)
        elif arguments[arg_index] == "-by_cron":
            if is_connected():
                # modified to get the id and destiny directory
                if is_matching(arg_index, len(arguments)):
                    jobs.by_cron(service)

        elif arguments[arg_index] == "-rt":
            arg_index += 1
            if is_connected():
                # in case of less arguments than required
                if is_matching(arg_index, len(arguments)):
                    drive_utils.file_restore(drive, arguments[arg_index:len(arguments)])
                    arg_index = len(arguments)

        else:
            print(str(arguments[arg_index]) +
                  " is an unrecognised argument. Please report if you know this is an error !")
            return

        arg_index += 1


def check_internet_socket(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False


def is_connected():
    if check_internet_socket():
        return True
    else:
        print("Opps! This function require to connect network!")
        return False


def is_matching(index, len_arg):
    if index >= len_arg:
        print("Error: arguments less than what expected")
        return False
    return True


if __name__ == "__main__" and __package__ is None:
    main()
