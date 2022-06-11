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

# Static variables
notFoundStr = 'NOT_FOUND'
codeDeployApprovalMsgStr = 'CODEDEPOYAPPROVALMSG'

# Read environment variables
currRelease = os.environ.get('RELEASE_RELEASEID', notFoundStr)
currStage = os.environ.get('RELEASE_ENVIRONMENTNAME', notFoundStr).upper()
currDeployment = os.environ.get('RELEASE_DEPLOYMENTID', notFoundStr)
teamProjectName = os.environ.get('SYSTEM_TEAMPROJECT', notFoundStr)
teamFoundationServerURL = os.environ.get('SYSTEM_TEAMFOUNDATIONSERVERURI', notFoundStr)


#
# Import arguments and environment properties etc
#
parser = argparse.ArgumentParser()
parser.add_argument("-azuretoken", required=True, help="Azure personal access token PAL")
parser.add_argument("-interventionName", required=True, help="Manual Intervention Name")
parser.add_argument('-t', action='store_true')
parser.add_argument('-failonapprovalcheck', action='store_true')
args = parser.parse_args()
azureToken = args.azuretoken
interventionName = args.interventionName
testMode = False
if args.t:
    testMode = True
    
#
# If 'failonapprovalcheck" is set then fail
# the script if code deployment approval check fails
#
if args.failonapprovalcheck:
    failIfCodeDeployCheckFails = True
else:
    failIfCodeDeployCheckFails = False    

#
# If running in test mode set test values
#
if testMode:
    currRelease = '69'
    currStage = 'PRD'
    currDeployment = '69'
    teamProjectName = 'Examples'
    teamFoundationServerURL = 'https://vsrm.dev.azure.com/zoyinc/'

if ((currRelease == notFoundStr) or (currStage == notFoundStr) or (currDeployment == notFoundStr) or (teamProjectName == notFoundStr) or (teamFoundationServerURL == notFoundStr)):
    print('##[error]')
    print('##[error] Something went wrong, could not determine some or all environment variables')
    print('##[error]')
    print('currRelease:                     ' + currRelease)
    print('currStage:                       ' + currStage)
    print('currDeployment:                  ' + currDeployment)
    print('teamFoundationServerURL:         ' +  teamFoundationServerURL)
    print('teamProjectName:                 ' + teamProjectName)
    quit(1)

azureReleaseURL = teamFoundationServerURL + teamProjectName + '/_apis/release/releases/' + currRelease + '?api-version=5.0'
basicStageName = re.sub(r'( |_|\(|\)|-)','', currStage).upper()
globalVarPrefix = 'GLOBALVAR_' + basicStageName
previousCodeDeployApprovalComment = os.environ.get(globalVarPrefix + '_' + codeDeployApprovalMsgStr, notFoundStr)


#
# Summary
#
print('#')
print('# Processing Code Deployment Approval Comments')
print('# ===========================================')
print('# Current release:                  ' + currRelease)
print('# Current stage name:               ' + currStage)
print('# Basic stage name:                 ' + basicStageName)
print('# Current deployment id:            ' + currDeployment)
print('# currDeployment:                   ' + currDeployment)
print('# teamFoundationServerURL:          ' + teamFoundationServerURL)
print('# Manual Intervention name:         ' + interventionName)
print('# Manual Intervention name:         ' + interventionName)
print('# Release URL:                      ' + azureReleaseURL)
print('# Variable name prefix:             ' + globalVarPrefix)
print('# Fail if code deploy check fails:  ' + str(failIfCodeDeployCheckFails))
if testMode:
    print('# Script running in:                TEST mode ')
else:
    print('# Script running in                 NORMAL mode ')
print('# Date:                             ' + datetime.now().strftime('%d/%m/%y %H:%M'))
print('#')


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
interventionNameUpper = interventionName.upper()
currStageUpper = currStage .upper()

#
# Now need to go through all tasks and look for ones that include 'instructions' so that we
# can find the comments for this manual intervention task
#

