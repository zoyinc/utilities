#
# In order to share variables between phases and tasks we make API calls
# to update release variables.
#
#

import requests
import json
import copy
import re
import sys
import argparse
import os
from datetime import datetime

notFoundStr = 'NOT_FOUND'
currRelease = os.environ.get('RELEASE_RELEASEID', notFoundStr)
teamProjectName = os.environ.get('SYSTEM_TEAMPROJECT', notFoundStr)
teamFoundationServerURL = os.environ.get('SYSTEM_TEAMFOUNDATIONSERVERURI', notFoundStr)

#
# Import arguments and environment properties etc
#
parser = argparse.ArgumentParser()
parser.add_argument("-azuretoken", required=True, help="Azure personal access token PAL")
parser.add_argument('-t', action='store_true')
args = parser.parse_args()
azureToken = args.azuretoken
testMode = False
if args.t:
    testMode = True

#
# If running in test mode set test values
#
if testMode:
    currRelease = '67'
    currStage = 'PRD'
    teamProjectName = 'Examples'
    teamFoundationServerURL = 'https://vsrm.dev.azure.com/zoyinc/'

if ((currRelease == notFoundStr) or (teamProjectName == notFoundStr) or (teamFoundationServerURL == notFoundStr)):
    print('##[error]')
    print('##[error] Something went wrong, could not determine some or all environment variables')
    print('##[error]')
    print('currRelease:              ' + currRelease)
    print('teamProjectName:          ' + teamProjectName)
    print('teamFoundationServerURL:  ' + teamFoundationServerURL)
    quit(1)

azureReleaseURL = teamFoundationServerURL + teamProjectName + '/_apis/release/releases/' + currRelease + '?api-version=5.0'

#
# Summary
#
print('#')
print('# Running Global Pipeline Variables Healthcheck')
print('# =============================================')
print('# Current release:             ' + currRelease)
print('# Team project name:           ' + teamProjectName)
print('# Team foundation server URL:  ' + teamFoundationServerURL)
print('# Date:                ' + datetime.now().strftime('%d/%m/%y %H:%M'))
print('#')
print('# Release URL:         ' + azureReleaseURL)
print('#')




##azureReleaseURL = 'https://vsrm.dev.azure.com/zoyinc/Examples/_apis/release/releases/' + currRelease + '?api-version=5.0'

print('Azure URL: ' + azureReleaseURL)
azureResponse = requests.get(azureReleaseURL, auth=('', azureToken))
if azureResponse.status_code != 200:
    print('##[error]')
    print('##[error] Could not connect to Azure')
    print('##[error]')
    print('URL:            ' + azureReleaseURL)
    print('Status code:    ' + str(azureResponse.status_code))
    print('Error received: ' + azureResponse.reason)
    quit(1)
    
releaseDetailOriginal = json.loads(azureResponse.text)

