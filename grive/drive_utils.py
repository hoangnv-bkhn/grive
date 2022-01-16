import threading
from builtins import str
import json
import os
import sys
import shutil
from pathlib import Path

import pyperclip
import hashlib
import re

from datetime import datetime

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
    import drive_services
except ImportError:
    from . import common_utils
    from . import config_utils
    from . import drive_services


def f_all(drive, fold_id, file_list, download, sync_folder, option, folder_list):
    """Recursively download or just list files in folder

        :param drive: Google Drive instance
        :param fold_id: id of folder to search
        :param file_list: initial list to store list of file when search
        :param download: True if downloads, False if just recursively list file
        :param sync_folder: folder to store when download
        :param option: option download (overwrite or not)
        :param folder_list: initial list to store list of folder when search

        :returns: List of file store in file_list param
    """

    q_string = "'%s' in parents and trashed=false" % fold_id
    for f in drive.ListFile({'q': q_string}).GetList():
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            # print(f['title'])
            if download:  # if we are to download the files
                save_location = os.path.join(sync_folder, f['title'])
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(sync_folder, os.path.basename(sync_folder))

                common_utils.dir_exists(save_location)
                os.setxattr(save_location, 'user.id', str.encode(f['id']))

                stats = os.stat(save_location)
                os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                    datetime.strptime(f['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

                f_all(drive, f['id'], None, True, save_location, option, folder_list)

            else:  # we want to just list the files
                # print(f['title'])
                folder_list.append(f)
                f_all(drive, f['id'], file_list, False, None, None, folder_list)
        else:
            if download:
                downloader(drive, option, f['id'], sync_folder)
            else:
                file_list.append(f)


def downloader(service, option, instance_id, save_folder):
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

        # checking if the specified id belongs to a folder
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
                        print(" Recreating folder %s in %s" % (remote_name, save_folder))
                else:
                    flag = False
                    print(" Folder '%s' already present in %s" % (instance['title'], save_folder))
            else:
                print(" Creating folder %s in %s" % (remote_name, save_folder))

            if flag:
                save_location = folder_path
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(save_folder, os.path.basename(folder_path))

                common_utils.dir_exists(save_location)
                os.setxattr(save_location, 'user.id', str.encode(remote_id))

                stats = os.stat(save_location)
                os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                    datetime.strptime(instance['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

                # f_all(drive, remote_id, None, True, save_location, option, [])
                file_contained = drive_services.get_files_in_folder(service, instance_id)
                for item in file_contained:
                    location = drive_services.get_local_path(service, item.get('id'), config_utils.get_folder_sync_path())
                    downloader(service, option, item.get('id'), location)

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
                downloaded = False
                save_location = os.path.join(save_folder, file_local_name)
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(save_folder, file_local_name)
                print("Download '%s' in '%s'" % (instance.get('title'), save_location))
                if is_workspace_document:
                    if drive_services.download(service, instance.get('id'), instance.get('title'),
                                               save_location, mime_swap[instance['mimeType']]):
                        downloaded = True
                    else:
                        # print("Download '%s' with id - '%s' failed !" % (file.get('title'), file_id))
                        return False
                else:
                    if drive_services.download(service, instance.get('id'), instance.get('title'), save_location):
                        downloaded = True
                    else:
                        # print("Download '%s' with id - '%s' failed !" % (file.get('title'), file_id))
                        return False
                if downloaded:
                    os.setxattr(save_location, 'user.id', str.encode(remote_id))
                    stats = os.stat(save_location)
                    os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                        datetime.strptime(instance['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
                    return True
    except:
        # print(" %s is an invalid id !" % file_id)
        return False


def f_create(drive, addr, fold_id, rel_addr, list_f, overwrite, isSync, show_update):
    # Check whether address is right or not
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, check the address!")
        return

    if isSync is True and overwrite is False and list_f is None:
        list_f = get_all_data(drive, "root", True)
        list_fold = get_list_folders(drive, "root")
        for i in list_fold:
            list_f.append(i)

    check_old_id = True

    if list_f is not None:
        if len(list_f) > 0:
            try:
                c_id = os.getxattr(addr, 'user.id')
                c_id = c_id.decode()
                for i in list_f:
                    if i['id'] == c_id:
                        check_old_id = False
                        break
            except:
                check_old_id = False

    # creating if it's a folder
    if os.path.isdir(addr):
        sync_dir = config_utils.get_folder_sync_path()
        # print progress
        if show_update:
            print("creating folder " + rel_addr)
        check_id = False
        if os.path.join(addr) == os.path.join(sync_dir) and fold_id is None and isSync is True:
            is_root_folder = True
            folder = drive.CreateFile()
            folder['id'] = None
            check_id = True
        if isSync is True and check_id is False and overwrite is False and check_old_id is False:
            try:
                check_id = True
                fold_id = os.getxattr(addr, 'user.id')
                fold_id = fold_id.decode()
                folder = drive.CreateFile({'id': fold_id})
            except:
                check_id = False
        if check_old_id is True and is_root_folder is False:
            check_id = False
        if check_id is False and is_root_folder is False:
            # if folder to be added to root
            if fold_id is None:
                folder = drive.CreateFile()
            # if folder to be added to some other folder
            else:
                folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

            folder['title'] = common_utils.get_file_name(addr)  # sets folder title
            folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
            try:
                check_e = os.getxattr(addr, 'user.excludeUpload')
                check_e = check_e.decode()
            except:
                check_e = 'False'
            if check_e == 'False':
                folder.Upload()
                if isSync is True or overwrite is True:
                    os.setxattr(addr, 'user.id', str.encode(folder['id']))

        # Traversing inside files/folders
        for item in os.listdir(addr):
            f_create(drive, os.path.join(addr, item), folder['id'], rel_addr + "/" +
                     str(common_utils.get_file_name(os.path.join(addr, item))), list_f, overwrite, isSync, show_update)

    # creating file
    else:
        # print progress
        if show_update:
            print("uploading file " + rel_addr)
        check_id = False
        checkModified = False
        stats = os.stat(addr)
        if isSync is True and overwrite is False and check_old_id is False:
            try:
                check_id = True
                file_id = os.getxattr(addr, 'user.id')
                file_id = file_id.decode()
                if list_f is not None:
                    for x in list_f:
                        if x['id'] == file_id:
                            if x['modifiedDate'] < datetime.utcfromtimestamp(stats.st_mtime).timestamp():
                                checkModified = True
                            break
                up_file = drive.CreateFile({'id': file_id})
            except:
                check_id = False
        if check_old_id is True:
            check_id = False
        if check_id is False:
            # if file is to be added to root
            if fold_id is None:
                up_file = drive.CreateFile()
            # if file to be added to some folder in drive
            else:
                up_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

        if checkModified is True or check_id is False:
            up_file.SetContentFile(addr)
            up_file['title'] = common_utils.get_file_name(addr)  # sets file title to original
            try:
                check_e = os.getxattr(addr, 'user.excludeUpload')
                check_e = check_e.decode()
            except:
                check_e = 'False'
            if check_e == 'False':
                up_file.Upload()
                os.utime(addr, (stats.st_atime, common_utils.utc2local(
                    datetime.strptime(up_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
                if isSync is True or overwrite is True:
                    if check_id is False or overwrite is True:
                        os.setxattr(addr, 'user.id', str.encode(up_file['id']))

    return True


def f_up(drive, fold_id, addrs, overwrite):
    sync_dir = config_utils.get_folder_sync_path()
    for addr in addrs:
        addr = os.path.join(os.path.expanduser(Path().resolve()), addr)
        # checks if the specified file/folder exists
        if not os.path.exists(addr):
            print("Specified file/folder doesn't exist !")
            return
        f_local_name = str(common_utils.get_file_name(addr))
        if sync_dir not in addr or fold_id is not None or os.path.join(addr) == os.path.join(sync_dir):
            # pass the address to f_create and on success delete/move file/folder
            if f_create(drive, addr, fold_id, f_local_name, None, False, False, True) is False:
                print("Upload unsuccessful, please try again!")
            continue
        try:
            f_id = os.getxattr(addr, 'user.id')
            f_id = f_id.decode()
            if overwrite is True:
                if os.path.isdir(addr):
                    print("Uploading...")
                    folder = drive.CreateFile({'id': f_id})
                    folder.Trash()
                    fold_id = folder['parents'][0]['id']
                    if f_create(drive, addr, fold_id, f_local_name, None, True, False, False) is False:
                        print("Upload unsuccessful, please try again!")
                else:
                    print("Uploading...")
                    up_file = drive.CreateFile({'id': f_id})
                    up_file.Trash()
                    fold_id = up_file['parents'][0]['id']
                    if f_create(drive, addr, fold_id, f_local_name, None, True, False, False) is False:
                        print("Upload unsuccessful, please try again!")
        except:
            fold_addr = os.path.dirname(addr)
            fold_name = []
            while fold_addr:
                try:
                    if os.path.join(fold_addr) == os.path.join(sync_dir):
                        if (len(fold_name) > 0):
                            fold_name.reverse()
                            i = 0
                            folder_addr = sync_dir
                            for x in fold_name:
                                if i == 0:
                                    folder = drive.CreateFile()
                                else:
                                    folder = drive.CreateFile(
                                        {"parents": [{"kind": "drive#fileLink", "id": folder['id']}]})
                                folder['title'] = x  # sets folder title
                                folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
                                try:
                                    check_e = os.getxattr(addr, 'user.excludeUpload')
                                    check_e = check_e.decode()
                                except:
                                    check_e = 'False'
                                if check_e == 'False':
                                    folder.Upload()
                                    folder_addr = os.path.join(folder_addr, x)
                                    os.setxattr(folder_addr, 'user.id', str.encode(folder['id']))
                                i += 1
                            print("Uploading...")
                            if f_create(drive, addr, folder['id'], f_local_name, None, True, True, False) is False:
                                print("Upload unsuccessful, please try again!")
                        else:
                            print("Uploading...")
                            if f_create(drive, addr, None, f_local_name, None, True, True, False) is False:
                                print("Upload unsuccessful, please try again!")
                        break
                    folder_id = os.getxattr(fold_addr, 'user.id')
                    folder_id = folder_id.decode()
                    if (len(fold_name) > 0):
                        fold_name.reverse()
                        folder = None
                        folder_addr = fold_addr
                        i = 0
                        for x in fold_name:
                            folder_addr = os.path.join(folder_addr, x)
                            if i == 0:
                                folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}]})
                            else:
                                folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder['id']}]})
                            folder['title'] = x  # sets folder title
                            folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
                            try:
                                check_e = os.getxattr(addr, 'user.excludeUpload')
                                check_e = check_e.decode()
                            except:
                                check_e = 'False'
                            if check_e == 'False':
                                folder.Upload()
                                os.setxattr(folder_addr, 'user.id', str.encode(folder['id']))
                            i += 1
                        print("Uploading...")
                        if f_create(drive, addr, folder['id'], f_local_name, None, True, True, False) is False:
                            print("Upload unsuccessful, please try again!")
                    else:
                        print("Uploading...")
                        if f_create(drive, addr, folder_id, f_local_name, None, True, True, False) is False:
                            print("Upload unsuccessful, please try again!")
                    break
                except:
                    fold_name.append(str(common_utils.get_file_name(fold_addr)))
                    fold_addr = os.path.dirname(fold_addr)


def f_sync(drive, addr):
    path = os.path.join(os.path.expanduser(Path().resolve()), addr)
    if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
        print
        # return False

    sync_dir = config_utils.get_folder_sync_path()

    list_delete = []
    print("Sync...")
    # check_root = False
    if os.path.join(path) != os.path.join(sync_dir):
        try:
            fold_id = os.getxattr(path, 'user.id')
            fold_id = fold_id.decode()
            list_f = get_all_data(drive, fold_id, True)
            list_fold = get_list_folders(drive, fold_id)
            for i in list_fold:
                list_f.append(i)
            list_l, listlf = f_list_local(path, True)
            for i in listlf:
                list_l.append(i)

        except:
            print(addr + " up")
            addrs = []
            addrs.append(path)
            f_up(drive, None, addrs, False)
            return True
    else:
        check_root = True
        list_f = get_all_data(drive, "root", True)
        list_fold = get_list_folders(drive, "root")
        for i in list_fold:
            list_f.append(i)
            # list_root = f_list(drive, "root", False)
        list_l, listlf = f_list_local(path, True)
        for i in listlf:
            list_l.append(i)
        # check_root = True
    if len(list_l) == 0 and check_root is True:
        return True
    for x in list_f:
        check_f = False
        for y in list_l:
            if x['id'] == y['id']:
                stats = os.stat(y['canonicalPath'])
                if x['modifiedDate'] > datetime.utcfromtimestamp(stats.st_mtime).timestamp():
                    save_location = common_utils.get_local_path(drive, x['id'], config_utils.get_folder_sync_path())
                    try:
                        x['type']
                        downloader(drive, "-do", x['id'], save_location)
                    except:
                        print
                check_f = True
                break
        # if check_f is False:
        #     save_location = common_utils.get_local_path(drive, x['id'], config_utils.get_dir_sync_location())
        #     if x['isFolder'] != 'folder':
        #         f_down(drive, "-d", x['id'], save_location)
        #     elif len(f_list(drive, x['id'], False)) == 0:
        #         f_down(drive, "-d", x['id'], save_location)

    for x in list_l:
        check_f = False
        for y in list_f:
            if x['id'] == y['id']:
                check_f = True
                break
        if check_f is False:
            if x['id'] is not None:
                list_delete.append(x['id'])

    if len(list_delete) > 0:
        f_remove(drive, "local", list_delete)
    if os.path.join(path) == os.path.join(sync_dir):
        fold_id = None
    if f_create(drive, path, fold_id, str(common_utils.get_file_name(path)), None, False, True, False) is False:
        print("Sync unsuccessful, please try again!")

    return True


def f_exclusive(addr, options):
    if options is True:
        path = os.path.join(os.path.expanduser(Path().resolve()), addr)
        if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
            return False
        # Traversing inside files/folders
        if os.path.isdir(addr):
            os.setxattr(addr, 'user.excludeUpload', str.encode('True'))
            for item in os.listdir(addr):
                f_exclusive(item)
        else:
            os.setxattr(addr, 'user.excludeUpload', str.encode('True'))
    else:
        path = os.path.join(os.path.expanduser(Path().resolve()), addr)
        if path.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
            return False
        # Traversing inside files/folders
        if os.path.isdir(addr):
            os.setxattr(addr, 'user.excludeUpload', str.encode('False'))
            for item in os.listdir(addr):
                f_exclusive(item)
        else:
            os.setxattr(addr, 'user.excludeUpload', str.encode('False'))


def share_link(drive, option, file_id, mail):
    # print(mail)
    if is_valid_id(drive, file_id):
        # create shared file
        share_file = drive.CreateFile({'id': file_id})
        # print(share_file)

        permissions = share_file.GetPermissions()
        if mail == 'all':
            for element in permissions:
                if element['role'] != 'owner':
                    share_file.DeletePermission(element['id'])
        else:
            for element in permissions:
                if 'emailAddress' in element and element['emailAddress'].lower() == mail.lower():
                    # print(element['emailAddress'], element['id'])
                    share_file.DeletePermission(element['id'])
                if element['id'] == 'anyone' and len(mail) == 0:
                    share_file.DeletePermission(element['id'])

        # check file's permission
        if common_utils.check_option(option, 'r', 3) or common_utils.check_option(option, 's', 2):
            role = "reader"
        elif common_utils.check_option(option, 'w', 3):
            role = "writer"
        elif common_utils.check_option(option, 'u', 3):
            # share_file.FetchMetadata(fields='permissionIds')
            # print(share_file['permissionIds'])
            return
        else:
            print("Permission is not a valid. Try again")
            return

        # permissions = share_file.GetPermissions()
        # print(permissions)

        if len(mail) == 0:
            share_file.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': role
            })
        else:
            try:
                share_file.InsertPermission({
                    'type': 'user',
                    'value': mail,
                    'role': role
                })
            except:
                print("%s is an invalid mail!" % mail)
                return

        share_file.FetchMetadata(fields='alternateLink, title')

        # print(share_file['alternateLink'])
        print("Share link copied to clipboard!")
        pyperclip.copy(share_file['alternateLink'])
        mess = pyperclip.paste()
        print(mess)


