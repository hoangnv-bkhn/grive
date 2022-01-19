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

            startup_on_boot = config_utils.get_auto_start_status()
            if startup_on_boot:
                # when not run as drive_sync from command line
                if __package__ is None:
                    gdrive_job = cron.new(
                        command='@reboot /usr/bin/python3 %s -by_cron' % os.path.join(common_utils.dir_path, 'main.py'),
                        comment='start Grive')
                # when run as package from command line
                else:
                    gdrive_job = cron.new(command='@reboot grive -by_cron', comment='start Grive')
            else:
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
def by_cron(service):
    drive_utils.f_sync(service, None)