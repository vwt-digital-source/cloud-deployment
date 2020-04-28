import sys
import json

project_id = sys.argv[1]
services_file = open(sys.argv[2])
default_services = json.load(services_file).get('default', [])

with open(sys.argv[3]) as projects_file:
    projects = json.load(projects_file)
    for project in projects.get('projects', []):
        if project.get('projectId') == project_id:
            services = project.get('services', [])
            services.extend(default_services)
            for service in list(set(services)):
                print(service)
