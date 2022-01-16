import io
import os.path
import sys

from googleapiclient import errors
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import HttpRequest

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import config_utils
except ImportError:
    from . import common_utils
    from . import config_utils


def get_all_remote_folder(service):
    result = []
    page_token = None
    while True:
        response = service.files().list(q="mimeType='application/vnd.google-apps.folder' and trashed = false",
                                        spaces='drive',
                                        fields='nextPageToken, items',
                                        pageToken=page_token).execute()
        for file in response.get('items', []):
            result.append(file)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return result


def get_files_in_folder(service, folder_id):
    result = []
    folder_tree = get_folder_tree(service)
    folders = []
    if folder_id in folder_tree:
        folders.append(folder_id)
        for elem in folder_tree[folder_id]:
            folders.append(elem)
    if len(folders) > 0:
        chunks = common_utils.chunks(folders, 10)
        for elem in chunks:
            query = ''
            for i in range(len(elem) - 1):
                query += "'" + elem[i] + "'" + " in parents and trashed = false or "
            query += "'" + elem[len(elem) - 1] + "'" + " in parents "
            query += "and trashed = false"
            # print(query)
            result.append(query_google_api(service, query))
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
                chunks = common_utils.chunks(folders, 10)
                for elem in chunks:
                    query = ''
                    for i in range(len(elem) - 1):
                        query += "'" + elem[i] + "'" + " in parents and trashed = false or "
                    query += "'" + elem[len(elem) - 1] + "'" + " in parents "
                    query += "and trashed = false"
                    # print(query)
                    result.append(query_google_api(service, query))
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


def download(service, file_id, save_location, mimetype=None):
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
            print("Download %d%%." % int(status.progress() * 100))
        fd.seek(0)

        with open(save_location, 'wb') as f:
            f.write(fd.read())
            f.close()
    except:
        return False

    return True


def upload(service, path, parent_id, mime_type):
    try:
        filename = common_utils.get_file_name(path)
        if mime_type is None:
            media_body = MediaFileUpload(path, chunksize=1024 * 1024, resumable=True)
        else:
            media_body = MediaFileUpload(path, mimetype=mime_type, resumable=True)
        body = {
            'title': filename
        }
        # Set the parent folder.
        if parent_id:
            body['parents'] = [{'id': parent_id}]
        # upload_rate = config_utils.get_network_limitation('upload')
        # if upload_rate:
        #     media_body.__init__(chunksize=upload_rate)
        file = service.files().insert(
            body=body,
            media_body=media_body)
        response = None
        while response is None:
            status, response = file.next_chunk()
            if status:
                sys.stdout.write("\rUpload %d%% complete." % int(status.progress() * 100))
                sys.stdout.flush()
        return True
    except errors.HttpError as error:
        print(error)
        return False


def get_folder_tree(service):
    tree = dict()
    folders = get_all_remote_folder(service)
    for elem in folders:
        if elem['id'] not in tree:
            tree[elem['id']] = []
    for elem in folders:
        if elem['parents'][0]['id'] in tree:
            tree[elem['parents'][0]['id']].append(elem['id'])
    return tree


def query_google_api(service, query):
    result = []
    page_token = None
    while True:
        response = service.files().list(q=query,
                                        spaces='drive',
                                        fields='nextPageToken, items',
                                        pageToken=page_token).execute()
        for file in response.get('items', []):
            result.append(file)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return result
