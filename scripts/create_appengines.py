import json
import sys


projectsfile = open(sys.argv[1], 'r')
projects = json.load(projectsfile)
for project in projects['projects']:
    if 'appengine.googleapis.com' in project.get('services', []) and 'appEngineRegion' in project:
        print('gcloud app create --project={} --region={}'.format(project['projectId'], project['appEngineRegion']))