#
# Now need to go through all tasks and look for ones that include 'instructions'
#
# For the instructions field there is the concept of 'variable expand support' which is where
# you can put environment variables in the instructions using the standard format '$(MY_VAR)'
#
# For us we are going to have gobal environment variables and the names will be consistent:
#
#     $(GLOBALVAR_WELLINGTON_MIMSG2)
#
# GLOBALVAR_  = Standard prefixes for all our global variables (This is our convention no Azure)
# WELLINGTON  = The environment name, must be equal to the 'name' of the 'Stage' in the pipeline
# _           = There is always an underscore after the environment name
# MIMSG2      = The name of the variable, in this case it stands for Manual Intervention MeSsaGe 2
#
# First iterate over all stages
#
globalVarPatternStr = r'\$\(GLOBALVAR_.*\)'
globalVarPatternStrConditions = r'\'GLOBALVAR_.*?\''
problemsReport = ''
varIndentStr = '    '
for stageIndex, itemValue in enumerate(releaseDetailOriginal['environments']):
    
    currStageName = releaseDetailOriginal['environments'][stageIndex]['name']
    basicStageName = re.sub(r'( |_|\(|\)|-)','', currStageName).upper()
    #
    # Second iterate over all the phases in the current stage
    #
    for deployPhaseIndex, phaseValue in enumerate(releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot']):
        
        currPhaseName = releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['name']
        #
        # Now check the conditions on the phase to see if they include any
        # global variables
        #
        currPhaseCondition = releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['deploymentInput']['condition']
        if re.search(globalVarPatternStrConditions, currPhaseCondition, re.IGNORECASE):
            print()
            print('Found global variable/s in phase conditions')
            print(' - Current phase:       ' + currPhaseName)
            print(' - Current stage name:  ' + currStageName)
            print('   - variable format:   ' + basicStageName)  
            print('   - Phase condition:   ' + currPhaseCondition)                  
            print(' Variables:')
            
            envVarIter = re.finditer(globalVarPatternStrConditions, currPhaseCondition, re.IGNORECASE)
            for currEnvVarStr in envVarIter:         
                
                # Need to check it matches the stage name
                foundStageNameMatch = re.search(r'_(.*)_', currEnvVarStr.group(), re.IGNORECASE)
                
                if foundStageNameMatch:
                    foundStageName = foundStageNameMatch.group(0)[1:-1]
                    if foundStageName == basicStageName:
                        print(varIndentStr + currEnvVarStr.group() + ' - OK')
                    else:
                        errMsg1 = currEnvVarStr.group() + ' - ERROR  with global variable in phase condition. Stage = \'' + currStageName + '\', phase  = \'' + currPhaseName + '\', and condition \'' + currPhaseCondition + '\''
                        indentBlanks = ' ' * len(currEnvVarStr.group())
                        errMsg2 = indentBlanks + '   The stage name used for the variable is \'' + foundStageName + '\', which is different from the expected stage name \'' + basicStageName + '\'.'
                        print( varIndentStr + errMsg1)
                        print( varIndentStr + errMsg2)
                        problemsReport = problemsReport + errMsg1 + '\n' + errMsg2 + '\n'
                else:
                    errMsg = currEnvVarStr.group() + ' - ERROR no stage name found in the variable name.'
                    print( varIndentStr + errMsg)
                    problemsReport = problemsReport + errMsg + '\n'

            print()
        
        
        #
        # Third iterate over all the tasks in the current phase
        #
        for deployTaskIndex, taskValue in enumerate(releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['workflowTasks']):
            
            currTaskName = releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['workflowTasks'][deployTaskIndex]['name']
            
            # If the 'instructions' field exists then examine it
            currTaskInstructions = ''
            if 'instructions' in releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['workflowTasks'][deployTaskIndex]['inputs']:
                currTaskInstructions = str(releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['workflowTasks'][deployTaskIndex]['inputs']['instructions'])
                currTaskName = str(releaseDetailOriginal['environments'][stageIndex]['deployPhasesSnapshot'][deployPhaseIndex]['workflowTasks'][deployTaskIndex]['name'])
                if re.search(globalVarPatternStr, currTaskInstructions, re.IGNORECASE):
                    print()
                    print('Found global variable/s in instructions')
                    print(' - Current phase:       ' + currPhaseName)
                    print(' - Current stage name:  ' + currStageName)
                    print('   - variable format:   ' + basicStageName)                    
                    print(' Variables:')
                    
                    envVarIter = re.finditer(globalVarPatternStr, currTaskInstructions, re.IGNORECASE)
                    for currEnvVarStr in envVarIter:            
                        # Need to check it matches the stage name
                        foundStageNameMatch = re.search(r'_(.*)_', currEnvVarStr.group(), re.IGNORECASE)
                        
                        if foundStageNameMatch:
                            foundStageName = foundStageNameMatch.group(0)[1:-1]
                            if foundStageName == basicStageName:
                                print(varIndentStr + currEnvVarStr.group() + ' - OK')
                            else:
                                errMsg1 = currEnvVarStr.group() + ' - ERROR  with global variable in stage, \'' + currStageName + '\', in phase \'' + currPhaseName + '\', and task \'' + currTaskName + '\'.'
                                indentBlanks = ' ' * len(currEnvVarStr.group())
                                errMsg2 = indentBlanks + '   The stage name used for the variable is \'' + foundStageName + '\', which is different from the expected stage name \'' + basicStageName + '\'.'
                                print( varIndentStr + errMsg1)
                                print( varIndentStr + errMsg2)
                                problemsReport = problemsReport + errMsg1 + '\n' + errMsg2 + '\n'
                        else:
                            errMsg = currEnvVarStr.group() + ' - ERROR no stage name found in the variable name.'
                            print( varIndentStr + errMsg)
                            problemsReport = problemsReport + errMsg + '\n'

                    print()

#
# If errors print them out
#
if problemsReport != '':
    print('##[error]')
    print('##[error] Errors with the use of global pipeline variables were found')
    print('##[error]')
    print(problemsReport)
    sys.stdout.flush()
    quit(1)
    















