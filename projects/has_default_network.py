import sys
import json

project_id = sys.argv[1]

with open(sys.argv[2]) as projects_file:
    projects = json.load(projects_file)
    for project in projects.get('projects', []):
        if project.get('projectId') == project_id:
            print(project.get('defaultNetwork'))
