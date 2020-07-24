import json
import sys

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)
    result = {
        'bindings': [
            {
                'members': [],
                'role': 'roles/pubsub.publisher'
            }
        ]
    }

    for pr in projects['projects']:
        result['bindings'][0]['members'].append('serviceAccount:{}@appspot.gserviceaccount.com'.format(pr['projectId']))

    print(json.dumps(result))
