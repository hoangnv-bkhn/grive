from builtins import str
import json
import os
import sys
import shutil
from pathlib import Path

import pyperclip
import hashlib

from datetime import datetime
from pydrive import files

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
except ImportError:
    from . import common_utils
    from . import config_utils


def f_all(drive, fold_id, file_list, download, sync_folder, option):
    """Recursively download or just list files in folder

        :param drive: Google Drive instance
        :param fold_id: id of folder to search
        :param file_list: initial list to store list of file when search
        :param download: True if downloads, False if just recursively list file
        :param sync_folder: folder to store when download
        :param option: option download (overwrite or not)

        :returns: List of file store in file_list param
    """

    q_string = "'%s' in parents and trashed=false" % fold_id
    for f in drive.ListFile({'q': q_string}).GetList():
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            if download:  # if we are to download the files
                save_location = os.path.join(sync_folder, f['title'])
                if os.path.exists(save_location):
                    save_location = common_utils.get_dup_name(sync_folder, os.path.basename(sync_folder))

                common_utils.dir_exists(save_location)
                os.setxattr(save_location, 'user.id', str.encode(f['id']))

                stats = os.stat(save_location)
                os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                    datetime.strptime(f['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

                f_all(drive, f['id'], None, True, save_location, option)

            else:  # we want to just list the files
                f_all(drive, f['id'], file_list, False, None, None)
        else:
            if download:
                f_down(drive, option, f['id'], sync_folder)
            else:
                file_list.append(f)


def f_down(drive, option, file_id, save_folder):
    # print(sync_folder)
    # check if file id not valid
    if not is_valid_id(drive, file_id):
        print(" %s is an invalid id of file or folder !" % file_id)
        return

    d_file = drive.CreateFile({'id': file_id})

    # open mime_swap dictionary for changing mimeType if required
    with open(common_utils.mime_dict) as f:
        mime_swap = json.load(f)

    overwrite = False
    if common_utils.check_option(option, 'o', 3) or common_utils.check_option(option, 'o', 4):
        overwrite = True

    # checking if the specified id belongs to a folder
    if d_file['mimeType'] == mime_swap['folder']:
        # folder_name = d_file['title']

        folder_remote_name = d_file['title']
        folder_remote_id = d_file['id']
        has_in_local = False
        folder_local_name = folder_remote_name

        # folder_path = os.path.join(sync_folder, folder_name)

        local_files, local_folders = f_list_local(save_folder, 0)
        for elem in local_files:
            if elem['id'] == folder_remote_id:
                has_in_local = True
                folder_local_name = elem['title']
                # print(123)

        folder_path = os.path.join(save_folder, folder_local_name)
        # print(folder_path)
        flag = True
        if has_in_local:
            if overwrite:
                if os.path.isdir(folder_path):
                    # print(folder_path)
                    shutil.rmtree(folder_path)
                    print(" Recreating folder %s in %s" % (folder_remote_name, save_folder))
            else:
                flag = False
                print(" Folder '%s' already present in %s" % (d_file['title'], save_folder))
        else:
            print(" Creating folder %s in %s" % (folder_remote_name, save_folder))

        if flag:
            save_location = folder_path
            if os.path.exists(save_location):
                # print(456)
                save_location = common_utils.get_dup_name(save_folder, os.path.basename(folder_path))
            # print(save_location)
            common_utils.dir_exists(save_location)
            os.setxattr(save_location, 'user.id', str.encode(folder_remote_id))

            stats = os.stat(save_location)
            os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                datetime.strptime(d_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

            f_all(drive, folder_remote_id, None, True, save_location, option)

    # for online file types like Gg Docs, Gg Sheet..etc
    elif d_file['mimeType'] in mime_swap:
        # open formats.json for adding custom format
        with open(common_utils.format_dict) as f:
            format_add = json.load(f)

        file_remote_name = d_file['title']
        file_remote_id = d_file['id']
        has_in_local = False
        file_local_name = file_remote_name

        # changing file name to suffix file format
        f_name = file_remote_name + format_add[d_file['mimeType']]
        # f_name = d_file['title']

        local_files, local_folders = f_list_local(save_folder, 0)
        for elem in local_files:
            if elem['id'] == file_remote_id:
                has_in_local = True
                file_local_name = elem['title']

        flag = True
        if has_in_local:
            if overwrite:
                if os.path.isfile(os.path.join(save_folder, file_local_name)):
                    os.remove(os.path.join(save_folder, file_local_name))
            else:
                flag = False
                print(" %s already present in %s" % (f_name, save_folder))
        if flag:
            save_location = os.path.join(save_folder, f_name)
            if os.path.exists(save_location):
                save_location = common_utils.get_dup_name(save_folder, f_name)

            print(" Downloading " + save_location)
            d_file.GetContentFile(save_location,
                                  mimetype=mime_swap[d_file['mimeType']])
            os.setxattr(save_location, 'user.id', str.encode(file_remote_id))
            stats = os.stat(save_location)
            os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                datetime.strptime(d_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

    else:
        file_remote_name = d_file['title']
        file_remote_id = d_file['id']
        file_local_name = file_remote_name
        has_in_local = False

        local_files, local_folders = f_list_local(save_folder, 0)
        for elem in local_files:
            if elem['id'] == file_remote_id:
                has_in_local = True
                file_local_name = elem['title']

        flag = True
        if has_in_local:
            if overwrite:
                if os.path.isfile(os.path.join(save_folder, file_local_name)):
                    os.remove(os.path.join(save_folder, file_local_name))
            else:
                flag = False
                print(" %s already present in %s" % (d_file['title'], save_folder))

        if flag:
            save_location = os.path.join(save_folder, file_remote_name)
            if os.path.exists(save_location):
                save_location = common_utils.get_dup_name(save_folder, file_remote_name)
            print(" Downloading " + save_location)
            d_file.GetContentFile(save_location)
            os.setxattr(save_location, 'user.id', str.encode(file_remote_id))
            stats = os.stat(save_location)
            os.utime(save_location, (stats.st_atime, common_utils.utc2local(
                datetime.strptime(d_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
            print(" Completed\n")


def f_create(drive, addr, fold_id, rel_addr, list_f, overwrite, isSync, show_update):
    # Check whether address is right or not
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, check the address!")
        return

    if isSync is True and overwrite is False and list_f is None:
        list_f = f_list(drive, "root", True)

    # creating if it's a folder
    if os.path.isdir(addr):
        sync_dir = config_utils.get_dir_sync_location()
        # print progress
        if show_update:
            print("creating folder " + rel_addr)
        check_id = False
        if os.path.join(addr) == os.path.join(sync_dir) and fold_id is None and isSync is True:
            folder = drive.CreateFile()
            folder['id'] = None
            check_id = True
        if isSync is True and check_id is False and overwrite is False:
            try:
                check_id = True
                fold_id = os.getxattr(addr, 'user.id')
                fold_id = fold_id.decode()
                folder = drive.CreateFile({'id': fold_id})
            except:
                check_id = False
        if check_id is False:
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
        if isSync is True and overwrite is False:
            try:
                check_id = True
                file_id = os.getxattr(addr, 'user.id')
                file_id = file_id.decode()
                for x in list_f:
                    if x['id'] == file_id:
                        if x['modifiedDate'] != datetime.utcfromtimestamp(stats.st_mtime).timestamp():
                            checkModified = True
                        break
                up_file = drive.CreateFile({'id': file_id})
            except:
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
                os.utime(addr, (stats.st_atime, common_utils.utc2local(datetime.strptime(up_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
                if isSync is True or overwrite is True:
                    if check_id is False or overwrite is True:
                        os.setxattr(addr, 'user.id', str.encode(up_file['id']))

    return True


def f_up(drive, fold_id, addrs, overwrite):
    sync_dir = config_utils.get_dir_sync_location()
    for addr in addrs:
        addr = os.path.join(os.path.expanduser(Path().resolve()), addr)
        # checks if the specified file/folder exists
        if not os.path.exists(addr):
            print("Specified file/folder doesn't exist, please remove from upload list using -config")
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
    if path.startswith(config_utils.get_dir_sync_location() + os.sep) is False:
        print
        # return False

    sync_dir = config_utils.get_dir_sync_location()

    list_delete = []
    print("Sync...")
    # check_root = False
    if os.path.join(path) != os.path.join(sync_dir):
        try:
            fold_id = os.getxattr(path, 'user.id')
            fold_id = fold_id.decode()
            list_f = f_list(drive, fold_id, True)
            list_l = f_list_local(path, True)
        except:
            addrs = []
            addrs.append(path)
            f_up(drive, None, addrs, False)
            return True
    else:
        list_f = f_list(drive, "root", True)
        # list_root = f_list(drive, "root", False)
        list_l = f_list_local(sync_dir, True)
        # check_root = True
    # if len(list_l) == 0 and check_root is True:
    #     for x in list_root:
    #         save_location = common_utils.get_local_path(drive, x['id'], config_utils.get_dir_sync_location())
    #         f_down(drive, "-d", x['id'], save_location)
    #     return True
    for x in list_f:
        check_f = False
        for y in list_l:
            if x['id'] == y['id']:
                stats = os.stat(y['canonicalPath'])
                if x['modifiedDate'] != datetime.utcfromtimestamp(stats.st_mtime).timestamp():
                    save_location = common_utils.get_local_path(drive, x['id'], config_utils.get_dir_sync_location())
                    if x['isFolder'] != 'folder':
                        f_down(drive, "-do", x['id'], save_location)
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

    f_remove(drive, "all", list_delete)
    if os.path.join(path) == os.path.join(sync_dir):
        fold_id = None
    if f_create(drive, path, fold_id, str(common_utils.get_file_name(path)), None, False, True, False) is False:
        print("Sync unsuccessful, please try again!")

    return True

def f_exclusive(addr, options):
    if options is True:
        path = os.path.join(os.path.expanduser(Path().resolve()), addr)
        if path.startswith(config_utils.get_dir_sync_location() + os.sep) is False:
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
        if path.startswith(config_utils.get_dir_sync_location() + os.sep) is False:
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
        sync_dir = config_utils.get_dir_sync_location()
        # Appending file/folder name to download directory
        for addr in addrs:
            addr = os.path.join(os.path.expanduser(Path().resolve()), addr)
            if addr.startswith(config_utils.get_dir_sync_location() + os.sep) is False:
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
        sync_dir = config_utils.get_dir_sync_location()
        for addr in addrs:
            check_path = True
            f_path = os.path.join(os.path.expanduser(Path().resolve()), addr)
            if f_path.startswith(config_utils.get_dir_sync_location() + os.sep) is False:
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
            list_local = f_list_local(sync_dir, True)
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

    local_files, sub_folders = f_list_local(config_utils.get_dir_sync_location(), True)

    path_err = False
    default_opt = False

    instance_id = None
    if common_utils.check_option(option, 'i', 2):
        default_opt = True
        path = os.path.join(os.path.expanduser(Path().resolve()), instance)
        if os.path.exists(path) and path.startswith(config_utils.get_dir_sync_location()+os.sep):
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
            # print(file)
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
                'fileSize': stats.st_size
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


# Operations for file list commands
def f_list(drive, keyword, recursive):
    # get recursively all files in the folder
    if recursive:
        file_list = []
        if keyword == "root":
            for f in drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList():
                # if file in list is folder, get it's file list
                if f['mimeType'] == 'application/vnd.google-apps.folder':
                    # print(f['title'])
                    f_all(drive, f['id'], file_list, False, None, None)
                else:
                    file_list.append(f)
        else:
            f_all(drive, keyword, file_list, False, None, None)

        # for f in file_list:
        #     print('title: %s, id: %s' % (f['title'], f['id']))

        dicts = []
        for file in file_list:
            result = {
                'storageLocation': 'remote',
                'id': file['id'],
                'alternateLink': file.get('alternateLink'),
                'title': file['title'],
                'modifiedDate': datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
                'parents': file.get('parents'),
                'shared': file.get('shared'),
                'md5Checksum': file.get('md5Checksum'),
                'type': file['mimeType'],
                'fileSize': file.get('fileSize') if file.get('fileSize') else '',
                'isFolder': 'folder' if file.get('mimeType') == 'application/vnd.google-apps.folder' else 'file'
            }
            dicts.append(result)

        return dicts

    # lists all files and folder inside given folder
    else:
        file_list = []
        if keyword == "all":
            for f in drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList():
                file_list.append(f)

        # lists all files and folders inside trash
        elif keyword == "trash":
            for f in drive.ListFile(
                    {'q': "trashed=true"}).GetList():  # nhu cu la: 'q': "'root' in parents and trashed=true"
                file_list.append(f)

        # lists all files and folders inside folder given as argument in keyword
        else:
            q_string = "'%s' in parents and trashed=false" % keyword
            for f in drive.ListFile({'q': q_string}).GetList():
                file_list.append(f)

        dicts = []
        for file in file_list:
            result = {
                'storageLocation': 'remote',
                'id': file['id'],
                'alternateLink': file.get('alternateLink'),
                'title': file['title'],
                'modifiedDate': datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
                'parents': file.get('parents'),
                'shared': file.get('shared'),
                'md5Checksum': file.get('md5Checksum'),
                'type': file['mimeType'],
                'fileSize': file.get('fileSize') if file.get('fileSize') else '',
                'typeShow': None,
                'isFolder': 'folder' if file.get('mimeType') == 'application/vnd.google-apps.folder' else 'file'
            }
            dicts.append(result)

        return dicts


def f_open(folder):
    os.system('xdg-open "%s"' % config_utils.get_dir_sync_location())


def check_remote_dir_files_sync(drive, remote_folder_id, local_folder):
    remote_dir_files_list = f_list(drive, remote_folder_id, True)
    local_dir_files_list, local_folders_list = f_list_local(local_folder, True)

    if len(remote_dir_files_list) != len(local_dir_files_list):
        return False
    else:
        count = 0
        for remote_file in remote_dir_files_list:
            for local_file in local_dir_files_list:
                if remote_file['title'] == local_file['title']:
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


def f_calculateUsageOfFolder(drive):
    driveAudioUsage = 0
    drivePhotoUsage = 0
    driveMoviesUsage = 0
    driveDocumentUsage = 0
    driveOthersUsage = 0

    file_list = f_list(drive, 'root', True)
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

# def convertToKBFileSize(size):
#     if(size!=''):
#         return round((float(size)/1024), 3)
#     else:
#         return size

# def convertToMBFileSize(size):
#     if(size!=''):
#         return round((float(size)/1048576), 3)
#     else:
#         return size
