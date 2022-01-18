import io
import os.path
import sys
import threading
import time
import timeit
from datetime import datetime
import json
from console_progressbar import ProgressBar

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
    import auth_utils
except ImportError:
    from . import common_utils
    from . import config_utils
    from . import auth_utils


def get_all_remote_folder(service):
    query_all_folders = "mimeType='application/vnd.google-apps.folder' and trashed = false and 'me' in owners"
    all_folders = query_google_api(service, query_all_folders)

    return all_folders


def get_files_in_folder(service, folder_id):
    result = []
    folder_tree = get_folder_tree(service)
    folders = []
    if folder_id in folder_tree:
        folders.append(folder_id)
        for elem in folder_tree[folder_id]:
            folders.append(elem)
    if len(folders) > 0:
        chunks = common_utils.chunks(folders, 100)
        for elem in chunks:
            query = '('
            for i in range(len(elem) - 1):
                query += "'" + elem[i] + "' in parents or "
            query += "'" + elem[len(elem) - 1] + "'" + " in parents) "
            query += "and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            # print(query)
            result += query_google_api(service, query)
    return result


def get_raw_data(service, instance, recursive):
    result = []
    if recursive:
        if instance == 'root':
            query = "trashed = false and 'me' in owners"
            result = query_google_api(service, query)
            return result
        else:
            folder_tree = get_folder_tree(service)
            folders = []
            if instance in folder_tree:
                folders.append(instance)
                for elem in folder_tree[instance]:
                    folders.append(elem)
            if len(folders) > 0:
                chunks = common_utils.chunks(folders, 100)
                for elem in chunks:
                    query = ''
                    for i in range(len(elem) - 1):
                        query += "'" + elem[i] + "'" + " in parents and trashed = false or "
                    query += "'" + elem[len(elem) - 1] + "'" + " in parents "
                    query += "and trashed = false"
                    # print(query)
                    result += query_google_api(service, query)
            return result

    else:
        if instance == 'root':
            query = "'root' in parents and trashed = false"
            result = query_google_api(service, query)
            return result
        elif instance == 'trash':
            query = "trashed = true"
            result = query_google_api(service, query)
            return result
        else:
            try:
                query = "'%s' in parents and trashed = false" % instance
                result = query_google_api(service, query)
            except:
                print(" %s is an invalid id !" % instance)

        return result


