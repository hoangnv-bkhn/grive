import logging
import logging.handlers as handlers
import os

try:
    import common_utils
except:
    from . import common_utils

logger = logging.getLogger("Grive")
logger.setLevel(logging.DEBUG)
common_utils.dir_exists(os.path.join(os.environ['HOME'], '.grive'))
log_path = os.path.join(os.environ['HOME'], '.grive/grive.log')
if not os.path.exists(log_path):
    print(log_path)
    with open(log_path, 'w+') as fp:
        pass
# fh = logging.FileHandler(log_path)
# fh.setLevel(logging.DEBUG)
# logHandler = handlers.RotatingFileHandler('app.log', maxBytes=5)
logHandler = logging.handlers.RotatingFileHandler(log_path, maxBytes= 5* 1024 * 1024, backupCount=5)
# logHandler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

def send_to_log(LogType, LogMsg):
    if 3 >= LogType:
        if LogType == 3:
            logger.debug(LogMsg)
        if LogType == 2:
            logger.info(LogMsg)
        if LogType == 1:
            logger.error(LogMsg)
