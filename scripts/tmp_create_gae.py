import json
import sys

projectsfile = open(sys.argv[1])
project = json.load(projectsfile)
if 'appengine.googleapis.com' in project.get('services', []) and project.get('appEngineRegion'):
    print('gcloud app describe --project={} || gcloud app create --project={} --region={}'.format(
        project['projectId'],
        project['projectId'],
        project['appEngineRegion']))
