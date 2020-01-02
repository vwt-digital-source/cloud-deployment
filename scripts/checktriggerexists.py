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
                    and 'triggerTemplate' in trigger \
                    and tr['triggerTemplate'].get('projectId', 'x') == tr['triggerTemplate'].get('projectId', '') \
                    and trigger['triggerTemplate'].get('repoName', 'x') == tr['triggerTemplate'].get('repoName', '')  \
                    and trigger['triggerTemplate'].get('branchName', 'x') == tr['triggerTemplate'].get('branchName', ''):
                print(tr['id'])

            if 'github' in tr \
                    and 'github' in trigger \
                    and trigger['github'].get('name', 'x') == tr['github'].get('name', '')  \
                    and trigger['github']['push'].get('branch', 'x') == tr['github']['push'].get('branch', ''):
                print(tr['id'])
