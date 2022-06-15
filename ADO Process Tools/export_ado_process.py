#
# Export an Azure DevOps process
# ==============================
#

import argparse
import logging
import sys
import json
from re import T
import zoyinc_std_tools

#
# User defined variables
#
consoleLogLevel = 'info'
fileLogLevel = 'debug'
logFilename = 'c:/temp/ado_process_logging.log'
proxySvr = 'http://192.168.202.245:80'
adoOrg = 'zoyinc'
adoProjectRaw = 'examples'
scriptOk = True

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-azuretoken", required=True, help="Azure personal access token PAL")

args = parser.parse_args()
azureToken = args.azuretoken
processDict = {}


#
# Misc variables
#
proxySvr = {'http':proxySvr, 'https':proxySvr}
logger = zoyinc_std_tools.enableLogging(consoleLogLevel,fileLogLevel,logFilename)
adoProject = adoProjectRaw.lower().strip()

# # Get list of projects in org
# adoApiUrl = 'https://dev.azure.com/' + adoOrg + '/_apis/projects?api-version=6.0'
# projectDetails = zoyinc_std_tools.adoAPICall(logger, adoApiUrl, 'get', None, None, None, proxySvr, azureToken, True)
# projectID = -1
# for curProject in projectDetails['json']['value']:
#     if adoProject == curProject['name'].lower().strip():
#             projectID = curProject['id']
#             logger.debug('Project ID for \'' + adoProjectRaw + '\' = \'' + projectID + '\'.')
# if projectID == -1:
#     errorMsg = 'Given project name, \'' + adoProjectRaw + '\', does not exist in the \'' + adoOrg + '\' organization.'
#     scriptOk = False

# Get list of processes in org
adoApiUrl = 'https://dev.azure.com/' + adoOrg + '/_apis/work/processes?api-version=6.0-preview.2'
processDetails = zoyinc_std_tools.adoAPICall(logger, adoApiUrl, 'get', None, None, None, proxySvr, azureToken, True)
processDict.update({'process':{}})
for curProcess in processDetails['json']['value']:
    processDict['process'].update({curProcess['name'].lower():curProcess})
print( json.dumps(processDict, indent=4, sort_keys=True))


if scriptOk:
    logger.info('Script completed successfully.')
else:
    logger.error('#')
    logger.error('# Script failed with the following error')
    logger.error('#')
    for currLine in errorMsg.splitlines():
        logger.error(currLine)
    logger.error('')
    sys.stdout.flush()
    exit(1)
