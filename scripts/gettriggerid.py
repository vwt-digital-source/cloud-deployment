import sys
import json


jsonfile = open(sys.argv[1], "r")
triggers = json.loads(jsonfile.read())

repoName = sys.argv[2]
branchName = sys.argv[3]

for trigger in triggers['triggers']:
    if 'triggerTemplate' in trigger:
        if trigger['triggerTemplate']['repoName'] == repoName and trigger['triggerTemplate']['branchName'] == branchName:
            print(trigger['id'])
    if 'github' in trigger:
        if trigger['github']['name'] == repoName and trigger['github']['push']['branch'] == branchName:
            print(trigger['id'])
