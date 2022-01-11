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


def f_down(drive, option, file_id, save_folder):
    # print(sync_folder)
    # check if file id not valid
    if not is_valid_id(drive, file_id):
        print("%s is an invalid id of file or folder !" % file_id)
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

        for elem in f_list_local(save_folder, 0):
            if elem['id'] == folder_remote_id:
                has_in_local = True
                folder_local_name = elem['title']

        folder_path = os.path.join(save_folder, folder_local_name)
        flag = True
        if has_in_local:
            if overwrite:
                if os.path.isdir(folder_path):
                    print(folder_path)
                    shutil.rmtree(folder_path)
                    print("Recreating folder %s in %s" % (folder_remote_name, save_folder))
            else:
                flag = False
                print("Folder '%s' already present in %s" % (d_file['title'], save_folder))
        else:
            print("Creating folder %s in %s" % (folder_remote_name, save_folder))

        if flag:
            common_utils.dir_exists(folder_path)
            os.setxattr(folder_path, 'user.id', str.encode(folder_remote_id))
            f_all(drive, folder_remote_id, None, True, folder_path, option)

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

        for elem in f_list_local(save_folder, 0):
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
                print("%s already present in %s" % (f_name, save_folder))
        if flag:
            print("Downloading " + os.path.join(save_folder, f_name))
            d_file.GetContentFile(os.path.join(save_folder, f_name),
                                  mimetype=mime_swap[d_file['mimeType']])
            os.setxattr(os.path.join(save_folder, f_name), 'user.id', str.encode(file_remote_id))

    else:
        file_remote_name = d_file['title']
        file_remote_id = d_file['id']
        has_in_local = False
        file_local_name = file_remote_name
        for elem in f_list_local(save_folder, 0):
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
                print("%s already present in %s" % (d_file['title'], save_folder))

        if flag:
            print("Downloading " + os.path.join(save_folder, file_remote_name))
            d_file.GetContentFile(os.path.join(save_folder, file_remote_name))
            os.setxattr(os.path.join(save_folder, file_remote_name), 'user.id', str.encode(file_remote_id))


def f_create(drive, addr, fold_id, rel_addr, show_update):
    # Check whether address is right or not
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, check the address!")
        return

    # creating if it's a folder
    if os.path.isdir(addr):
        # print progress
        if show_update:
            print("creating folder " + rel_addr)
        # if folder to be added to root
        if fold_id is None:
            folder = drive.CreateFile()
        # if folder to be added to some other folder
        else:
            folder = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

        folder['title'] = common_utils.get_file_name(addr)  # sets folder title
        folder['mimeType'] = 'application/vnd.google-apps.folder'  # assigns it as GDrive folder
        folder.Upload()

        # Traversing inside files/folders
        for item in os.listdir(addr):
            f_create(drive, os.path.join(addr, item), folder['id'], rel_addr + "/" +
                     str(common_utils.get_file_name(os.path.join(addr, item))), show_update)

    # creating file
    else:
        # print progress
        if show_update:
            print("uploading file " + rel_addr)
        # if file is to be added to root
        if fold_id is None:
            up_file = drive.CreateFile()
        # if file to be added to some folder in drive
        else:
            up_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": fold_id}]})

        up_file.SetContentFile(addr)
        up_file['title'] = common_utils.get_file_name(addr)  # sets file title to original
        up_file.Upload()

    return True


def f_up(drive, addr, fold_id):
    # checks if the specified file/folder exists
    if not os.path.exists(addr):
        print("Specified file/folder doesn't exist, please remove from upload list using -config")
        return

    # pass the address to f_create and on success delete/move file/folder
    if f_create(drive, addr, fold_id, str(common_utils.get_file_name(addr)), True):
        # remove file if Remove_Post_Upload is true, otherwise move to GDrive downloads
        # remove_post_upload = config_utils.read_config()['Remove_Post_Upload']
        remove_post_upload = False
        if remove_post_upload:
            # use recursive removal if directory
            if os.path.isdir(addr):
                shutil.rmtree(addr)
            # normal os removal for file
            else:
                os.remove(addr)
        # else:
        #     shutil.move(addr, config_utils.get_dir_sync_location())
    else:
        print("Upload unsuccessful, please try again!")


def f_sync(drive):

    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

    dir_folder = config_utils.get_dir_sync_location()

    for f in os.listdir(dir_folder):

        check = False

        dir_file = dir_folder + "/" + f
        rel_addr = common_utils.get_file_name(dir_file)

        for f_sub in file_list:
            if((f == f_sub['title']) and (f_sub.get('md5Checksum') is not None)):
                check = True
                md5checksum = hashlib.md5(open(dir_file, 'rb').read()).hexdigest()
                if(md5checksum != f_sub.get('md5Checksum')):
                    up_file = drive.CreateFile({'id': f_sub['id'], 'title': f_sub['title']})
                    up_file.SetContentFile(dir_file)
                    print("Modified file " + rel_addr)
                    up_file.Upload()
                    break

        if (check is False):
            up_file = drive.CreateFile()
            up_file.SetContentFile(dir_file)
            up_file['title'] = rel_addr
            print("uploading file " + rel_addr)
            up_file.Upload()

    return


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


def file_remove(drive, mode, addrs):
    print(addrs)
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

    dicts = []
    if recursive:
        subfolders, local_files = common_utils.run_fast_scandir(folder)
        for file in local_files:
            # print(file)
            stats = os.stat(file)
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
                'md5Checksum': hashlib.md5(open(file, 'rb').read()).hexdigest(),
                'excludeUpload': False,
                'fileSize': stats.st_size
            }
            dicts.append(result)
        return dicts
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
                'md5Checksum': file.get('md5Checksum'),
                'type': file['mimeType'],
                'fileSize': file.get('fileSize') if file.get('fileSize') else '',
                'isFolder': 'folder' if file['mimeType'] == 'application/vnd.google-apps.folder' else 'file'
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
            for f in drive.ListFile({'q': "trashed=true"}).GetList(): # nhu cu la: 'q': "'root' in parents and trashed=true"
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
                'alternateLink': file['alternateLink'],
                'title': file['title'],
                'modifiedDate': datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
                'parents': file['parents'],
                'md5Checksum': file.get('md5Checksum'),
                'type': file['mimeType'],
                'fileSize': file.get('fileSize') if file.get('fileSize') else '',
                'typeShow': None,
                'isFolder': 'folder' if file['mimeType'] == 'application/vnd.google-apps.folder' else 'file'
            }
            dicts.append(result)

        return dicts


def f_open(folder):
    os.system('xdg-open "%s"' % config_utils.get_dir_sync_location())


def check_remote_dir_files_sync(drive,remote_folder_id, local_folder):
    remote_dir_files_list = f_list(drive, remote_folder_id, True)
    local_dir_files_list = f_list_local(local_folder,True)

    if(len(remote_dir_files_list) != len(local_dir_files_list)):
        return False
    else:
        count = 0
        for remote_file in remote_dir_files_list:
            for local_file in local_dir_files_list:
                if remote_file['title'] == local_file['title']:
                    if remote_file['md5Checksum']:
                        if remote_file['md5Checksum'] == local_file['md5Checksum']:
                            count+=1
                            break
                    elif remote_file['fileSize'] == remote_file['fileSize']:
                        count+=1
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
        elif  common_utils.isImageFile(file):
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

