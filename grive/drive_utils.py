import threading
from builtins import str
import json
import os
import sys
import shutil
from pathlib import Path
from concurrent.futures.thread import ThreadPoolExecutor

import pyperclip
import hashlib
import re
from prettytable import PrettyTable
from datetime import datetime

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
    import drive_services
    import tree
except ImportError:
    from . import common_utils
    from . import config_utils
    from . import drive_services
    from . import tree


# def f_all(drive, fold_id, file_list, download, sync_folder, option, folder_list):
#     """Recursively download or just list files in folder
#
#         :param drive: Google Drive instance
#         :param fold_id: id of folder to search
#         :param file_list: initial list to store list of file when search
#         :param download: True if downloads, False if just recursively list file
#         :param sync_folder: folder to store when download
#         :param option: option download (overwrite or not)
#         :param folder_list: initial list to store list of folder when search
#
#         :returns: List of file store in file_list param
#     """
#
#     q_string = "'%s' in parents and trashed=false" % fold_id
#     for f in drive.ListFile({'q': q_string}).GetList():
#         if f['mimeType'] == 'application/vnd.google-apps.folder':
#             # print(f['title'])
#             if download:  # if we are to download the files
#                 save_location = os.path.join(sync_folder, f['title'])
#                 if os.path.exists(save_location):
#                     save_location = common_utils.get_dup_name(sync_folder, os.path.basename(sync_folder))
#
#                 common_utils.dir_exists(save_location)
#                 os.setxattr(save_location, 'user.id', str.encode(f['id']))
#
#                 stats = os.stat(save_location)
#                 os.utime(save_location, (stats.st_atime, common_utils.utc2local(
#                     datetime.strptime(f['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
#
#                 f_all(drive, f['id'], None, True, save_location, option, folder_list)
#
#             else:  # we want to just list the files
#                 # print(f['title'])
#                 folder_list.append(f)
#                 f_all(drive, f['id'], file_list, False, None, None, folder_list)
#         else:
#             if download:
#                 downloader(drive, option, f['id'], sync_folder)
#             else:
#                 file_list.append(f)


