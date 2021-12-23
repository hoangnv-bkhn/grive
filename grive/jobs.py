import os
import sys
import pwd
import json
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

            gdrive_job = cron.new(
                command='/usr/bin/python3 %s -by_cron' % os.path.join(common_utils.dir_path, 'main.py'),
                comment='start Grive')

            # # when not run as drive_sync from command line
            # if __package__ is None:
            #     gdrive_job = cron.new(command='%s -by_cron' % os.path.join(common_utils.dir_path, 'main.py'),
            #                           comment='start Grive')
            # # when run as package from command line
            # else:
            #     gdrive_job = cron.new(command='grive -by_cron', comment='start Grive')

            gdrive_job.minute.every(1)  # setting to run every five minutes
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
    """
    Modified para get the file_id to save in the same directory
    """
    # traversing through all upload folders

    folder = config_utils.get_dir_sync_location()
    # print(folder)
    # stores if the file is being uploaded
    uploading = {}

    # load if status.json exists in the folder
    path = os.path.join(folder, "status.json")
    if os.path.exists(path):
        with open(path, 'r') as f_input:
            uploading = json.load(f_input)

    print(uploading)
    to_up = []  # stores files/folders to be uploaded by this cron instance
    for f in os.listdir(folder):
        if f not in uploading:
            uploading[f] = False
            print("check1")

        # check if the file is not being uploaded
        if not uploading[f]:
            to_up.append(f)
            uploading[f] = True
            print("check2")

    # saving back the status of files
    try:
        print(path)
        with open(path, 'w') as f_output:
            print(uploading)
            json.dump(uploading, f_output)
            print("check3")
    except IOError:
        print("Error: insufficient permission to write to %s" % folder)
        return

    print(to_up)
    # processing upload queue
    for item in to_up:
        # ignoring status.json
        if item == "status.json":
            continue

        drive_utils.f_up(drive, os.path.join(folder, item), file_id)

        # remove uploaded item from status.json
        # with open(path, 'r') as f_input:
        #     uploading = json.load(f_input)
        # del uploading[item]
        # with open(path, 'w') as f_output:
        #     json.dump(uploading, f_output)