def f_remove(drive, mode, addrs):
    # print(addrs)
    if mode == "local":
        sync_dir = config_utils.get_folder_sync_path()
        # Appending file/folder name to download directory
        for addr in addrs:
            addr = os.path.join(os.path.expanduser(Path().resolve()), addr)
            if addr.startswith(config_utils.get_folder_sync_path() + os.sep) is False:
                return False
            if not os.path.exists(addr):
                print("%s doesn't exist in %s" % (addr, sync_dir))
            else:
                # use recursive removal if directory
                if os.path.isdir(addr):
                    shutil.rmtree(addr)
                else:
                    os.remove(addr)
                print("%s removed from %s" % (addr, sync_dir))
        return True

    elif mode == "remote":
        for addr in addrs:
            # check if file_id valid
            if is_valid_id(drive, addr):
                # file to be removed
                r_file = drive.CreateFile({'id': addr})
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
        for addr in addrs:
            check_path = True
            f_path = os.path.join(os.path.expanduser(Path().resolve()), addr)
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
                print("%s removed from %s" % (addr, sync_dir))
                return True
            # check if file_id valid
            list_local, local_folders = f_list_local(sync_dir, True)
            for i in local_folders:
                list_local.append(i)
            if is_valid_id(drive, addr):
                # file to be removed
                r_file = drive.CreateFile({'id': addr})
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
                if x['id'] == addr:
                    f_addr = x['canonicalPath']
                    # use recursive removal if directory
                    if os.path.isdir(f_addr):
                        shutil.rmtree(f_addr)
                    else:
                        os.remove(f_addr)
                        print("%s removed from %s" % (f_addr, sync_dir))
        return True

    else:
        print("%s is not a valid mode" % mode)
        return False


