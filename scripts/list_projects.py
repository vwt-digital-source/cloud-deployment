import json
import sys

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)
    for pr in projects['projects']:
        print(pr['projectId'])
