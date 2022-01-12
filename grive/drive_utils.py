from builtins import str
import json
import os
import sys
import shutil
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
                temp_d_folder = os.path.join(sync_folder, f['title'])
                common_utils.dir_exists(temp_d_folder)
                f_all(drive, f['id'], None, True, temp_d_folder, option)

            else:  # we want to just list the files
                f_all(drive, f['id'], file_list, False, None, None)
        else:
            if download:
                f_down(drive, option, f['id'], sync_folder)
            else:
                file_list.append(f)


def f_down(drive, option, file_id, sync_folder):
    # check if file id not valid
    if not is_valid_id(drive, file_id):
        print("%s is an invalid id of file or folder !" % file_id)
        return

    d_file = drive.CreateFile({'id': file_id})

    # open mime_swap dictionary for changing mimeType if required
    with open(common_utils.mime_dict) as f:
        mime_swap = json.load(f)

    overwrite = False
    if common_utils.check_option(option, 'o', 3):
        overwrite = True

    # checking if the specified id belongs to a folder
    if d_file['mimeType'] == mime_swap['folder']:
        folder_name = d_file['title']
        folder_path = os.path.join(sync_folder, folder_name)
        if folder_name in os.listdir(sync_folder):
            if overwrite:
                if os.path.isdir(folder_path):
                    shutil.rmtree(folder_path)
                    print("Recreating folder %s in %s" % (folder_name, sync_folder))
                    common_utils.dir_exists(folder_path)
                    f_all(drive, d_file['id'], None, True, folder_path, option)
            else:
                print("Folder '%s' already present in %s" % (d_file['title'], sync_folder))
        else:
            print("Creating folder %s in %s" % (folder_name, sync_folder))
            common_utils.dir_exists(os.path.join(sync_folder, d_file['title']))
            f_all(drive, d_file['id'], None, True, folder_path, option)

    # for online file types like Gg Docs, Gg Sheet..etc
    elif d_file['mimeType'] in mime_swap:
        # open formats.json for adding custom format
        # with open(common_utils.format_dict) as f:
        #     format_add = json.load(f)

        # changing file name to suffix file format
        # f_name = d_file['title'] + format_add[d_file['mimeType']]
        f_name = d_file['title']
        if f_name in os.listdir(sync_folder):
            if overwrite:
                if os.path.isfile(os.path.join(sync_folder, f_name)):
                    os.remove(os.path.join(sync_folder, f_name))
                    print("Downloading " + os.path.join(sync_folder, f_name))
                    d_file.GetContentFile(os.path.join(sync_folder, f_name),
                                          mimetype=mime_swap[d_file['mimeType']])
            else:
                print("%s already present in %s" % (f_name, sync_folder))
        else:
            print("Downloading " + os.path.join(sync_folder, f_name))
            d_file.GetContentFile(os.path.join(sync_folder, f_name),
                                  mimetype=mime_swap[d_file['mimeType']])

    else:
        f_name = d_file['title']
        if f_name in os.listdir(sync_folder):
            if overwrite:
                if os.path.isfile(os.path.join(sync_folder, f_name)):
                    os.remove(os.path.join(sync_folder, f_name))
                    print("Downloading " + os.path.join(sync_folder, d_file['title']))
                    d_file.GetContentFile(os.path.join(sync_folder, d_file['title']))
            else:
                print("%s already present in %s" % (d_file['title'], sync_folder))

        else:
            print("Downloading " + os.path.join(sync_folder, d_file['title']))
            d_file.GetContentFile(os.path.join(sync_folder, d_file['title']))


