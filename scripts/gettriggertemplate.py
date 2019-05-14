import sys
import json


jsonfile = open(sys.argv[1], "r")
triggers = json.loads(jsonfile.read())

repoName=sys.argv[2]
branchName=sys.argv[3]

for trigger in triggers['triggers']:
    if trigger['triggerTemplate']['repoName'] == repoName and trigger['triggerTemplate']['branchName'] == branchName:
        print(trigger['triggerTemplate'])
