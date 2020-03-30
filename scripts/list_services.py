import sys
import json

project_id = sys.argv[1]

default_services = [
    'cloudtrace.googleapis.com',
    'logging.googleapis.com',
    'monitoring.googleapis.com',
    'servicecontrol.googleapis.com',
    'servicemanagement.googleapis.com',
    'cloudresourcemanager.googleapis.com',
    'source.googleapis.com'
    'sourcerepo.googleapis.com',
    'storage-api.googleapis.com',
    'storage-component.googleapis.com',
    'cloudbuild.googleapis.com',
    'pubsub.googleapis.com',
    'cloudfunctions.googleapis.com'
]

with open(sys.argv[2]) as projects_file:
    projects = json.load(projects_file)
    for project in projects.get('projects', []):
        if project.get('projectId') == project_id:
            services = project.get('services', [])
            services.extend(default_services)
            for service in services:
                print(service)
