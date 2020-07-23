import json
import sys
from collections import OrderedDict

projectfile = open(sys.argv[1])
project = json.load(projectfile)
if 'firewallRules' in project and len(project['firewallRules']) > 0:
    for rule in project['firewallRules']:
        rule['network'] = 'https://www.googleapis.com/compute/v1/projects/{}/global/networks/{}' \
            .format(project['projectId'], rule['network'])
        rule['protocolRules'] = ','.join(map(str, rule['protocolRules']))
        rule['sourceRanges'] = ','.join(map(str, rule['sourceRanges']))
        rule = OrderedDict(sorted(rule.items()))
        print(' '.join('"{}"'.format(value)
                       if any(map(str(value).__contains__, [' ', '\n'])) or value == ''
                       else str(value) for _, value in rule.items()))
