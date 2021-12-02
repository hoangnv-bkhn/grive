from pkg_resources import resource_filename
# stores default file address
import os
import ntpath
import errno
from pydrive import settings

#huy
from crontab import CronTab
import pwd

dir_path = os.path.dirname(os.path.realpath(__file__))
home = os.path.expanduser("~")

#huy
try:
    config_file = os.path.join(dir_path, "config_dicts/config.json")
# when launched as package
except settings.InvalidConfigError or OSError:
    config_file = resource_filename(__name__, "config_dicts/config.json")
# returns current username
def get_username():
    return pwd.getpwuid(os.getuid())[0]

try:
    client_secrets = os.path.join(dir_path, "credential.json")
except settings.InvalidConfigError or OSError:
    client_secrets = resource_filename(__name__, "credential.json")

def get_credential_file():
    # when launched as non-package
    try:
        return os.path.join(home, "credential.json")
        # return os.path.join(dir_path, "credential.json")
    # when launched as package
    except settings.InvalidConfigError or OSError:
        return os.path.join(home, "credential.json")

# Extracts file name or folder name from full path
def get_f_name(addr):
    if os.path.exists(addr):
        head, tail = ntpath.split(addr)
        return tail or ntpath.basename(head)  # return tail when file, otherwise other one for folder
    else:
        raise TypeError("addr not valid")

#huy
def dir_exists(addr):
    if not os.path.exists(addr):
        try:
            os.makedirs(addr)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
# returns true if GDrive_Sync is running
def is_running(remove):  # remove tells if the function was called from stop
    running = False
    cron = CronTab(user=get_username())
    for job in cron:
        if job.comment == 'start GDrive_Sync':
            if remove:
                cron.remove(job)
                print("GDrive_Sync stopped")
            running = True
    cron.write()
    return running

# cron progress execution from crontab
def cron_process(arg):
    if arg == "start":
        # add cron script if cron not running
        if not is_running(False):
            cron = CronTab(user=get_username())
            # when not run as drive_sync from command line
            if __package__ is None:
                gdrive_job = cron.new(command='%s -by_cron' % os.path.join(file_add.dir_path, 'main.py'),
                                      comment='start GDrive_Sync')
            # when run as package from command line
            else:
                gdrive_job = cron.new(command='drive_sync -by_cron', comment='start GDrive_Sync')
            gdrive_job.minute.every(5)  # setting to run every five minutes
            cron.write()
            print("GDrive_Sync started")

        else:
            print("GDrive_Sync is already running")

    elif arg == "stop":
        # removing gdrive_job from cron
        if not is_running(True):
            print("Error: GDrive_Sync is not running")

    elif arg == "status":
        # print the current status of cron

        if is_running(False):
            print("GDrive_Sync is running in background")
        else:
            print("GDrive_Sync is not running in background")