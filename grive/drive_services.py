import io
import os.path
import sys

from googleapiclient.http import MediaIoBaseDownload
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


def download(service, file_id, file_name, save_location, mimetype=None):
    try:
        if mimetype is not None:
            request = service.files().export_media(fileId=file_id,
                                                   mimeType=mimetype)
        else:
            request = service.files().get_media(fileId=file_id)

        fd = io.BytesIO()
        download_rate = config_utils.get_network_limitation('download')
        if not download_rate:
            downloader = MediaIoBaseDownload(fd=fd, request=request)
        else:
            downloader = MediaIoBaseDownload(fd=fd, request=request, chunksize=download_rate)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %s %d%%." % (file_name, int(status.progress() * 100)))
        fd.seek(0)

        with open(save_location, 'wb') as f:
            f.write(fd.read())
            f.close()
    except:
        return False

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


def get_local_path(service, instance_id, sync_dir):
    """Get tree folder from cloud of this instance.

            :param service: Google Drive instance
            :param instance_id: id of file or folder
            :param sync_dir: default sync directory

            :returns: corresponding canonical path of instance locally
    """
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
