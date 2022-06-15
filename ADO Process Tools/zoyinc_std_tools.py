#
# Standard tools
# ==============
#

import logging
import requests
import sys
import json

#
# Azure DevOps REST api call
#
# Requests docs: https://requests.readthedocs.io/en/latest/api/
#
def adoAPICall(logger, requestURL, requestTypeRaw, requestParams, requestData, requestHeaders, requestProxies, azureToken, failOnError):

    currFunction = __name__ + '.adoAPICall()'
    logger.debug('running function ' + currFunction)
    errorsFound = False

    requestType = requestTypeRaw.upper()
    if requestType not in ['GET', ]:
        logger.error('#')
        logger.error('# Request type \'' + requestType + '\' not currently supported in this function \'' + currFunction + '\'.')
        logger.error('#')
        sys.stdout.flush()
        exit(1)

    if requestType == 'GET':
        logger.debug('Making request.' + requestType.lower() + '() call')
        logger.debug('URL: ' + requestURL)
        try:
            adoResponse = requests.get(requestURL, params=requestParams, data=requestData, headers=requestHeaders, proxies = requestProxies, auth=('', azureToken), )
            logger.debug('Response.content: ' + str(adoResponse.content))
        except requests.exceptions.ProxyError as e:
            errorsFound = True
            errorMsg = 'Failed to load json response.\nError:' + str(e)       

    # Check the response
    if not errorsFound: 
        if adoResponse.status_code == 200:        
            try:
                responseJson = json.loads(adoResponse.content)
            except ValueError as e:
                errorsFound = True
                errorMsg = 'Failed to load json response.\nError:' + str(e)
                logger.error('# Error making api call: ' + errorMsg)
        else:
            if failOnError:
                errorsFound = True                
                errorMsg = 'api returned response code: ' + str(adoResponse.status_code) + '\nThe response was:\n' + str(adoResponse.content)
                logger.error('# Error making api call: ' + errorMsg)
        
    if errorsFound:
        if failOnError:
            # If fail on an error
            responseJson = {'errorMsg':errorMsg, 'success':False}
            logger.error('#')
            logger.error('# Error running ' + currFunction)
            logger.error('#')
            for currLine in errorMsg.splitlines():
                logger.error(currLine)
            logger.error('')
            sys.stdout.flush()
            exit(1)
        else:
            # If do not fail on error
            logger.error('#')
            logger.error('# Error running ' + currFunction)
            logger.error('# failOnError is set to False, so we won\'t fail, however the error is:')
            logger.error('#')
            for currLine in errorMsg.splitlines():
                logger.error(currLine)
            logger.error()
            sys.stdout.flush()
    
    if errorsFound:
        adoApiReturn = {'json':None,
                    'status_code':adoResponse.status_code,
                    'content':adoResponse.content,
                    'errorMsg':errorMsg,
                    'success':False}
    else:
        adoApiReturn = {'json':responseJson,
                    'status_code':adoResponse.status_code,
                    'content':adoResponse.content,
                    'errorMsg':None,
                    'success':True}
    
    return adoApiReturn


#
# Enable logging
#
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
        consoleLogHandler.setLevel(consoleLogLevel)
    else:
        print('#', flush=True)
        print('# Console log level \'' + consoleLogLevel + '\' is invalid!', flush=True)
        print('#', flush=True)
        exit(1)
    if fileLogLevel in validLogLevels:
        fileLogHandler.setLevel(fileLogLevel)
    else:
        print('#', flush=True)
        print('# File log level \'' + fileLogLevel + '\' is invalid!', flush=True)
        print('#', flush=True)
        exit(1)

    # Add handlers to logger
    logger.addHandler(consoleLogHandler)
    logger.addHandler(fileLogHandler)

    return logger