def downloader(service, option, instance_id, save_folder, id_list=None):
    if id_list is None:
        id_list = []
    try:

        instance = service.files().get(fileId=instance_id).execute()
        # open mime_swap dictionary for changing mimeType if required
        with open(common_utils.mime_dict) as f:
            mime_swap = json.load(f)

        overwrite = False
        if common_utils.check_option(option, 'o', 3) or common_utils.check_option(option, 'o', 4):
            overwrite = True

        has_in_local = False

        remote_name = instance.get('title')
        remote_id = instance.get('id')

        # checking if the specified id is a folder
        if instance['mimeType'] == mime_swap['folder']:
            folder_local_name = remote_name

            local_files, local_folders = f_list_local(save_folder, 0)
            for elem in local_files:
                if elem['id'] == remote_id:
                    has_in_local = True
                    folder_local_name = elem['title']

            folder_path = os.path.join(save_folder, folder_local_name)
            # print(folder_path)
            flag = True
            if has_in_local:
                if overwrite:
                    if os.path.isdir(folder_path):
                        shutil.rmtree(folder_path)
                        # print("Recreating folder %s in %s" % (remote_name, save_folder))
                else:
                    flag = False
                    print("Folder '%s' already present in %s" % (instance['title'], save_folder))
            else:
                print("Creating folder %s in %s" % (remote_name, save_folder))

            if flag:
                save_location = folder_path
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(save_folder, os.path.basename(folder_path))

                common_utils.dir_exists(save_location)
                os.setxattr(save_location, 'user.id', str.encode(remote_id))
                stats = os.stat(save_location)
                os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                    datetime.strptime(instance['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

                file_contained = drive_services.get_files_in_folder(service, instance_id)
                for item in file_contained:
                    location, trashed = drive_services.get_local_path(service, item.get('id'),
                                                                      config_utils.get_folder_sync_path())
                    downloader(service, option, item.get('id'), location, id_list)

        else:
            is_workspace_document = False
            if instance.get('mimeType') in mime_swap:
                # open formats.json for adding custom format
                with open(common_utils.format_dict) as f:
                    format_add = json.load(f)
                # changing file name to suffix file format
                file_local_name = remote_name + format_add[instance['mimeType']]
                is_workspace_document = True
            else:
                file_local_name = remote_name

            local_files, local_folders = f_list_local(save_folder, 0)
            for elem in local_files:
                if elem['id'] == remote_id:
                    has_in_local = True
                    file_local_name = elem['title']

            flag = True
            if has_in_local:
                if overwrite:
                    if os.path.isfile(os.path.join(save_folder, file_local_name)):
                        os.remove(os.path.join(save_folder, file_local_name))
                else:
                    flag = False
                    print(" %s already present in %s" % (file_local_name, save_folder))

            if flag:
                save_location = os.path.join(save_folder, file_local_name)
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(save_folder, file_local_name)
                # print("Download '%s' in '%s'" % (instance.get('title'), save_location))
                if is_workspace_document:
                    elem = {
                        'id': instance.get('id'),
                        'title': instance.get('title'),
                        'saveLocation': save_location,
                        'modifiedDate': instance.get('modifiedDate'),
                        'mimeType': mime_swap[instance['mimeType']]
                    }
                    id_list.append(elem)
                else:
                    elem = {
                        'id': instance.get('id'),
                        'title': instance.get('title'),
                        'saveLocation': save_location,
                        'modifiedDate': instance.get('modifiedDate'),
                        'mimeType': None
                    }
                    id_list.append(elem)
    except:
        # print(" %s is an invalid id !" % instance_id)
        return False


def uploader(service, option, path, parent_id, for_sync, id_list=None):
    try:
        path = os.path.normpath(path)
        overwrite = False
        is_local_sync = False
        f_id = None
        file_info_local, folder_info_local, file_info, folder_info = [], [], [], []
        if os.path.exists(path) is False:
            return False
        if id_list is None:
            id_list = []
        if common_utils.check_option(option, 'o', 3) or common_utils.check_option(option, 'o', 4) or for_sync is True:
            overwrite = True
        if os.path.normpath(config_utils.get_folder_sync_path()) in os.path.normpath(path):
            is_local_sync = True
        if is_local_sync is True and parent_id is None:
            file_info_local, folder_info_local, file_info, folder_info = get_list_file_for_sync(service,
                                                                                                config_utils.get_folder_sync_path(),
                                                                                                'all')
            try:
                f_id = os.getxattr(path, 'user.id')
                f_id = f_id.decode()
            except:
                f_id = None
            if f_id is not None:
                if os.path.isdir(path):
                    f_list = folder_info
                else:
                    f_list = file_info
                if f_list is not None:
                    for i in f_list:
                        if i['id'] == f_id:
                            if overwrite is False:
                                print("%s already present in Google Drive" % common_utils.get_file_name(path))
                                return True
        f_new_id = None
        if parent_id is not None:
            f_new_id = parent_id
        if is_local_sync is True and parent_id is None:
            f_info_local = None
            if os.path.isdir(path):
                for i in folder_info_local:
                    if i['absolute_path'] == os.path.dirname(path) and i['name'] == common_utils.get_file_name(path):
                        f_info_local = i
                        break
            else:
                for i in file_info_local:
                    if i['absolute_path'] == os.path.dirname(path) and i['name'] == common_utils.get_file_name(path):
                        f_info_local = i
                        break
            check_location = None
            for i in f_info_local['parents']:
                if check_location is not False:
                    check_path = drive_services.filter_trash(service, i['folder_id'],
                                                             config_utils.get_folder_sync_path())
                    if check_path is not None:
                        if os.path.normpath(check_path) != os.path.normpath(i['folder_path']):
                            check_location = False
                        else:
                            f_new_id = i['folder_id']
                    else:
                        check_location = False
                if check_location is False:
                    if f_new_id is None:
                        file_metadata = {
                            'title': i['folder_name'],
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                    else:
                        file_metadata = {
                            'title': i['folder_name'],
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [{'id': f_new_id}]
                        }
                    file = service.files().insert(body=file_metadata,
                                                  fields='id').execute()
                    f_new_id = file.get('id')
                    os.setxattr(os.path.join(i['folder_path'], i['folder_name']), 'user.id',
                                str.encode(f_new_id))
        if os.path.isdir(path):
            if parent_id is None and is_local_sync is True:
                folder_create_for_upload(service, path, f_new_id, True, file_info, True, id_list)
            else:
                folder_create_for_upload(service, path, f_new_id, False, None, True, id_list)
        else:
            mime_type = None
            if parent_id is None and is_local_sync is True:
                set_id = True
                for i in file_info:
                    if i['id'] == f_id:
                        mime_type = i.get('mimeType')
                        break
            else:
                set_id = False
            elem = {
                'title': common_utils.get_file_name(path),
                'parent_id': f_new_id,
                'path': path,
                'mimeType': mime_type,
                'set_id': set_id
            }
            id_list.append(elem)
        if for_sync is False:
            try:
                service.files().trash(fileId=f_id).execute()
            except:
                return True
    except:
        return False


def folder_create_for_upload(service, path, parent_id, set_id, file_info, is_parent=True, id_list=None):
    if os.path.isdir(path):
        if is_parent is True:
            if parent_id is None:
                file_metadata = {
                    'title': common_utils.get_file_name(path),
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            else:
                file_metadata = {
                    'title': common_utils.get_file_name(path),
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [{'id': parent_id}]
                }
            file = service.files().insert(body=file_metadata,
                                          fields='id').execute()
            parent_id = file.get('id')
            if set_id is True:
                os.setxattr(path, 'user.id', str.encode(file.get('id')))
            is_parent = False
        if is_parent is False:
            for entry in os.scandir(path):
                if entry.is_dir():
                    if parent_id is None:
                        file_metadata = {
                            'title': common_utils.get_file_name(entry.path),
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                    else:
                        file_metadata = {
                            'title': common_utils.get_file_name(entry.path),
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [{'id': parent_id}]
                        }
                    file = service.files().insert(body=file_metadata,
                                                  fields='id').execute()
                    if set_id is True:
                        os.setxattr(entry.path, 'user.id', str.encode(file.get('id')))
                    folder_create_for_upload(service, entry.path, file.get('id'), set_id, file_info, is_parent, id_list)
                else:
                    mime_type = None
                    if set_id is True:
                        try:
                            f_id = os.getxattr(entry.path, 'user.id')
                            f_id = f_id.decode()
                        except:
                            f_id = None
                        if f_id is not None:
                            for i in file_info:
                                if i['id'] == f_id:
                                    mime_type = i.get('mimeType')
                                    break
                    elem = {
                        'title': common_utils.get_file_name(entry.path),
                        'parent_id': parent_id,
                        'path': entry.path,
                        'mimeType': mime_type,
                        'set_id': set_id
                    }
                    id_list.append(elem)
    else:
        return False


def get_file_info_for_sync(f_list, absolute_path, parents, parent_folder_id, file_info_list, folder_info_list):
    try:
        if absolute_path is None:
            absolute_path = config_utils.get_folder_sync_path()
        if parents is None:
            parents = []
        if file_info_list is None:
            file_info_list = []
        if folder_info_list is None:
            folder_info_list = []
        for i in f_list:
            try:
                if i['mimeType'] == 'application/vnd.google-apps.folder' and i['parents'][0]['id'] == parent_folder_id:
                    obj = {
                        "id": i['id'],
                        "name": i['title'],
                        "parent_folder_id": parent_folder_id,
                        "parents": [],
                        "absolute_path": absolute_path,
                        "modifiedDate": datetime.strptime(i['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                    }
                    obj["parents"].extend(parents)
                    folder_info_list.append(obj)
                    temp_path = os.path.join(absolute_path, i['title'])
                    parents.append({
                        "folder_name": i['title'],
                        "folder_id": i['id'],
                        "folder_path": absolute_path
                    })
                    parents_len = len(parents) - 1
                    get_file_info_for_sync(f_list, temp_path, parents, i['id'], file_info_list, folder_info_list)
                    for j in range(parents_len, len(parents)):
                        parents.pop(j)
                elif i['parents'][0]['id'] == parent_folder_id:
                    obj = {
                        "id": i['id'],
                        "name": i['title'],
                        "parent_folder_id": parent_folder_id,
                        "parents": [],
                        "absolute_path": absolute_path,
                        "mimeType": i.get('mimeType'),
                        "md5Checksum": i.get('md5Checksum'),
                        "modifiedDate": datetime.strptime(i['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                    }
                    obj["parents"].extend(parents)
                    file_info_list.append(obj)
            except:
                continue
        return file_info_list, folder_info_list
    except:
        return [], []


def get_folder_tree_for_sync(path, sub_path, parents):
    path = os.path.normpath(path)
    sub_path = os.path.normpath(sub_path)
    if parents is None:
        parents = []
    if path == sub_path:
        return
    for entry in os.scandir(path):
        if entry.is_dir() and entry.path in sub_path:
            try:
                f_id = os.getxattr(entry.path, 'user.id')
                f_id = f_id.decode()
            except:
                f_id = None
            parents.append({
                "folder_name": entry.name,
                "folder_id": f_id
            })
            get_folder_tree_for_sync(entry.path, sub_path, parents)
            break
    return parents


def get_file_info_in_local(path, is_root, parents, parent_folder_id, file_info_list, folder_info_list):
    try:
        if path is None:
            path = config_utils.get_folder_sync_path()
        if parents is None:
            parents = []
        if file_info_list is None:
            file_info_list = []
        if folder_info_list is None:
            folder_info_list = []
        if config_utils.get_folder_sync_path() in path and is_root is False:
            if os.path.normpath(config_utils.get_folder_sync_path()) != os.path.normpath(path):
                parents = get_folder_tree_for_sync(config_utils.get_folder_sync_path(), path, None)
            is_root = True
        obj = os.scandir(path)
        for entry in obj:
            try:
                f_id = os.getxattr(entry.path, 'user.id')
                f_id = f_id.decode()
            except:
                f_id = None
            if entry.is_dir():
                obj = {
                    "id": f_id,
                    "name": entry.name,
                    "parent_folder_id": parent_folder_id,
                    "parents": [],
                    "absolute_path": os.path.dirname(entry.path),
                    "modifiedDate": datetime.utcfromtimestamp(entry.stat().st_mtime).timestamp()
                }
                obj["parents"].extend(parents)
                folder_info_list.append(obj)
                parents.append({
                    "folder_name": entry.name,
                    "folder_id": f_id,
                    "folder_path": os.path.dirname(entry.path)
                })
                parents_len = len(parents) - 1
                get_file_info_in_local(entry.path, is_root, parents, f_id, file_info_list, folder_info_list)
                for j in range(parents_len, len(parents)):
                    parents.pop(j)
            elif entry.is_file():
                obj = {
                    "id": f_id,
                    "name": entry.name,
                    "parent_folder_id": parent_folder_id,
                    "parents": [],
                    "absolute_path": os.path.dirname(entry.path),
                    "md5Checksum": hashlib.md5(open(entry.path, 'rb').read()).hexdigest(),
                    "modifiedDate": datetime.utcfromtimestamp(entry.stat().st_mtime).timestamp()
                }
                obj["parents"].extend(parents)
                file_info_list.append(obj)
        return file_info_list, folder_info_list
    except:
        return [], []


def get_list_file_for_sync(service, local_path, option):
    if option == 'remote' or option == 'all':
        f_list = drive_services.get_raw_data(service, 'root', True)
        file_info = []
        folder_info = []
        for i in f_list:
            try:
                if i['parents'][0]['isRoot'] is True:
                    file_info, folder_info = get_file_info_for_sync(f_list, None, None, i['parents'][0]['id'], None,
                                                                    None)
                    break
            except:
                continue
        if option == 'remote':
            return file_info, folder_info
    file_info_local, folder_info_local = get_file_info_in_local(local_path, False, None, None, None, None)
    if option == 'local':
        return file_info_local, folder_info_local
    else:
        return file_info_local, folder_info_local, file_info, folder_info


def f_sync(service, local_path):
    if local_path is None:
        local_path = config_utils.get_folder_sync_path()
    id_list = []
    file_info_local, folder_info_local, file_info, folder_info = get_list_file_for_sync(service, local_path, 'all')
    change_list = None
    for i in file_info_local:
        check_file = None
        if i['id'] is not None:
            path = drive_services.filter_trash(service, i['id'], config_utils.get_folder_sync_path())
            if path is not None:
                if os.path.normpath(i['absolute_path']) != os.path.normpath(path):
                    check_file = False
                else:
                    check_file = True
        if check_file is None:
            uploader(service, '-u', os.path.join(i['absolute_path'], i['name']), None, False, id_list)
            with ThreadPoolExecutor(5) as executor:
                executor.map(drive_services.upload, id_list)
            id_list.clear()
        check_id_exist = False
        if check_file is True:
            if file_info is not None:
                for file in file_info:
                    if file['id'] == i['id']:
                        check_id_exist = True
                        if file['modifiedDate'] > i['modifiedDate']:
                            os.remove(os.path.join(i['absolute_path'], i['name']))
                            save_location = drive_services.filter_trash(service, file['id'],
                                                                        config_utils.get_folder_sync_path())
                            downloader(service, '-d', file['id'], save_location, id_list)
                            with ThreadPoolExecutor(5) as executor:
                                executor.map(drive_services.download, id_list)
                            id_list.clear()
                        else:
                            if file['modifiedDate'] == i['modifiedDate']:
                                with open(common_utils.format_dict) as f:
                                    format_add = json.load(f)
                                check_type = format_add.get(file.get('mimeType'))
                                if check_type is not None:
                                    file_name = os.path.splitext(i['name'])[0]
                                else:
                                    file_name = i['name']
                                if file['name'] != file_name:
                                    drive_services.update_file(service, file['id'],
                                                               os.path.join(i['absolute_path'], i['name']),
                                                               False)
                            else:
                                drive_services.update_file(service, file['id'],
                                                           os.path.join(i['absolute_path'], i['name']),
                                                           True)
                        break
            if check_id_exist is False:
                uploader(service, '-u', os.path.join(i['absolute_path'], i['name']), None, False, id_list)
                with ThreadPoolExecutor(5) as executor:
                    executor.map(drive_services.upload, id_list)
                id_list.clear()
        if check_file is False:
            last_edit = None
            for file in file_info:
                if file['id'] == i['id']:
                    if file['modifiedDate'] > i['modifiedDate']:
                        last_edit = 'remote'
                    else:
                        if i['modifiedDate'] > file['modifiedDate']:
                            last_edit = 'local'
                        else:
                            last_edit = True
                    break
            if last_edit is True:
                stat = os.stat(os.path.join(i['absolute_path'], i['name']))
                if change_list is None:
                    change_list = drive_services.retrieve_all_changes(service, None)
                for j in change_list:
                    if j['id'] == i['id']:
                        if datetime.utcfromtimestamp(stat.st_ctime).timestamp() > j['c_time']:
                            last_edit = 'local'
                        else:
                            last_edit = 'remote'
                        break
            if last_edit == 'remote':
                os.remove(os.path.join(i['absolute_path'], i['name']))
                save_location = drive_services.filter_trash(service, i['id'], config_utils.get_folder_sync_path())
                downloader(service, '-d', i['id'], save_location, id_list)
                with ThreadPoolExecutor(5) as executor:
                    executor.map(drive_services.download, id_list)
                id_list.clear()
            elif last_edit == 'local':
                uploader(service, '-u', os.path.join(i['absolute_path'], i['name']), None, True, id_list)
                for file in id_list:
                    drive_services.move_file_remote(service, i['id'], file['parent_id'],
                                                    os.path.join(os.path.join(i['absolute_path'], i['name'])))
                id_list.clear()
            if last_edit is None:
                uploader(service, '-u', os.path.join(i['absolute_path'], i['name']), None, False, id_list)
                with ThreadPoolExecutor(5) as executor:
                    executor.map(drive_services.upload, id_list)
                id_list.clear()
    clean_folder_empty(service, local_path, True)
    return True


def clean_folder_empty(service, path, is_root=True):
    if os.path.isdir(path):
        i = 0
        for entry in os.scandir(path):
            i += 1
            if entry.is_dir():
                clean_folder_empty(service, entry.path, False)
        if i == 0 and is_root is False:
            try:
                f_id = os.getxattr(path, 'user.id')
                f_id = f_id.decode()
            except:
                f_id = None
            if f_id is not None:
                """
                Need to check if the folder on the remote is empty.
                ERROR:
                When you move the folder on the remote and then run the sync, the folder on the remote will be deleted.
                """
                try:
                    f_list = drive_services.get_raw_data(service, f_id, False)
                    if len(f_list) == 0:
                        service.files().delete(fileId=f_id).execute()
                except:
                    return
                shutil.rmtree(path)


def f_exclusive(path, options):
    if options is True:
        path = os.path.join(os.path.expanduser(Path().resolve()), path)
        if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
            return False
        # Traversing inside files/folders
        if os.path.isdir(path):
            os.setxattr(path, 'user.excludeUpload', str.encode('True'))
            for item in os.scandir(path):
                f_exclusive(item.path, options)
        else:
            os.setxattr(path, 'user.excludeUpload', str.encode('True'))
        print("Exclude Upload Success")
    else:
        path = os.path.join(os.path.expanduser(Path().resolve()), path)
        if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
            return False
        # Traversing inside files/folders
        if os.path.isdir(path):
            os.setxattr(path, 'user.excludeUpload', str.encode('False'))
            for item in os.scandir(path):
                f_exclusive(item.path, options)
        else:
            os.setxattr(path, 'user.excludeUpload', str.encode('False'))
        print("UnExclude Upload Success")


def sharer(service, option, instance_id, mail):
    try:
        permissions = service.permissions().list(fileId=instance_id).execute()
        list_permissions = permissions.get('items', [])
        print(list_permissions)
        result = None

        unshared = False
        already_have = False
        role = None
        if common_utils.check_option(option, 'r', 3) or common_utils.check_option(option, 's', 2):
            role = "reader"
        elif common_utils.check_option(option, 'w', 3):
            role = "writer"
        elif common_utils.check_option(option, 'u', 3):
            unshared = True
        else:
            print("Permission is not valid. Try again")
            return

        for elem in list_permissions:
            # if elem.get('emailAddress') == mail:
            if 'emailAddress' in elem and elem.get('emailAddress').lower() == mail.lower():
                already_have = True
                if elem.get('role') != 'owner':
                    if unshared is False:
                        elem['role'] = role
                        try:
                            result = service.permissions().update(
                                fileId=instance_id, permissionId=elem['id'], body=elem).execute()
                        except:
                            print('An error occurred !')
                    else:
                        try:
                            service.permissions().delete(
                                fileId=instance_id, permissionId=elem['id']).execute()
                            print("Unshare successfully !")
                        except:
                            print('An error occurred !')
                else:
                    print('Failed! \nYou are the owner of this file (folder) !')

            if elem['id'] == 'anyone' and len(mail) == 0 and unshared:
                try:
                    service.permissions().delete(
                        fileId=instance_id, permissionId=elem['id']).execute()
                    print("Unshare successfully !")
                except:
                    print('An error occurred !')

        if unshared and mail == 'all':
            for elem in list_permissions:
                if elem.get('role') != 'owner':
                    service.permissions().delete(
                        fileId=instance_id, permissionId=elem['id']).execute()

        if not already_have and not unshared:
            if len(mail) == 0:
                new_permission = {
                    'type': 'anyone',
                    'value': 'anyone',
                    'role': role
                }
            else:
                new_permission = {
                    'type': 'user',
                    'value': mail,
                    'role': role
                }
            try:
                result = service.permissions().insert(
                    fileId=instance_id, body=new_permission).execute()
            except:
                print('An error occurred !')

        if result is not None:
            instance = service.files().get(fileId=instance_id,
                                           fields='alternateLink').execute()
            print("Share link copied to clipboard!")
            pyperclip.copy(instance['alternateLink'])
            mess = pyperclip.paste()
            print(mess)

    except:
        print("%s is an invalid id!" % instance_id)

    return None


def f_remove(drive, mode, paths):
    if mode == "local":
        sync_dir = config_utils.get_folder_sync_path()
        # Appending file/folder name to download directory
        for path in paths:
            path = os.path.join(os.path.expanduser(Path().resolve()), path)
            if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
                return False
            if not os.path.exists(path):
                print("%s doesn't exist in %s" % (path, sync_dir))
            else:
                # use recursive removal if directory
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print("%s removed from %s" % (path, sync_dir))
        return True

    elif mode == "remote":
        for id in paths:
            # check if file_id valid
            if is_valid_id(drive, id):
                # file to be removed
                r_file = drive.CreateFile({'id': id})
                f_name = r_file['title']
                # delete permanently if in trash
                if is_trash(drive, r_file['id']):
                    r_file.Delete()
                    print("%s deleted permanently" % f_name)
                # move to trash
                else:
                    r_file.Trash()
                    print("%s moved to GDrive trash. List files in trash by -lt parameter" % f_name)
        return True

    elif mode == "all":
        sync_dir = config_utils.get_folder_sync_path()
        for path in paths:
            check_path = True
            f_path = os.path.join(os.path.expanduser(Path().resolve()), path)
            if f_path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
                check_path = False
            if os.path.exists(f_path) and check_path is True:
                try:
                    f_id = os.getxattr(f_path, 'user.id')
                    f_id = f_id.decode()
                    if is_valid_id(drive, f_id):
                        # file to be removed
                        r_file = drive.CreateFile({'id': f_id})
                        f_name = r_file['title']
                        # delete permanently if in trash
                        if is_trash(drive, r_file['id']):
                            r_file.Delete()
                            print("%s deleted permanently" % f_name)
                        # move to trash
                        else:
                            r_file.Trash()
                            print("%s moved to GDrive trash. List files in trash by -lt parameter" % f_name)
                except:
                    print
                # use recursive removal if directory
                if os.path.isdir(f_path):
                    shutil.rmtree(f_path)
                else:
                    os.remove(f_path)
                print("%s removed from %s" % (f_path, sync_dir))
                return True
            # check if file_id valid
            list_local, local_folders = f_list_local(sync_dir, True)
            for i in local_folders:
                list_local.append(i)
            if is_valid_id(drive, path):
                # file to be removed
                r_file = drive.CreateFile({'id': path})
                f_name = r_file['title']
                # delete permanently if in trash
                if is_trash(drive, r_file['id']):
                    r_file.Delete()
                    print("%s deleted permanently" % f_name)
                # move to trash
                else:
                    r_file.Trash()
                    print("%s moved to GDrive trash. List files in trash by -lt parameter" % f_name)
            for x in list_local:
                if x['id'] == path:
                    f_path = x['canonicalPath']
                    # use recursive removal if directory
                    if os.path.isdir(f_path):
                        shutil.rmtree(f_path)
                    else:
                        os.remove(f_path)
                        print("%s removed from %s" % (f_path, sync_dir))
        return True

    else:
        print("%s is not a valid mode" % mode)
        return False


def get_info(service, option, instance):
    result_local = None
    result_remote = None

    local_files, sub_folders = f_list_local(config_utils.get_folder_sync_path(), True)

    path_err = False
    default_opt = False

    instance_id = None
    if common_utils.check_option(option, 'i', 2):
        default_opt = True
        path = os.path.join(os.path.expanduser(Path().resolve()), instance)
        if os.path.exists(path) and path.startswith(config_utils.get_folder_sync_path() + os.sep):
            flag = False
            for file in local_files:
                if path == file['canonicalPath']:
                    flag = True
                    instance_id = file['id']
                    if instance_id is None:
                        result_local = file
            if not flag:
                for folder in sub_folders:
                    if path == folder['canonicalPath']:
                        instance_id = folder['id']
                        if instance_id is None:
                            result_local = folder
        else:
            path_err = True
            print('%s is invalid path !' % path)

    elif common_utils.check_option(option, 'f', 3):
        instance_id = instance
    else:
        print(str(option) + " is an unrecognised argument. Please report if you know this is an error .\n\n")

    if instance_id is not None:
        try:
            fields = 'id, title, alternateLink, parents, userPermission, permissions, ' \
                     'shared, ownedByMe, md5Checksum, fileSize, mimeType, createdDate, modifiedDate'
            remote_file = service.files().get(fileId=instance_id,
                                              fields=fields).execute()

            permissions = remote_file.get('permissions')
            instance_parent = remote_file.get('parents')[0]['id']
            # print(instance_parent)
            rel_path = []
            all_folders = drive_services.get_all_remote_folder(service)
            drive_services.get_cloud_path(all_folders, instance_parent, rel_path)
            remote_path = os.sep
            for elem in rel_path:
                # print(elem)
                remote_path += elem.get('name') + os.sep
            result_remote = {
                'storageLocation': 'remote',
                'id': remote_file.get('id'),
                'title': remote_file.get('title'),
                'alternateLink': remote_file.get('alternateLink'),
                'parents': remote_file.get('parents'),
                'userPermission': [],
                'shared': remote_file.get('shared'),
                'ownedByMe': remote_file.get('ownedByMe'),
                'md5Checksum': remote_file.get('md5Checksum'),
                'fileSize': remote_file.get('fileSize'),
                'mimeType': remote_file.get('mimeType'),
                'createdDate': common_utils.utc2local(
                    datetime.strptime(remote_file['createdDate'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(microsecond=0)),
                'modifiedDate': common_utils.utc2local(
                    datetime.strptime(remote_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(microsecond=0)),
                'remotePath': remote_path
            }
            for elem in permissions:
                result_remote.get('userPermission').append({
                    "id": elem.get('id'),
                    "name": elem.get('name'),
                    "emailAddress": elem.get('emailAddress'),
                    "role": elem.get('role'),
                })

            flag = False
            for file in local_files:
                if instance_id == file['id']:
                    flag = True
                    result_local = file
            if not flag:
                for folder in sub_folders:
                    if instance_id == folder['id']:
                        result_local = folder
        except:
            print('%s is an invalid parameter !' % instance)

    else:
        if not path_err and not default_opt:
            print('%s is invalid !' % instance)

    # print(result_local)
    # print("=====")
    # print(result_remote)
    # print("=====")
    # print(Path().resolve())

    return result_local, result_remote


def file_restore(drive, addr_list):
    for addr in addr_list:
        # check if file_id valid
        if is_valid_id(drive, addr):
            # file to be removed
            r_file = drive.CreateFile({'id': addr})
            f_name = r_file['title']
            # if in trash then restore
            if is_trash(drive, r_file['id']):
                r_file.UnTrash()
                print("%s is restored" % f_name)
            # else done nothing
            else:
                print("%s is not trash" % f_name)
                return


def is_valid_id(drive, file_id):
    try:
        file_check = drive.CreateFile({'id': file_id})
        file_check.FetchMetadata()
    except:
        # print("%s is an invalid file_id!" % file_id)
        return False
    return True


def is_trash(drive, file_id):
    # for f in drive.ListFile({'q': "'root' in parents and trashed=true"}).GetList():
    for f in drive.ListFile({'q': "trashed=true"}).GetList():
        if file_id == f['id']:
            return True
    return False


def f_list_local(folder, recursive):
    """List all files and folders in the sync directory

        :param folder: Canonical path of folder
        :param recursive: True if recursive and and vice versa

        :returns: List of files with information
    """

    files_info = []
    folders_info = []
    if recursive:
        sub_folders, local_files = common_utils.run_fast_scandir(folder)
        for file in local_files:
            stats = os.stat(file)
            try:
                instance_id = os.getxattr(os.path.join(folder, file), 'user.id').decode()
            except:
                instance_id = None

            try:
                exclude_upload = os.getxattr(os.path.join(folder, file), 'user.excludeUpload').decode()
            except:
                exclude_upload = None

            result = {
                'storageLocation': 'local',
                'id': instance_id,
                'title': common_utils.get_file_name(file),
                'canonicalPath': file,
                'modifiedDate': stats.st_mtime,
                'md5Checksum': hashlib.md5(open(file, 'rb').read()).hexdigest(),
                'excludeUpload': exclude_upload,
                'fileSize': stats.st_size,
                'typeShow': None
            }
            files_info.append(result)

        for elem in sub_folders:
            try:
                instance_id = os.getxattr(elem, 'user.id').decode()
            except:
                instance_id = None

            try:
                exclude_upload = os.getxattr(elem, 'user.excludeUpload').decode()
            except:
                exclude_upload = None

            stats = os.stat(elem)

            result = {
                'storageLocation': 'local',
                'id': instance_id,
                'title': os.path.basename(elem),
                'canonicalPath': elem,
                'modifiedDate': stats.st_mtime,
                'excludeUpload': exclude_upload,
                'folderSize': common_utils.get_folder_size(elem)
            }
            folders_info.append(result)

        return files_info, folders_info
    else:
        # for file in os.listdir(folder):
        for file in os.scandir(folder):
            # print(file)
            stats = os.stat(file.path)

            try:
                instance_id = os.getxattr(os.path.join(folder, file), 'user.id').decode()
            except:
                instance_id = None

            result = {
                'storageLocation': 'local',
                'id': instance_id,
                'title': common_utils.get_file_name(file),
                'canonicalPath': file,
                'modifiedDate': stats.st_mtime,
                'md5Checksum': hashlib.md5(open(file.path, 'rb').read()).hexdigest() if file.is_file() else None,
                'excludeUpload': False,
                'fileSize': stats.st_size,
                'typeShow': None,
                'type': 'folder' if file.is_dir() else 'file'
            }
            files_info.append(result)

        try:
            instance_id = os.getxattr(folder, 'user.id').decode()
        except:
            instance_id = None

        try:
            exclude_upload = os.getxattr(folder, 'user.excludeUpload').decode()
        except:
            exclude_upload = None

        stats = os.stat(folder)

        folder_info = {
            'storageLocation': 'local',
            'id': instance_id,
            'title': os.path.basename(folder),
            'canonicalPath': folder,
            'modifiedDate': stats.st_mtime,
            'excludeUpload': exclude_upload,
            'folderSize': common_utils.get_folder_size(folder)
        }
        folders_info.append(folder_info)

        return files_info, folders_info


def get_list_folders(drive, keyword):
    folder_list = []
    file_list = []
    instance = None
    check = False
    if keyword == 'root':
        check = True
        instance = keyword
    elif is_valid_id(drive, keyword):
        folder = drive.CreateFile({'id': keyword})
        folder.FetchMetadata(fetch_all=True)
        if folder['mimeType'] == 'application/vnd.google-apps.folder':
            check = True
            instance = keyword
    if check:
        q_string = "'%s' in parents and trashed=false" % instance
        for f in drive.ListFile({'q': q_string}).GetList():
            # if file in list is folder, get it's file list
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                # print(f['title'])
                folder_list.append(f)
                # f_all(drive, f['id'], file_list, False, None, None, folder_list)
            else:
                file_list.append(f)

    results = []
    for elem in folder_list:
        result = {
            'storageLocation': 'remote',
            'id': elem['id'],
            'title': elem['title'],
            'modifiedDate': datetime.timestamp(datetime.strptime(elem['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
            'md5Checksum': elem.get('md5Checksum'),
            'mimeType': elem['mimeType'],
            'fileSize': elem.get('fileSize') if elem.get('fileSize') else None,
        }
        results.append(result)

    return results


# Operations for file list commands
def get_all_data(service, keyword, recursive):
    # get recursively all files in the folder
    if recursive:
        raw_data = drive_services.get_raw_data(service, keyword, True)

    # lists all files and folder inside given folder
    else:
        raw_data = drive_services.get_raw_data(service, keyword, False)

    result = []
    for elem in raw_data:
        item = {
            'storageLocation': 'remote',
            'id': elem['id'],
            'alternateLink': elem.get('alternateLink'),
            'title': elem['title'],
            'modifiedDate': datetime.timestamp(datetime.strptime(elem['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
            'parents': elem.get('parents'),
            'shared': elem.get('shared'),
            'md5Checksum': elem.get('md5Checksum'),
            'mimeType': elem['mimeType'],
            'fileSize': elem.get('fileSize')
        }
        result.append(item)

    return result


def f_open(folder):
    os.system('xdg-open "%s"' % config_utils.get_folder_sync_path())


def get_tree_folder(service):
    files_local, folders_local, files, folders = get_list_file_for_sync(service, config_utils.get_folder_sync_path(),
                                                                        "all")
    # print(files_local)
    # print(folders_local)
    # print("----")
    # print(files)
    # print(folders)
    root = tree.newNode({"id": None, "name": "root"})

    for folder in folders:
        tmp_folder = {"id": folder["id"], "name": folder["name"], 'type': 'folder'}
        if folder['parents'] == []:
            tree.add_node(root, {"id": None, "name": "root"}, tmp_folder)
        else:
            parents_key = {"id": folder["parents"][-1]["folder_id"], "name": folder["parents"][-1]["folder_name"]}

            tree.add_node(root, parents_key, tmp_folder)

    for file in files:
        tmp_file = {"id": file["id"], "name": file["name"], 'type': 'file'}
        if file['parents'] == []:
            tree.add_node(root, {"id": None, "name": "root"}, tmp_file)
        else:
            parents_key = {"id": file["parents"][-1]["folder_id"], "name": file["parents"][-1]["folder_name"]}
            tree.add_node(root, parents_key, tmp_file)

    for folder in folders_local:
        tmp_folder = {"id": folder["id"], "name": folder["name"], 'type': 'folder',
                      'canonicalPath': folder['absolute_path'] + "/" + folder['name']}
        if folder['parents'] == []:
            tree.add_node(root, {"id": None, "name": "root"}, tmp_folder)
        else:
            parents_key = {"id": folder["parents"][-1]["folder_id"], "name": folder["parents"][-1]["folder_name"]}

            tree.add_node(root, parents_key, tmp_folder)

    for file in files_local:
        tmp_file = {"id": file["id"], "name": file["name"], "type": 'file',
                    'canonicalPath': folder['absolute_path'] + "/" + folder['name']}
        if file['parents'] == []:
            tree.add_node(root, {"id": None, "name": "root"}, tmp_file)
        else:
            parents_key = {"id": file["parents"][-1]["folder_id"], "name": file["parents"][-1]["folder_name"]}
            tree.add_node(root, parents_key, tmp_file)
    return root


def check_remote_dir_files_sync(service, remote_folder_id, local_folder):
    remote_list = get_all_data(service, remote_folder_id, True)
    remote_sub_direct_files_list = list(filter(lambda e: (not re.compile('folder', re.IGNORECASE).search(
        e.get('mimeType'))) and common_utils.is_parents_folder(remote_folder_id, e['parents']), remote_list))
    remote_sub_direct_folders_list = list(filter(
        lambda e: (re.compile('folder', re.IGNORECASE).search(e.get('mimeType'))) and common_utils.is_parents_folder(
            remote_folder_id, e['parents']), remote_list))

    local_files_list, local_folders_list = f_list_local(local_folder, True)
    local_sub_direct_files_list = list(
        filter(lambda e: e['canonicalPath'] == os.path.join(local_folder, e['title']), local_files_list))
    local_sub_direct_folders_list = list(
        filter(lambda e: e['canonicalPath'] == os.path.join(local_folder, e['title']), local_folders_list))
    # print(remote_sub_direct_folders_list)
    # print("--")
    # print(local_sub_direct_folders_list)
    # print("--")
    # print(remote_sub_direct_files_list)
    # print("--")
    # print(local_sub_direct_files_list)

    count = 0
    for remote_file in remote_sub_direct_files_list:
        for local_file in local_sub_direct_files_list:
            if remote_file['id'] == local_file['id']:
                if remote_file['md5Checksum']:
                    if remote_file['md5Checksum'] == local_file['md5Checksum']:
                        count += 1
                        break
                elif remote_file['fileSize'] == remote_file['fileSize']:
                    count += 1
                    break
    count2 = 0
    for remote_folder in remote_sub_direct_folders_list:
        for local_folder in local_sub_direct_folders_list:
            if remote_folder['id'] == local_folder['id']:
                if check_remote_dir_files_sync(service, remote_folder['id'], local_folder['canonicalPath']):
                    count2 += 1
                    break
    if count == max(len(remote_sub_direct_files_list), len(local_sub_direct_files_list)) and count2 == max(
            len(remote_sub_direct_folders_list), len(local_sub_direct_folders_list)):
        return True
    else:
        return False


def compare_and_change_type_show(service, remote_files_list, local_files_list):
    for remote_file in remote_files_list:
        for local_file in local_files_list:
            if remote_file['id'] == local_file['id']:
                if not re.compile('folder', re.IGNORECASE).search(remote_file.get('mimeType')):
                    if remote_file['md5Checksum']:
                        if remote_file['md5Checksum'] == local_file['md5Checksum']:
                            remote_file['typeShow'] = "dongbo"
                        else:
                            remote_file['typeShow'] = "notdongbo"
                    else:
                        if remote_file['fileSize'] == local_file['fileSize']:
                            remote_file['typeShow'] = "dongbo"
                else:
                    if check_remote_dir_files_sync(service, remote_file['id'], local_file['canonicalPath']):
                        remote_file['typeShow'] = "dongbo"
                    else:
                        remote_file['typeShow'] = "notdongbo"
                # list_print.append(remote_file)
                break
        if remote_file.get('typeShow') is None:
            remote_file['typeShow'] = "dammay"


def compare_and_change_type_show_local(service, local_files_list, remote_files_list):
    for local_file in local_files_list:
        for remote_file in remote_files_list:
            if local_file['id'] == remote_file['id']:
                if 'type' in local_file and re.compile('folder', re.IGNORECASE).search(local_file['type']):
                    if check_remote_dir_files_sync(service, remote_file['id'], local_file['canonicalPath']):
                        local_file['typeShow'] = "dongbo"
                    else:
                        local_file['typeShow'] = "notdongbo"
                else:
                    if local_file['md5Checksum']:
                        if local_file['md5Checksum'] == remote_file['md5Checksum']:
                            local_file['typeShow'] = "dongbo"
                        else:
                            local_file['typeShow'] = "notdongbo"
                    else:
                        if local_file['fileSize'] == remote_file['fileSize']:
                            local_file['typeShow'] = "dongbo"
                break
        if local_file['typeShow'] == None: local_file['typeShow'] = "maytinh"


def get_direct_folders_remote(service, keyword):
    root_remote_files_list = get_all_data(service, keyword, 0)
    return list(filter(lambda e: e['mimeType'] == "application/vnd.google-apps.folder"))


def get_direct_files_remote(service, keyword):
    root_remote_files_list = get_all_data(service, keyword, 0)
    return list(filter(lambda e: e['mimeType'] != "application/vnd.google-apps.folder"))


def show_folder(service, folder_id):
    table = PrettyTable()
    table.field_names = ['Name', 'Id', 'Status', 'Date Modified', 'Type', 'Size']
    is_print = False

    remote_files_list = []
    if (folder_id):
        remote_files_list = get_all_data(service, folder_id, 0)
    else:
        return
    root_files_list, root_folders_list = f_list_local(config_utils.get_folder_sync_path(), True)

    if folder_id == 'root':
        x = []
        tmp = {'canonicalPath': config_utils.get_folder_sync_path()}
        x.append(tmp)
    else:
        x = list(filter(lambda e: e['id'] == folder_id, root_folders_list))

    if (len(remote_files_list) > 0):
        if len(x) > 0:
            local_folder = x[0]
            local_files_list, local_folders_list = f_list_local(local_folder['canonicalPath'], False)
            # print(remote_files_list)
            # print(local_files_list)
            compare_and_change_type_show(service, remote_files_list, local_files_list)

            result = filter_local_only(local_files_list, remote_files_list)
            for file in result:
                table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'],
                               file['id'] if file['id'] else '', common_utils.renderTypeShow(file['typeShow']),
                               datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'],
                               common_utils.sizeof_fmt(common_utils.getFileSize(file))])

        else:
            for file in remote_files_list:
                file['typeShow'] = 'dammay'

        for file in remote_files_list:
            table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                           common_utils.renderTypeShow(file['typeShow']),
                           common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime(
                               "%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1],
                           common_utils.sizeof_fmt(common_utils.getFileSize(file))])
        is_print = True
    else:  # truong hop ko co tren remote
        if len(x) > 0:  # neu co tren local
            local_folder = x[0]
            local_files_list, local_folders_list = f_list_local(local_folder['canonicalPath'], False)

            for file in local_files_list:
                file['typeShow'] = 'maytinh'
                table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'],
                               file['id'] if file['id'] else '', common_utils.renderTypeShow(file['typeShow']),
                               datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"), file['type'],
                               common_utils.sizeof_fmt(common_utils.getFileSize(file))])
            is_print = True
    if is_print:
        table.align = "l"
        print(table)


def show_folder_recusive(service, folder_id, folder_name, root_node):
    sub_node = tree.get_direct_sub_node(root_node,
                                        {"id": folder_id, "name": folder_name} if folder_name else {"id": folder_id})
    if not sub_node:
        return
    print(folder_name)
    if (folder_id == None and folder_name == 'root'):
        show_folder(service, 'root')
    else:
        show_folder(service, folder_id)

    for node in sub_node:
        if node.key['type'] == 'folder':
            show_folder_recusive(service, node.key['id'], node.key['name'], root_node)


def show_folder_by_path(service, folder_path):
    table = PrettyTable()
    table.field_names = ['Name', 'Id', 'Status', 'Date Modified', 'Type', 'Size']
    is_print = False

    try:
        local_files_list, local_folders_list = f_list_local(folder_path, False)

        if (folder_path == config_utils.get_folder_sync_path()):
            x = []
            x.append({'id': 'root'})
        else:
            root_files_list, root_folders_list = f_list_local(config_utils.get_folder_sync_path(), True)
            x = list(filter(lambda e: e['canonicalPath'] == folder_path, root_folders_list))
        if len(x) > 0:
            remote_folder = x[0]
            remote_files_list = get_all_data(service, remote_folder['id'], False)

            compare_and_change_type_show_local(service, local_files_list, remote_files_list)

            result = filter_remote_only(remote_files_list, local_files_list)

            for file in result:
                table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                               common_utils.renderTypeShow(file['typeShow']),
                               common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])).strftime(
                                   "%m/%d/%Y %H:%M"), file['mimeType'].split(".")[-1],
                               common_utils.sizeof_fmt(common_utils.getFileSize(file))])

            for file in local_files_list:
                table.add_row([(file['title'][:37] + "...") if len(file["title"]) > 37 else file['title'], file['id'],
                               common_utils.renderTypeShow(file['typeShow']),
                               datetime.fromtimestamp(file['modifiedDate']).strftime("%m/%d/%Y %H:%M"),
                               file['type'] if 'type' in file else "file",
                               common_utils.sizeof_fmt(common_utils.getFileSize(file))])
            is_print = True
        else:
            for file in local_files_list:
                file['typeShow'] = 'maytinh'

    except FileNotFoundError as error:
        print(error)
        is_print = False

    if is_print:
        table.align = "l"
        print(table)


def show_folder_recusive_by_path(service, path, root_node):
    # tree.LevelOrderTraversal(root_node)
    if path == config_utils.get_folder_sync_path():
        show_folder_recusive(service, None, "root", root_node)
    else:
        node = tree.find_node_by_canonicalPath(root_node, path)
        if node == None:
            print('%s is invalid !' % (path))
        elif node.key['type'] == 'file':
            print('%s is path of file ,not path of folder!')
        else:
            folder_id = node.key['id']
            folder_name = node.key['name']
            print(folder_id)
            print(folder_name)
            show_folder_recusive(service, folder_id, folder_name, root_node)


def filter_local_only(local_files_list, remote_files_list):
    result = []
    for local_file in local_files_list:
        if not local_file['id']:
            local_file['typeShow'] = 'maytinh'
            result.append(local_file)
        else:
            x = list(filter(lambda e: e['id'] == local_file['id'], remote_files_list))
            if len(x) == 0:
                local_file['typeShow'] = 'maytinh'
                result.append(local_file)
    return result


def filter_remote_only(remotes_list, local_files_list):
    result = []
    for remote in remotes_list:
        x = list(filter(lambda e: e['id'] == remote['id'], local_files_list))
        if len(x) == 0:
            remote['typeShow'] = 'dammay'
            result.append(remote)
    return result


def f_calculate_usage_of_folder(service):
    drive_audio_usage = 0
    drive_photo_usage = 0
    drive_movies_usage = 0
    drive_document_usage = 0
    drive_others_usage = 0

    # file_list = get_all_data(service, 'root', True)
    lists = get_all_data(service, "root", True)
    files_list = list(filter(lambda e: not e['mimeType'] == "application/vnd.google-apps.folder", lists))

    for file in files_list:
        if common_utils.isAudioFile(file):
            drive_audio_usage += common_utils.getFileSize(file)
        elif common_utils.isImageFile(file):
            drive_photo_usage += common_utils.getFileSize(file)
        elif common_utils.isVideoFile(file):
            drive_movies_usage += common_utils.getFileSize(file)
        elif common_utils.isDocument(file):
            drive_document_usage += common_utils.getFileSize(file)
        else:
            drive_others_usage += common_utils.getFileSize(file)
    return drive_audio_usage, drive_photo_usage, drive_movies_usage, drive_document_usage, drive_others_usage