def f_create(drive, addr, fold_id, rel_addr, listF, overwrite, isSync, show_update):
    # Check whether address is right or not
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, check the address!")
        return

    if isSync is True and overwrite is False and listF is None:
        listF = f_list(drive, "root", True)

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
            folder.Upload()
            if isSync is True or overwrite is True:
                os.setxattr(addr, 'user.id', str.encode(folder['id']))

        # Traversing inside files/folders
        for item in os.listdir(addr):
            f_create(drive, os.path.join(addr, item), folder['id'], rel_addr + "/" +
                     str(common_utils.get_file_name(os.path.join(addr, item))), listF, overwrite, isSync, show_update)

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
                for x in listF:
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
            up_file.Upload()
            os.utime(addr, (stats.st_atime, common_utils.utc2local(datetime.strptime(up_file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
            if isSync is True or overwrite is True:
                if check_id is False or overwrite is True:
                    os.setxattr(addr, 'user.id', str.encode(up_file['id']))

    return True

def f_up(drive, fold_id, addrs, overwrite):
    sync_dir = config_utils.get_dir_sync_location()
    for addr in addrs:
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
                                    folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder['id']}]})
                                folder['title'] = x  # sets folder title
                                folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
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
    sync_dir = config_utils.get_dir_sync_location()
    if sync_dir not in addr:
        return False
    # listF = f_list(addr, "root", False)
    if os.path.join(addr) != os.path.join(sync_dir):
        try:
            fold_id = os.getxattr(addr, 'user.id')
            fold_id = fold_id.decode()
        except:
            addrs = []
            addrs.append(addr)
            f_up(drive, None, addrs, False)
            return True
    else:
        # fold_id = listF[0]['parents']['id']
        fold_id = None
    # f_down(drive, "-d", fold_id, addr)
    print("Sync...")
    if f_create(drive, addr, fold_id, str(common_utils.get_file_name(addr)), None, False, True, False) is False:
        print("Sync unsuccessful, please try again!")

    return True

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
            f_path = os.path.join(sync_dir, addr)
            if not os.path.exists(f_path):
                print("%s doesn't exist in %s" % (addr, sync_dir))
            else:
                # use recursive removal if directory
                if os.path.isdir(addr):
                    shutil.rmtree(f_path)
                else:
                    os.remove(f_path)
                print("%s removed from %s" % (addr, sync_dir))

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
    
    elif mode == "all":
        sync_dir = config_utils.get_dir_sync_location()
        for addr in addrs:
            # check if file_id valid
            if is_valid_id(drive, addr):
                # file to be removed
                r_file = drive.CreateFile({'id': addr})
                f_name = r_file['title']
                f_parent = r_file['parents'][0]
                folder_name = []
                while f_parent['isRoot'] is False:
                    folder = drive.CreateFile({'id': f_parent['id']})
                    folder_name.append(folder['title'])
                    f_parent = folder['parents'][0]
                if (len(folder_name) > 0):
                    folder_name.reverse()
                    f_path = os.path.join(sync_dir)
                    for x in folder_name:
                        f_path = os.path.join(f_path, x)
                    f_path = os.path.join(f_path, f_name)
                    if os.path.exists(f_path):
                        if os.path.isdir(f_path):
                            shutil.rmtree(f_path)
                        else:
                            os.remove(f_path)
                # delete permanently if in trash
                if is_trash(drive, r_file['id']):
                    r_file.Delete()
                    print("%s deleted permanently" % f_name)
                # move to trash
                else:
                    r_file.Trash()
                    print("%s moved to GDrive trash. List files in trash by -lt parameter" % f_name)

    else:
        print("%s is not a valid mode" % mode)
        return


def file_restore(drive, addrs):
    print(addrs)
    for addr in addrs:
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
    for f in drive.ListFile({'q': "'root' in parents and trashed=true"}).GetList():
        if file_id == f['id']:
            return True
    return False


def f_list_local(folder, recursive):
    """List all files and folders in the sync directory

        :param folder: Canonical path of folder
        :param recursive: True if recursive and and vice versa

        :returns: List of files with information
    """

    dicts = []
    if recursive:
        subfolders, local_files = common_utils.run_fast_scandir(folder)
        for file in local_files:
            # print(file)
            stats = os.stat(file)
            result = {
                'storageLocation': 'local',
                'title': common_utils.get_file_name(file),
                'canonicalPath': file,
                'modifiedDate': stats.st_mtime,
                'md5Checksum': hashlib.md5(open(file, 'rb').read()).hexdigest(),
                'excludeUpload': False
            }
            dicts.append(result)
        return dicts
    else:
        # for file in os.listdir(folder):
        for file in os.scandir(folder):
            stats = os.stat(file.path)
            result = {
                'storageLocation': 'local',
                'title': common_utils.get_file_name(file),
                'canonicalPath': file,
                'modifiedDate': stats.st_mtime,
                'md5Checksum': hashlib.md5(open(file.path, 'rb').read()).hexdigest() if file.is_file() else None,
                'excludeUpload': False
            }
            dicts.append(result)
        return dicts


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
                'alternateLink': file['alternateLink'],
                'title': file['title'],
                'modifiedDate': datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
                'parents': file['parents'],
                'md5Checksum': file.get('md5Checksum')
            }
            dicts.append(result)

        return dicts

    # lists all files and folder inside given folder
    else:
        if keyword == "all":
            file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
            for f in file_list:
                print('title: %s, id: %s' % (f['title'], f['id']))

        # lists all files and folders inside trash
        elif keyword == "trash":
            file_list = drive.ListFile({'q': "'root' in parents and trashed=true"}).GetList()
            for f in file_list:
                print('title: %s, id: %s' % (f['title'], f['id']))

        # lists all files and folders inside folder given as argument in keyword
        else:
            q_string = "'%s' in parents and trashed=false" % keyword
            file_list = drive.ListFile({'q': q_string}).GetList()
            for f in file_list:
                print('title: %s, id: %s' % (f['title'], f['id']))


def f_open(folder):
    os.system('xdg-open "%s"' % config_utils.get_dir_sync_location())