problemsReport = ''
varIndentStr = '    '
commentIsFound = False
for stageIndex, itemValue in enumerate(releaseDetailOriginal['environments']):
    
    currStageName = releaseDetailOriginal['environments'][stageIndex]['name']
    basicStageName = re.sub(r'( |_|\(|\)|-)','', currStageName).upper()
    print('Stage = ' + currStageName)
    
    if currStageName.upper() == currStageUpper:
        print('==== Stage ==>')
    
        #
        # Second iterate over all the deploy steps in the current stage
        #
        for deployStepIndex, deployStepValue in enumerate(releaseDetailOriginal['environments'][stageIndex]['deploySteps']):
            
            currDeployStepID = releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['deploymentId']
            print('  Deploy Step ID = ' + str(currDeployStepID))
            
            if str(currDeployStepID) == currDeployment:
                print('  ==== Deployment ID ==>')
            
                #
                # Third iterate over all the release deployment phases in the current deploy step
                #
                for releaseDeployPhaseIndex, releaseDeployPhaseValue in enumerate(releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases']):
                    currReleaseDeployPhaseId = releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases'][releaseDeployPhaseIndex]['phaseId']
                    currReleaseDeployPhaseName = releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases'][releaseDeployPhaseIndex]['name']
                    print('      Release Deploy Phase = ' + str(currReleaseDeployPhaseId) + ' (' + currReleaseDeployPhaseName + ')')
                    
                    #
                    # Fourthly iterate over all the manual interventions
                    #
                    for currManualInterventionsIndex, manualInterventionsValue in enumerate(releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases'][releaseDeployPhaseIndex]['manualInterventions']):
                        currManualInterventionsName = releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases'][releaseDeployPhaseIndex]['manualInterventions'][currManualInterventionsIndex]['name']
                        print('           Manual Intervention Name = ' + currManualInterventionsName)
                        if interventionNameUpper == currManualInterventionsName.upper():
                            manualInterventionComment = releaseDetailOriginal['environments'][stageIndex]['deploySteps'][deployStepIndex]['releaseDeployPhases'][releaseDeployPhaseIndex]['manualInterventions'][currManualInterventionsIndex]['comments']
                            print('           =====Intervention ==>')
                            print('           Manual intervention comment = ' + manualInterventionComment)
                            
                            #
                            # We have found the comment we are searching for no need to keep looping
                            # through so exit
                            #
                            commentIsFound = True
                        if commentIsFound:
                            break
                    if commentIsFound:
                        break
            if commentIsFound:
                break
    if commentIsFound:
        break

#
# If no comments found fail
#
if not commentIsFound:
    print('')
    print('##[error]')
    print('##[error] No comment details found')
    print('##[error]')
    print('')
    print('This does not mean that no comments were entered, it means that no comment')
    print('block was found in the JSON response. This is a different problem.')
    print('')
    quit(1)

#
# Process the Code Deployment Approval comments
#
azureVars = {}
azureVars.update({globalVarPrefix + '_' + codeDeployApprovalMsgStr: manualInterventionComment})


#
# Ensure the Code Deployment Approval comment contains the environment
# name with hyphens between letters - so 'PRD' goes to 'P-R-D'
#
hyphenatedEnvName = basicStageName.upper().replace('','-')[:-1][1:]
print('hyphenatedEnvName = \'' + hyphenatedEnvName + '\'')
correctHyphenatedNameFound = True
if manualInterventionComment.upper().find(hyphenatedEnvName) != -1:
    azureVars.update({globalVarPrefix + '_DEPLOYAPPROVALOK': 'TRUE'})
else:
    #
    # If '-failonapprovalcheck' was set when running this script
    # then fail if the approval comment does not include a hyphenated
    # environment name.
    # 
    if failIfCodeDeployCheckFails:
        print('')
        print('##[error]')
        print('##[error] The comments in the \'Code Deployment Approval\' did not contain')
        print('##[error] the environment name in hyphens or it was not hypenated correctly.')
        print('##[error] ')
        print('')
        print('In neither the original code deployment approval comments, or the second \'Last Chance\'')
        print('deployment approval comments was the environment name include in the comments with hyphens')
        print('between characters. For example if the environment was  \'STG\' then you should have included')
        print('\'S-T-G\' in the approval comments.')
        print('')
        print('The comment from the original approval was:')
        print('')
        print(previousCodeDeployApprovalComment)
        print('')
        print('The comments just entered, in the \'Last Chance\' approval was:')
        print('')
        print(manualInterventionComment)
        print('')
        quit(1)
    else:
        #
        # User has not entered a hyphenated stage name
        #
        print('##[warning]')
        print('##[warning] No hyphenated stage name found')
        print('##[warning]')
        azureVars.update({globalVarPrefix + '_DEPLOYAPPROVALOK': 'FALSE'})
        correctHyphenatedNameFound = False
        

#
# Update Azure global variable using the "Releases - Update Release" api
# ----------------------------------------------------------------------
#
# To update or add a global, variable with scope of "Release", you need to use the
# "Releases - Update Release" api. This is a complete replace of the release definition
# for this release number - so a release change, not a release definition change.
#
# Because this api does a complete replace you could get problems if two people
# are doing deploys at the same time and their changes interlace.
#
# The way this code works is to get a complete copy of the definition, via a
# "Releases - Get Release" api. This load the full definition for the release
# into the variable "ReleaseOldDetailsDict".
#
# We then copy "ReleaseOldDetailsDict" to the variable "PUTRequestReleaseNewDetailsDict",
# then we update "PUTRequestReleaseNewDetailsDict" with the new global variable details for
# the release and PUT it back using the"Releases - Update Release" api.
#
# It gets a bit tricky here. The problem is what if two people are doing deploys
# using he same pipeline release number. They could end up dove-tailing their changes
# with unexpected results.
#
# This Azure api will give an error:
#
#    You are using an old copy of release. Refresh your copy and try again.
#
# Suppose you and another process grab a copy of a release and they make a change first. In
# this case when you try to do your PUT to the api it will vail with the "..old copy of release..." error.
# - This should prevent processes dovetailing each other.
#
# Thus when we run this api we loop around up to x number of times if you we get error. So on 
# the basis that a clash will be rare, we give it X tries before we fail.
# 
headers = {"Content-Type" : "application/json"}
updateOK = False
updateRetrysLeft = 5
while (not updateOK) and (updateRetrysLeft > 0):
    updateRetrysLeft -= 1
    
    #
    # Get current release definition as "ReleaseOldDetailsDict"
    #
    azureResponseReleaseOldDetails = requests.get(azureReleaseURL, auth=('', azureToken))
    if azureResponseReleaseOldDetails.status_code != 200:
        print('##[error]')
        print('##[error] Could not connect to Azure')
        print('##[error]')
        print('URL:            ' + azureReleaseURL)
        print('Status code:    ' + str(azureResponseReleaseOldDetails.status_code))
        print('Error received: ' + azureResponseReleaseOldDetails.reason)
        quit(1)        
    ReleaseOldDetailsDict = json.loads(azureResponseReleaseOldDetails.text)
    
    #
    # Update the definition with the new global variable details
    #      
    PUTRequestReleaseNewDetailsDict = copy.deepcopy(ReleaseOldDetailsDict)
    for envVarItem, envVarVal in azureVars.items():
        PUTRequestReleaseNewDetailsDict['variables'].update({envVarItem :{'value': envVarVal}})
    
    #
    # Push the change to Azure using PUT requests
    #
    azureResponseReleaseNewDetails = requests.put(azureReleaseURL, auth=('', azureToken), data=json.dumps(PUTRequestReleaseNewDetailsDict), headers=headers)
    if azureResponseReleaseNewDetails.status_code != 200:        
        #
        # Get "message" from Azure
        #
        # This is different from the HTTP error. The Azure "message" is a dictionary
        # item in the JSON response.
        #
        # We are looking for a HTTP 400 error which returns a JSON response
        #
        fatalError = False
        try:
            responseMsg = json.loads(azureResponseReleaseNewDetails.content)['message']
            if responseMsg.upper().find('USING AN OLD COPY OF RELEASE') == -1:
                responseMsg = 'Unexpected error. Please review the \'JSON message\' for errors.'
                fatalError = False                
            else:
                print('# update of global property failed because of another process is also updating the release definition. We will try again.')
                time.sleep(5)
        except ValueError as e:
            fatalError = True
            responseMsg = 'No JSON response received - some other error type.'
        except KeyError as e:
            fatalError = True
            responseMsg = 'JSON response received but no dictionary \'message\' item was found.'
        
        #
        # If we have a fatal error then quit
        #
        if fatalError:
            print('##[error]')
            print('##[error] Could not connect to Azure')
            print('##[error]')
            print('URL:            ' + azureReleaseURL)
            print('Status code:    ' + str(azureResponseReleaseNewDetails.status_code))
            print('Error received: ' + azureResponseReleaseNewDetails.reason)
            print('JSON message:   ' + responseMsg)
            print('Content:        ' + str(azureResponseReleaseNewDetails.content))
            quit(1)
    else:
        # Update was successful
        updateOK = True 

#
# If we were unable to update exit
#
if not updateOK:
    print('##[error]')
    print('##[error] Could not update the global variable for this release')
    print('##[error]')
    quit(1)
    
#
# All went well
#
print('##[section]')
if correctHyphenatedNameFound:
    print('##[section] The code deployment approval was acceptable and contained the')
    print('##[section] environment name is hyphens.')
else:
    print('##[section] The stage hyphenated name was not found. But since that was the')
    print('##[section] first code deployment approval we will move to the \'Last Chance\' approval')
    print('##[section] task.')
    
print('##[section] ')
print('##[section] The release can continue!')  
print('##[section] ')  
print()
print()