
import sys
from os import path
import os
from concurrent.futures.thread import ThreadPoolExecutor

from builtins import str
import re

import logging
from datetime import datetime
from pathlib import Path
from threading import local
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
    "-u", "-uf", "-uo",
    "-da", "-dl", "-dr",
    "-ls_files", "ls_files", "-laf",
    "-l", "-lr", "-lp", "-lpr", "-lf", "-lfr",
    "-ls_trash", "ls_trash", "-lt",
    "-ls_folder",
    "-restore", "restore",
    "-z",
    "-usage", "usage",
    "-q", "-qc",
    "-xs"
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

    logger = logging.getLogger("Grive")
    logger.setLevel(logging.DEBUG)
    common_utils.dir_exists(os.path.join(os.environ['HOME'], '.grive'))
    log_path = os.path.join(os.environ['HOME'], '.grive/grive.log')
    if not os.path.exists(log_path):
        print(log_path)
        with open(log_path, 'w+') as fp:
            pass
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    send_to_log(logger, 2, "Grive Started")

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

        elif arguments[arg_index] == '-xs':
            restore_default.restore_default()

        elif arguments[arg_index] == "-u" or arguments[arg_index] == "-uf" or arguments[arg_index] == "-uo":
            folder_id = None
            mode = False
            if arguments[arg_index] == "-uo":
                mode = True
            if arguments[arg_index] == "-uf":
                folder_id = arguments[len(arguments) - 1]
                arg_index += 2
            else:
                arg_index += 1
            if is_matching(arg_index, len(arguments)):
                if arguments[arg_index] == "-uf":
                    drive_utils.f_up(drive, folder_id, arguments[arg_index:len(arguments) - 1], mode)
                    arg_index = len(arguments)
                else:
                    drive_utils.f_up(drive, folder_id, arguments[arg_index:len(arguments)], mode)
                    arg_index = len(arguments)

        elif arguments[arg_index] == "-q" or arguments[arg_index] == '-qc':
            arg_index += 1
            mode = True
            if arguments[arg_index] == "-q":
                mode = False
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_exclusive(arguments[arg_index], mode)
                arg_index = len(arguments)

        elif arguments[arg_index] == "-z":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                drive_utils.f_sync(service, arguments[arg_index])
                arg_index = len(arguments)

        elif arguments[arg_index] == "-d" or arguments[arg_index] == "-do" \
                or arguments[arg_index] == "-df" or arguments[arg_index] == "-dfo":
            arg_index += 1
            # print()
            if is_matching(arg_index, len(arguments)):
                id_list = []
                if arguments[0] == "-df" or arguments[0] == "-dfo":
                    save_location = os.path.join(os.path.expanduser(Path().resolve()), arguments[len(arguments) - 1])
                    if os.path.exists(save_location):
                        # save_location = arguments[len(arguments) - 1]
                        for argument in arguments[arg_index: len(arguments) - 1]:
                            if drive_utils.downloader(service, arguments[0], argument, save_location, id_list) is False:
                                print("'%s' is an invalid id !" % argument)
                        with ThreadPoolExecutor(5) as executor:
                            executor.map(drive_services.download, id_list)
                    else:
                        print('%s does not exist !' % arguments[len(arguments) - 1])

                elif arguments[0] == "-d" or arguments[0] == "-do":
                    for argument in arguments[arg_index: len(arguments)]:
                        save_location = drive_services.get_local_path(service,
                                                                      argument, config_utils.get_folder_sync_path())
                        if save_location is not None:
                            drive_utils.downloader(service, arguments[0], argument, save_location, id_list)
                        else:
                            print("'%s' is an invalid id !" % argument)
                    # for elem in id_list:
                    #     print(elem)
                    with ThreadPoolExecutor(5) as executor:
                        executor.map(drive_services.download, id_list)

                arg_index = len(arguments)  # all arguments used up by download
                # if not drive_utils.is_valid_id(drive, arguments[len(arguments) - 1]) and len(arguments) > 2:
            # print('\n')

        elif arguments[arg_index] == "-s" or arguments[arg_index] == "-sr" \
                or arguments[arg_index] == "-sw" or arguments[arg_index] == "-us":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                # share to anyone
                if len(arguments) == 2:
                    drive_utils.share_link(drive, arguments[arg_index - 1], arguments[arg_index], "")
                else:
                    # share for specified users
                    for argument in arguments[arg_index + 1: len(arguments)]:
                        drive_utils.share_link(drive, arguments[0], arguments[1], argument)

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

        elif arguments[arg_index] == "-o" or arguments[arg_index] == "-open" or arguments[arg_index] == "open":
            drive_utils.f_open(arguments[arg_index])

        elif arguments[arg_index] == "-i" or arguments[arg_index] == "-if":
            arg_index += 1
            if is_matching(arg_index, len(arguments)):
                info_local, info_remote = drive_utils.get_info(drive, arguments[0], arguments[arg_index])
                # table = PrettyTable()
                # table.field_names = ['Name', 'Id', 'StorageLocation', 'Date Modified', 'Size']
                # table.add_column("Field 1",['Name', 'Id', 'StorageLocation', 'Date Modified', 'Size'])

                # table.add_row([info_local['title'], info_local['id'],info_local['storageLocation'],info_local['modifiedDate'],info_local['title'],info_local['title'] ])
                # table.add_row([(info_local['title'][:37]+ "...")if len(info_local["title"])> 37 else info_local['title'],
                #                         info_local['id'] if info_local['id'] else '',
                #                         info_local['storageLocation'],
                #                         datetime.fromtimestamp(info_local['modifiedDate']).strftime("%m/%d/%Y %H:%M"),
                #                         common_utils.sizeof_fmt(common_utils.getFileSize(info_local))]),

                print("%-40s | %30s | %10s | %20s | %10s" % ((info_local['title'][:37]+ "...")if len(info_local["title"])> 37 else info_local['title'],
                                        info_local['id'] if info_local['id'] else '',
                                        info_local['storageLocation'],
                                        datetime.fromtimestamp(info_local['modifiedDate']).strftime("%m/%d/%Y %H:%M"),
                                        common_utils.sizeof_fmt(common_utils.getFileSize(info_local))))  

                # table.add_row([(info_remote['title'][:37]+ "...")if len(info_remote["title"])> 37 else info_remote['title'],
                #                         info_remote['id'] if info_remote['id'] else '',
                #                         info_remote['storageLocation'],
                #                         datetime.fromtimestamp(info_remote['modifiedDate']).strftime("%m/%d/%Y %H:%M"),
                #                         common_utils.sizeof_fmt(common_utils.getFileSize(info_remote))]),
                print("%-40s | %30s | %10s | %20s | %10s" % ((info_remote['title'][:37]+ "...")if len(info_remote["title"])> 37 else info_remote['title'],
                                        info_remote['id'] if info_remote['id'] else '',
                                        info_remote['storageLocation'],
                                        datetime.fromtimestamp(info_remote['modifiedDate']).strftime("%m/%d/%Y %H:%M"),
                                        common_utils.sizeof_fmt(common_utils.getFileSize(info_remote))))
                print(info_local)
                print("+++")
                print(info_remote)
                # print(table)
        elif arguments[arg_index] == "-l" or arguments[arg_index] == "-lr" or  arguments[arg_index] == "-lp" or arguments[arg_index] == "-lpr" or \
                                    arguments[arg_index] == "-lf" or arguments[arg_index] == "-lfr":
            table = PrettyTable()
            table.field_names = ['Name', 'Id', 'Status', 'Date Modified', 'Type' , 'Size']
            is_print = True

            remote_files_list = []
            local_files_list = []
            if (arg_index + 1) < len(arguments):
                if arguments[arg_index] == "-l":
                    arg_index += 1
                    remote_files_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], 0)

                    if(len(remote_files_list)  == 0) :
                        is_print = False
                        print("Error: Invalid id folder or id folder is not exits!")
                    else:
                        root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                        x = list(filter(lambda e: e['id']== arguments[len(arguments) - 1] , root_folders_list))
                        if len(x)!=0: 
                            local_folder = x[0]
                            local_files_list, local_folders_list = drive_utils.f_list_local(local_folder['canonicalPath'], False)

                            drive_utils.compare_and_change_type_show(service, remote_files_list, local_files_list)

                            result= drive_utils.filter_local_only(local_files_list,remote_files_list)
                            for file in result:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'] if file['id'] else '', common_utils.renderTypeShow(file['typeShow']),
                                                                    datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                            
                        else: 
                            for file in remote_files_list:
                                file['typeShow']='dammay'

                        for file in remote_files_list:
                            table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                     
                elif arguments[arg_index] == "-lr":
                    arg_index += 1
                    # remote_files_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], 1)
                    remote_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], 1)
                    remote_files_list = list(filter(lambda e : not e['mimeType'] == "application/vnd.google-apps.folder", remote_list))

                    if(len(remote_files_list)  == 0) :
                        is_print = False
                        print("Error: Invalid id folder or id folder is not exits!")
                    else:
                        root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                        x = list(filter(lambda e: e['id']== arguments[len(arguments) - 1] , root_folders_list))
                        if len(x)!=0: 
                            local_folder = x[0]
                            local_files_list, local_folders_list = drive_utils.f_list_local(local_folder['canonicalPath'], True)

                            drive_utils.compare_and_change_type_show(service, remote_files_list, local_files_list)
                            
                            result= drive_utils.filter_local_only(local_files_list,remote_files_list)
                            for file in result:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'] if file['id'] else '', common_utils.renderTypeShow(file['typeShow']),
                                                                    datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), 'file', common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                            
                        else: 
                            for file in remote_files_list:
                                file['typeShow']='dammay'

                        for file in remote_files_list:
                            table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                     
                elif arguments[arg_index] == "-lp":
                    arg_index += 1
                    try:
                        local_files_list, local_folders_list = drive_utils.f_list_local(arguments[len(arguments) - 1], False)

                        root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                        x = list(filter(lambda e: e['canonicalPath']== arguments[len(arguments) - 1] , root_folders_list))
                        if len(x) > 0:
                            remote_folder = x[0]
                            remote_files_list = drive_utils.get_all_data(service, remote_folder['id'], False)

                            drive_utils.compare_and_change_type_show_local(service, local_files_list, remote_files_list)

                            result = drive_utils.filter_remote_only(remote_files_list, local_files_list)

                            for file in result:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])

                            for file in local_files_list:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                            datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'] if 'type' in file else "file", common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                        else:
                            for file in local_files_list:
                                file['typeShow'] = 'maytinh'

                    except FileNotFoundError as error:
                        print(error)
                        is_print = False
                elif arguments[arg_index] == "-lpr":
                    arg_index += 1
                    try:
                        local_files_list, local_folders_list = drive_utils.f_list_local(arguments[len(arguments) - 1], True)

                        root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                        x = list(filter(lambda e: e['canonicalPath']== arguments[len(arguments) - 1] , root_folders_list))
                        if len(x) > 0:
                            remote_folder = x[0]
                            # remote_files_list = drive_utils.get_all_data(service, remote_folder['id'], True)
                            remote_list = drive_utils.get_all_data(service, remote_folder['id'], True)
                            remote_files_list = list(filter(lambda e : not e['mimeType'] == "application/vnd.google-apps.folder", remote_list))

                            drive_utils.compare_and_change_type_show_local(drive, local_files_list, remote_files_list)

                            result = drive_utils.filter_remote_only(remote_files_list, local_files_list)

                            for file in result:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])

                            for file in local_files_list:
                                table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                            datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'] if 'type' in file else "file", common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                        else:
                            for file in local_files_list:
                                file['typeShow'] = 'maytinh'

                    except FileNotFoundError as error:
                        print(error)
                        is_print = False
                elif arguments[arg_index] == "-lf":
                    arg_index += 1
                    root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                    x = list(filter(lambda e: e['id']== arguments[len(arguments) - 1] , root_folders_list))
                    if(len(x) != 0):
                        local_folder = x[0]
                        local_files_list, local_folders_list = drive_utils.f_list_local(local_folder['canonicalPath'], False)

                        remote_files_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], False)

                        drive_utils.compare_and_change_type_show_local(service, local_files_list, remote_files_list)

                        for file in local_files_list:
                            table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                        datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'] if 'type' in file else "file", common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                    else: 
                        print("Error: Invalid id folder!")
                        is_print = False
                elif arguments[arg_index] == "-lfr":
                    arg_index += 1
                    root_files_list, root_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                    x = list(filter(lambda e: e['id']== arguments[len(arguments) - 1] , root_folders_list))
                    if len(x) > 0:
                        local_folder = x[0]
                        local_files_list, local_folders_list = drive_utils.f_list_local(local_folder['canonicalPath'], True)

                        # remote_files_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], True)
                        remote_list = drive_utils.get_all_data(service, arguments[len(arguments) - 1], True)
                        remote_files_list = list(filter(lambda e : not e['mimeType'] == "application/vnd.google-apps.folder", remote_list))


                        drive_utils.compare_and_change_type_show_local(drive, local_files_list, remote_files_list)

                        for file in local_files_list:
                            table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                        datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'] if 'type' in file else "file", common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                    else: 
                        print("Error: Invalid id folder!")
                        is_print = False
   
            else: # not have argument
                if arguments[arg_index] == "-l" : 
                    remote_files_list = drive_utils.get_all_data(service, "root", False)
                    print(remote_files_list)
                    local_files_list, local_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), False)
                    
                    result= drive_utils.filter_local_only(local_files_list,remote_files_list)
                    
                    for file in result:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'] if file['id'] else '', common_utils.renderTypeShow(file['typeShow']),
                                                                    datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                    
                    drive_utils.compare_and_change_type_show(service, remote_files_list, local_files_list)
                    # common_utils.print_table_remote(remote_files_list)

                    for file in remote_files_list:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(int(file['fileSize'])) if file['fileSize'] else "" ])

                elif arguments[arg_index] == "-lr":
                    # remote_files_list = drive_utils.get_all_data(service, "root", True)
                    remote_list = drive_utils.get_all_data(service, "root", True)
                    remote_files_list = list(filter(lambda e : not e['mimeType'] == "application/vnd.google-apps.folder", remote_list))


                    local_files_list, local_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)

                    # result= drive_utils.filter_local_only(local_files_list  + local_folders_list, remote_files_list)
                    result= drive_utils.filter_local_only(local_files_list , remote_files_list)

                    for file in result:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], "", common_utils.renderTypeShow(file['typeShow']),
                                                                datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), 'file', common_utils.sizeof_fmt(common_utils.getFileSize(file))])
                    drive_utils.compare_and_change_type_show(service, remote_files_list, local_files_list + local_folders_list)

                    # drive_utils.show(service, remote_files_list , "root")
                    for file in remote_files_list:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                                common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(int(file['fileSize'])) if file['fileSize'] else "" ])

                elif arguments[arg_index] == "-lp" or arguments[arg_index] == "-lf":
                    local_files_list, local_folders_list = drive_utils.f_list_local(
                        config_utils.get_folder_sync_path(), False)
                    remote_files_list = drive_utils.get_all_data(service, 'root', False)
                    drive_utils.compare_and_change_type_show_local(service, local_files_list, remote_files_list)

                    result = drive_utils.filter_remote_only(remote_files_list, local_files_list)

                    for file in result:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])

                    for file in local_files_list:
                        table.add_row(
                            [(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                             common_utils.renderTypeShow(file['typeShow']),
                             datetime.utcfromtimestamp(file['modifiedDate']),
                             file['type'] if 'type' in file else "file",
                             common_utils.sizeof_fmt(common_utils.getFileSize(file))])

                elif arguments[arg_index] == "-lpr" or arguments[arg_index] == "-lfr":
                    local_files_list, local_folders_list = drive_utils.f_list_local(config_utils.get_folder_sync_path(), True)
                    # remote_files_list = drive_utils.get_all_data(service, 'root', True)
                    remote_list = drive_utils.get_all_data(service, "root", True)
                    remote_files_list = list(filter(lambda e : not e['mimeType'] == "application/vnd.google-apps.folder", remote_list))

                    drive_utils.compare_and_change_type_show_local(service, local_files_list, remote_files_list)

                    result = drive_utils.filter_remote_only(remote_files_list, local_files_list)

                    for file in result:
                        table.add_row([(file['title'][:37]+ "...")if len(file["title"])> 37 else file['title'], file['id'], common_utils.renderTypeShow(file['typeShow']),
                                                    common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime("%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])


                    for file in local_files_list:
                        table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'],
                                       file['id'], common_utils.renderTypeShow(file['typeShow']),
                                       datetime.utcfromtimestamp(file['modifiedDate']),
                                       file['type'] if 'type' in file else "file",
                                       common_utils.sizeof_fmt(common_utils.getFileSize(file))])

            if is_print: 
                table.align = "l"
                print(table)

        # /home/tadanghuy/Documents/sync_grive/test
        elif arguments[arg_index] == "-usage" or arguments[arg_index] == "usage":
            drive_audio_usage, drive_photo_usage, drive_movies_usage, drive_document_usage, drive_others_usage = drive_utils.f_calculate_usage_of_folder(service)
            total_usage = drive_audio_usage + drive_photo_usage + drive_movies_usage + drive_document_usage + drive_others_usage
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

        elif arguments[arg_index] == "-ls_trash" or arguments[arg_index] == "-lt" or arguments[arg_index] == "ls_trash":
            table = PrettyTable()
            table.field_names = ['Name', 'id', 'Date Modified', 'Type', 'Size']

            trash_files_list = drive_utils.get_all_data(service, "trash", 0)
            for file in trash_files_list:
                # print('%-30s | %50s | %30s | %10s' % (file['title'], file['id'], datetime.utcfromtimestamp(file['modifiedDate']), file['fileSize']))
                table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                               common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime(
                                   "%m/%d/%Y %H:%M"),
                               file['mimeType'].split(".")[-1], common_utils.sizeof_fmt(common_utils.getFileSize(file))])
            table.align = 'l'
            print(table)
        elif arguments[arg_index] == "-by_cron":
            # modified to get the id and destiny directory
            if (arg_index + 1) < len(arguments):
                arg_index += 1
                # add the Id to same directory on gDrive
                jobs.by_cron(drive, arguments[arg_index])
            else:
                jobs.by_cron(service)

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


def send_to_log(logger, LogType, LogMsg):
    if 3 >= LogType:
        if LogType == 3:
            logger.debug(LogMsg)
        if LogType == 2:
            logger.info(LogMsg)
        if LogType == 1:
            logger.error(LogMsg)


if __name__ == "__main__" and __package__ is None:
    main()
