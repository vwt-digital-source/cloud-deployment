import sys
import json
from create_projects import append_default_services

project_id = sys.argv[1]

with open(sys.argv[2]) as projects_file:
    projects = json.load(projects_file)
    for project in projects.get('projects', []):
        if project.get('projectId') == project_id:
            services = project.get('services', [])
            services = append_default_services(services)
            for service in services:
                print(service)
