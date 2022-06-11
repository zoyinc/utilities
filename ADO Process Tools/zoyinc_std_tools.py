#
# Standard tools
# ==============
#

import logging

def enableLogging(consoleLogLevelRaw, fileLogLevelRaw, logFilename):

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Misc
    consoleLogLevel = consoleLogLevelRaw.upper().strip()
    fileLogLevel = fileLogLevelRaw.upper().strip()
    validLogLevels = ['DEBUG','INFO','WARNING','ERROR','CRITICAL']

    # Enable logging handlers
    consoleLogHandler = logging.StreamHandler()
    fileLogHandler = logging.FileHandler(logFilename, mode='a', encoding=None, delay=False, errors=None)

    # Log formatters
    consoleLogHandler.setFormatter(logging.Formatter('%(message)s'))
    fileLogHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y/%m/%d %H:%M:%S'))
    
    # Set logging levels
    if consoleLogLevel in validLogLevels:
        print('# Setting console log level of ' + consoleLogLevel)
        consoleLogHandler.setLevel(logging.DEBUG)
    else:
        print('#', flush=True)
        print('# Console log level \'' + consoleLogLevel + '\' is invalid!', flush=True)
        print('#', flush=True)
        exit(1)
    if fileLogLevel in validLogLevels:
        print('# Setting file log level of ' + consoleLogLevel)
        fileLogHandler.setLevel(logging.DEBUG)
    else:
        print('#', flush=True)
        print('# File log level \'' + fileLogLevel + '\' is invalid!', flush=True)
        print('#', flush=True)
        exit(1)

    # Add handlers to logger
    logger.addHandler(consoleLogHandler)
    logger.addHandler(fileLogHandler)

    return logger