import sys
import json

# RepoSource : https://cloud.google.com/cloud-build/docs/api/reference/rest/Shared.Types/Build#RepoSource
# triggertTemplate:
# { 'projectId': 'vwt-d-gew1-dat-deployment',
#   'repoName': 'github_vwt-digital-config_dat-deployment-config',
#   'branchName': 'develop'}
#
# github:
# { 'projectId': 'vwt-d-gew1-dat-deployment',
#   'repoName': 'high-privilege-access-config',
#   'branchName': 'develop'}

jsonfile = open(sys.argv[1], "r")
triggers = json.loads(jsonfile.read())

projectId = sys.argv[2]
repoName = sys.argv[3]
branchName = sys.argv[4]

for trigger in triggers['triggers']:
    if 'triggerTemplate' in trigger:
        if trigger['triggerTemplate']['repoName'] == repoName and trigger['triggerTemplate']['branchName'] == branchName:
            print(trigger['triggerTemplate'])
    if 'github' in trigger:
        if trigger['github']['name'] == repoName and trigger['github']['push']['branch'] == branchName:
            RepoSource = {}
            RepoSource['projectId'] = projectId
            RepoSource['repoName'] = trigger['github']['name']
            RepoSource['branchName'] = trigger['github']['push']['branch']
            print(RepoSource)
