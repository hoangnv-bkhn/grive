import os
import sys
import pwd
import hashlib
import json
from datetime import datetime
from crontab import CronTab

try:
    # set directory for relativistic import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import common_utils
    import drive_utils
    import config_utils
except ImportError:
    from . import common_utils
    from . import drive_utils
    from . import config_utils


# returns current username
def get_username():
    return pwd.getpwuid(os.getuid())[0]


# cron progress execution from crontab
def cron_process(arg):
    if arg == "start":
        # add cron script if cron not running
        if not is_running(False):
            cron = CronTab(user=get_username())

            # gdrive_job = cron.new(
            #     command='/usr/bin/python3 %s -by_cron' % os.path.join(common_utils.dir_path, 'main.py'),
            #     comment='start Grive')

            # when not run as drive_sync from command line
            if __package__ is None:
                gdrive_job = cron.new(command='/usr/bin/python3 %s -by_cron' % os.path.join(common_utils.dir_path, 'main.py'),
                                      comment='start Grive')
            # when run as package from command line
            else:
                gdrive_job = cron.new(command='grive -by_cron', comment='start Grive')

            gdrive_job.minute.every(config_utils.get_sync_cycle())  # setting to run every n minutes
            cron.write()
            print("Grive started")

        else:
            print("Grive is already running")

    elif arg == "stop":
        # removing gdrive_job from cron
        if not is_running(True):
            print("Error: Grive is not running")

    elif arg == "status":
        # print the current status of cron
        if is_running(False):
            print("Grive is running in background")
        else:
            print("Grive is not running in background")


# returns true if GDrive_Sync is running
def is_running(remove):  # remove tells if the function was called from stop
    running = False
    cron = CronTab(user=get_username())
    for job in cron:
        # print(job)
        if job.comment == 'start Grive':
            if remove:
                cron.remove(job)
                print("Grive stopped")
            running = True

    cron.write()
    return running


# code to be launched by cron periodically
def by_cron(drive, file_id=None):

    sync_dir = config_utils.get_dir_sync_location()
    # stores if the file is being uploaded
    uploading = {}

    remote_files = drive_utils.f_list(drive, "root", 1)
    # print(remote_files[0]['modifiedDate'])

    # datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ'))

    subfolders, local_files = common_utils.run_fast_scandir(config_utils.get_dir_sync_location())

    dicts = []
    for file in remote_files:
        res = {
            'storageLocation': 'remote',
            'id': file['id'],
            'alternateLink': file['alternateLink'],
            'title': file['title'],
            'modifiedDate': common_utils.utc2local(datetime.fromtimestamp(file['modifiedDate'])),
            'parents': file['parents'],
            'md5Checksum': file.get('md5Checksum')
        }
        dicts.append(res)
    for file in dicts:
        if file['title'] == 'data':
            print(file['id'], file['title'], file.get('md5Checksum'), file['modifiedDate'])

    dicts2 = []
    # datetime.utcfromtimestamp(stats.st_mtime)
    for file in local_files:
        # print(file)
        stats = os.stat(file)
        # print(stats)
        res = {
            'storageLocation': 'local',
            'title': common_utils.get_file_name(file),
            'canonicalPath': file,
            'modifiedDate': datetime.fromtimestamp(stats.st_mtime),
            'accessedDate': datetime.fromtimestamp(stats.st_atime),
            'changedDate': datetime.fromtimestamp(stats.st_ctime),
            'md5Checksum': hashlib.md5(open(file, 'rb').read()).hexdigest(),
            'excludeUpload': 'false'
        }
        dicts2.append(res)
    for file in dicts2:
        if file['title'] == 'data':
            print('title', file['title'])
            print('Checksum', file.get('md5Checksum'))
            print("modified: ", file['modifiedDate'])
            print("access: ", file['accessedDate'])
            print("changed: ", file['changedDate'])



    # if os.path.exists(common_utils.config_folder):
    #     path = os.path.join(common_utils.config_folder, "metadata_file.json")
    #     with open(path, 'w') as metadata_file:
    #         dicts = []
    #         for file in remote_files:
    #             dict = {
    #                 'storageLocation': 'remote',
    #                 'id': file['id'],
    #                 'alternateLink': file['alternateLink'],
    #                 'title': file['title'],
    #                 'modifiedDate': datetime.timestamp(datetime.strptime(file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')),
    #                 'parents': file['parents'],
    #                 'md5Checksum': file.get('md5Checksum')
    #             }
    #             dicts.append(dict)
    #         for file in dicts:
    #             print(file['title'], file.get('md5Checksum'), file['modifiedDate'])

            # datetime.utcfromtimestamp(stats.st_mtime)
            # for file in local_files:
            #     # print(file)
            #     stats = os.stat(file)
            #     dict = {
            #         'storageLocation': 'local',
            #         'title': common_utils.get_file_name(file),
            #         'canonicalPath': file,
            #         'modifiedDate': stats.st_mtime,
            #         'md5Checksum': hashlib.md5(open(file, 'rb').read()).hexdigest(),
            #         'excludeUpload': 'false'
            #     }
            #     dicts.append(dict)

            # json.dump(dicts, metadata_file, default=str)



    # for f in os.listdir(sync_dir):
    #     print(f)

    # load if status.json exists in the folder
    # path = os.path.join(folder, "status.json")
    # if os.path.exists(path):
    #     with open(path, 'r') as f_input:
    #         uploading = json.load(f_input)

    # drive_utils.f_sync(drive)

    # traversing through all upload folders

    # folder = config_utils.get_dir_sync_location()
    # # print(folder)
    # # stores if the file is being uploaded
    # uploading = {}
    #
    # # load if status.json exists in the folder
    # path = os.path.join(folder, "status.json")
    # if os.path.exists(path):
    #     with open(path, 'r') as f_input:
    #         uploading = json.load(f_input)
    #
    # print(uploading)
    # to_up = []  # stores files/folders to be uploaded by this cron instance
    # for f in os.listdir(folder):
    #     if f not in uploading:
    #         uploading[f] = False
    #
    #     # check if the file is not being uploaded
    #     if not uploading[f]:
    #         to_up.append(f)
    #         uploading[f] = True
    #
    # # saving back the status of files
    # try:
    #     with open(path, 'w') as f_output:
    #         print(uploading)
    #         json.dump(uploading, f_output)
    # except IOError:
    #     print("Error: insufficient permission to write to %s" % folder)
    #     return
    #
    # print(to_up)
    # if len(to_up) > 0 :
    #     drive_utils.f_sync(drive)
    # processing upload queue
    # for item in to_up:
    #     # ignoring status.json
    #     if item == "status.json":
    #         continue

        # drive_utils.f_up(drive, os.path.join(folder, item), file_id)

        # remove uploaded item from status.json
        # with open(path, 'r') as f_input:
        #     uploading = json.load(f_input)
        # del uploading[item]
        # with open(path, 'w') as f_output:
        #     json.dump(uploading, f_output)