# def download(service, file_id, file_name, save_location, mimetype=None):
def download(instance):
    try:
        # print("Thread : {}".format(threading.current_thread().name))
        creds = auth_utils.get_user_credential()
        service = build('drive', 'v2', credentials=creds)

        if instance.get('mimeType') is not None:
            request = service.files().export_media(fileId=instance.get('id'),
                                                   mimeType=instance.get('mimeType'))
        else:
            request = service.files().get_media(fileId=instance.get('id'))

        fd = io.BytesIO()
        download_rate = config_utils.get_network_limitation('download')
        if not download_rate:
            downloader = MediaIoBaseDownload(fd=fd, request=request)
            done = False
            pb = ProgressBar(total=100, prefix='Downloading ' + instance.get('title'), decimals=3, length=50, fill='X',
                             zfill='-')
            while done is False:
                status, done = downloader.next_chunk()
                # print("Download %s %d%%." % (instance.get('title'), int(status.progress() * 100)))
                pb.print_progress_bar(int(status.progress() * 100))
        else:
            downloader = MediaIoBaseDownload(fd=fd, request=request, chunksize=download_rate * 1024)
            done = False
            while done is False:
                start = timeit.default_timer()
                status, done = downloader.next_chunk()
                print("Download %s %d%%." % (instance.get('title'), int(status.progress() * 100)))
                stop = timeit.default_timer()
                processing_time = stop - start
                if processing_time < 0.95:
                    time.sleep(0.95 - processing_time)

        fd.seek(0)
        with open(instance.get('saveLocation'), 'wb') as f:
            f.write(fd.read())
            f.close()
    except:
        return False

    os.setxattr(instance.get('saveLocation'), 'user.id', str.encode(instance.get('id')))
    stats = os.stat(instance.get('saveLocation'))
    os.utime(instance.get('saveLocation'), (stats.st_atime, common_utils.utc2local(
        datetime.strptime(instance.get('modifiedDate'), '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))

    return True


def upload(instance):
    try:
        creds = auth_utils.get_user_credential()
        service = build('drive', 'v2', credentials=creds)
        filename = instance.get('title')
        path = instance.get('path')
        try:
            f_exclusive = os.getxattr(path, 'user.excludeUpload')
            f_exclusive = f_exclusive.decode()
        except:
            f_exclusive = None
        if f_exclusive is not None:
            if f_exclusive == 'True':
                return True
        parent_id = instance.get('parent_id')
        set_id = instance.get('set_id')
        with open(common_utils.format_dict) as f:
            format_add = json.load(f)
        check_type = format_add.get(instance.get('mimeType'))
        upload_rate = config_utils.get_network_limitation('upload')
        if not upload_rate:
            media_body = MediaFileUpload(path, chunksize=275000, resumable=True)
        else:
            media_body = MediaFileUpload(path, chunksize=upload_rate * 1024, resumable=True)
        if check_type is not None:
            body = {
                'title': os.path.splitext(filename)[0],
                'mimeType': instance.get('mimeType')
            }
        else:
            body = {
                'title': filename
            }
        # Set the parent folder.
        if parent_id is not None:
            body['parents'] = [{'id': parent_id}]
        file = service.files().insert(body=body, media_body=media_body, fields='id')
        response = None
        while response is None:
            status, response = file.next_chunk()
            if status:
                start = timeit.default_timer()
                print("Upload %s file %d%% complete." % (filename, int(status.progress() * 100)))
                stop = timeit.default_timer()
                processing_time = stop - start
                if processing_time < 0.95:
                    time.sleep(0.95 - processing_time)
        file = service.files().get(fileId=response.get('id')).execute()
        if set_id is True:
            os.setxattr(path, 'user.id', str.encode(response.get('id')))
            stats = os.stat(path)
            os.utime(path, (stats.st_atime, common_utils.utc2local(
                datetime.strptime(file.get('modifiedDate'), '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
        print("Upload %s file complete." % filename)
        return True
    except:
        return False


def update_file(service, file_id, path, option):
    """
    Args:
        option: True when update file, False when rename file

    Returns:
        True or False
    """
    try:
        f_exclusive = os.getxattr(path, 'user.excludeUpload')
        f_exclusive = f_exclusive.decode()
    except:
        f_exclusive = None
    if f_exclusive is not None:
        if f_exclusive == 'True':
            return True
    try:
        # First retrieve the file from the API.
        file = service.files().get(fileId=file_id).execute()

        with open(common_utils.format_dict) as f:
            format_add = json.load(f)
        check_type = format_add.get(file.get('mimeType'))
        filename = common_utils.get_file_name(path)
        if check_type is not None:
            filename = os.path.splitext(filename)[0]
        # File's new metadata.
        file['title'] = filename

        if option is True:
            # File's new content.
            media_body = MediaFileUpload(path, resumable=True)
            updated_file = service.files().update(
                fileId=file_id,
                body=file,
                media_body=media_body).execute()
            print("Upload %s file complete." % filename)
        else:
            updated_file = service.files().patch(
                fileId=file_id,
                body=file,
                fields='title').execute()
            print("Update %s file complete." % filename)
        stats = os.stat(path)
        os.utime(path, (stats.st_atime, common_utils.utc2local(
            datetime.strptime(updated_file.get('modifiedDate'), '%Y-%m-%dT%H:%M:%S.%fZ')).timestamp()))
        return True
    except:
        return None


def move_file_remote(service, file_id, parent_id):
    # Retrieve the existing parents to remove
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join([parent["id"] for parent in file.get('parents')])
    # Move the file to the new folder
    file = service.files().update(fileId=file_id,
                                  addParents=parent_id,
                                  removeParents=previous_parents,
                                  fields='id, parents').execute()
    print("Moved %s complete." % file_id)
    return True


def get_folder_tree(service):
    tree = dict()
    folders = get_all_remote_folder(service)
    for elem in folders:
        if elem['id'] not in tree:
            tree[elem['id']] = []
    for elem in folders:
        if len(elem['parents']) > 0 and elem['parents'][0]['id'] in tree:
            tree[elem['parents'][0]['id']].append(elem['id'])
    return tree


def get_cloud_path(all_folders, instance_id, path=None):
    check = False
    elem = {}
    if path is None:
        path = []
    for folder in all_folders:
        if folder.get('id') == instance_id:
            check = True
            elem['id'] = folder.get('id')
            elem['name'] = folder.get('title')
            elem['parents_id'] = folder.get('parents')[0]['id']
            path.insert(0, elem)
    if check:
        get_cloud_path(all_folders, elem.get('parents_id'), path)
    else:
        return False
    # print(path)


def get_local_path(service, instance_id, sync_dir):
    """Get tree folder from cloud of this instance.

            :param service: Google Drive instance
            :param instance_id: id of file or folder
            :param sync_dir: default sync directory

            :returns: corresponding canonical path of instance locally
    """
    try:
        instance = service.files().get(fileId=instance_id).execute()
        instance_parent = instance.get('parents')[0]['id']
        # print(instance_parent)
        rel_path = []
        all_folders = get_all_remote_folder(service)
        get_cloud_path(all_folders, instance_parent, rel_path)
        # print(rel_path)

        for p in rel_path:
            check = False
            for file in os.listdir(sync_dir):
                try:
                    if os.getxattr(os.path.join(sync_dir, file), 'user.id').decode() == p['id']:
                        check = True
                        sync_dir = os.path.join(sync_dir, file)
                except:
                    continue

            if not check:
                if os.path.exists(os.path.join(sync_dir, p['name'])):
                    sync_dir = common_utils.get_dup_name(sync_dir, p['name'])
                else:
                    sync_dir = os.path.join(sync_dir, p['name'])
                common_utils.dir_exists(sync_dir)
                os.setxattr(sync_dir, 'user.id', str.encode(p['id']))

        # dir_exists(sync_dir)
        # print(sync_dir)
        return sync_dir
    except:
        return None


def query_google_api(service, query):
    result = []
    page_token = None
    while True:
        response = service.files().list(q=query,
                                        spaces='drive',
                                        fields='nextPageToken, items',
                                        pageToken=page_token).execute()
        for file in response.get('items', []):
            # print(file['title'], file['id'])
            result.append(file)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return result


def retrieve_all_changes(service, start_change_id=None):
    """Retrieve a list of Change resources.

    Args:
      service: Drive API service instance.
      start_change_id: ID of the change to start retrieving subsequent changes
                       from or None.
    Returns:
      List of Change resources.
    """
    result = []
    page_token = None
    while True:
        try:
            param = {}
            if start_change_id:
                param['startChangeId'] = start_change_id
            if page_token:
                param['pageToken'] = page_token
            changes = service.changes().list(**param).execute()

            for file in changes['items']:
                result.append({
                    'id': file['fileId'],
                    'c_time': datetime.strptime(file['modificationDate'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                })

            page_token = changes.get('nextPageToken')
            if not page_token:
                break
        except:
            break
    return result
