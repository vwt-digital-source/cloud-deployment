import json
import sys


if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)
    for ds in projects['dataset']:
        dist = ds['distribution'][0]

        if dist['format'] == "gitrepo":
            print(dist['title'])
