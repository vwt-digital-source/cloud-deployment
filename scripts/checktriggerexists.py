import json
import sys


if len(sys.argv) > 2:
    existingtrsfile = open(sys.argv[1])
    existingtrs = json.load(existingtrsfile)
    triggerfile = open(sys.argv[2])
    trigger = json.load(triggerfile)
    if 'triggers' in existingtrs:
        for tr in existingtrs['triggers']:
            if 'triggerTemplate' in tr \
                and tr['triggerTemplate'].get('projectId', 'x') == tr['triggerTemplate'].get('projectId', '') \
                and trigger['triggerTemplate'].get('repoName', 'x') == tr['triggerTemplate'].get('repoName', '')  \
                and trigger['triggerTemplate'].get('branchName', 'x') == tr['triggerTemplate'].get('branchName', ''):
                    print(tr['id'])