def get_info(drive, option, instance):
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

    # print(instance_id)
    if instance_id is not None and is_valid_id(drive, instance_id):
        remote_file = drive.CreateFile({'id': instance_id})
        # print(remote_file['title'])
        remote_file.FetchMetadata(fetch_all=True)
        permissions = remote_file.get('permissions')
        # print(remote_file)
        # print(permissions)
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
            'fileSize': remote_file.get('fileSize') if remote_file.get('fileSize') else '',
            'isFolder': True if remote_file.get('mimeType') == 'application/vnd.google-apps.folder' else False
        }
        for elem in permissions:
            result_remote.get('userPermission').append({
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
    else:
        if not path_err and not default_opt:
            print('%s is invalid !' % instance)

    print(result_local)
    print("=====")
    print(result_remote)
    # print("=====")
    # print(Path().resolve())

    return result_local, result_remote


def file_restore(drive, addr_list):
    print(addr_list)
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
            # ele done nothing
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
                f_all(drive, f['id'], file_list, False, None, None, folder_list)
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


def check_remote_dir_files_sync(service, remote_folder_id, local_folder):
    remote_dir_files_list = get_all_data(service, remote_folder_id, True)
    local_dir_files_list, local_folders_list = f_list_local(local_folder, True)

    if len(remote_dir_files_list) != len(local_dir_files_list):
        return False
    else:
        count = 0
        for remote_file in remote_dir_files_list:
            for local_file in local_dir_files_list:
                if remote_file['id'] == local_file['id']:
                    if remote_file['md5Checksum']:
                        if remote_file['md5Checksum'] == local_file['md5Checksum']:
                            count += 1
                            break
                    elif remote_file['fileSize'] == remote_file['fileSize']:
                        count += 1
                        break
        if count == len(remote_dir_files_list):
            return True
        else:
            return False


def compare_and_change_type_show(service, remote_files_list, local_files_list):
    for remote_file in remote_files_list:
        for local_file in local_files_list:
            if remote_file['id'] == local_file['id']:
                if re.compile('folder', re.IGNORECASE).search(remote_file.get('mimeType')):
                    if check_remote_dir_files_sync(service, remote_file['id'], local_file['canonicalPath']):
                        remote_file['typeShow'] = "dongbo"
                    else:
                        remote_file['typeShow'] = "notdongbo"
                else:
                    if remote_file['md5Checksum']:
                        if remote_file['md5Checksum'] == local_file['md5Checksum']:
                            remote_file['typeShow'] = "dongbo"
                        else:
                            remote_file['typeShow'] = "notdongbo"
                    else:
                        if remote_file['fileSize'] == local_file['fileSize']:
                            remote_file['typeShow'] = "dongbo"
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


def filter_none_id(local_files_list):
    result = []
    for local_file in local_files_list:
        if not local_file['id']:
            local_file['typeShow'] = 'maytinh'
            result.append(local_file)
    return result


def f_calculate_usage_of_folder(service):
    driveAudioUsage = 0
    drivePhotoUsage = 0
    driveMoviesUsage = 0
    driveDocumentUsage = 0
    driveOthersUsage = 0

    file_list = get_all_data(service, 'root', True)
    for file in file_list:
        if common_utils.isAudioFile(file):
            driveAudioUsage += common_utils.getFileSize(file)
        elif common_utils.isImageFile(file):
            drivePhotoUsage += common_utils.getFileSize(file)
        elif common_utils.isVideoFile(file):
            driveMoviesUsage += common_utils.getFileSize(file)
        elif common_utils.isDocument(file):
            driveDocumentUsage += common_utils.getFileSize(file)
        else:
            driveOthersUsage += common_utils.getFileSize(file)
    return driveAudioUsage, drivePhotoUsage, driveMoviesUsage, driveDocumentUsage, driveOthersUsage
