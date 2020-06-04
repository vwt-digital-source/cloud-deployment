import re
import json
import logging
import argparse
import subprocess

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

logging.basicConfig(level=logging.INFO, format='%(levelname)7s: %(message)s')


def flatten_bindings(bindings):
    """Flattens bindings based on members"""

    flattened = []
    for binding in bindings:
        for member in binding['members']:
            flat_binding = {
                'role': binding['role'],
                'member': member
            }
            flattened.append(flat_binding)

    return flattened


def get_documented_policies(project):
    """Get documented polices from project object"""

    odrlPolicy = project.get('odrlPolicy')

    documented_policies = []
    if odrlPolicy.get('permission'):
        for permission in odrlPolicy.get('permission', []):
            if permission.get('target') == project.get('projectId'):
                documented_policies.append(permission)

    return documented_policies


def transform_binding(binding, service, project_id):
    """Transforms an IAM binding to their end state"""

    binding['member'] = binding['member'].replace('__PROJECT_ID__', project_id)
    matches = re.findall(r'\$\(ref\.(.*)\.projectNumber\)', binding['member'])
    if matches:
        project_number = get_project_number(service, matches[0])
        binding['member'] = re.sub(r'\$\(ref\.(.*)\.projectNumber\)', project_number, binding['member'])

    return binding


def filter_bindings(bindings, project_number, project_id):
    """Filter IAM bindings for gcp default service accounts"""

    prefix = 'serviceAccount:service-{}'.format(project_number)
    excludes = ['serviceAccount:firebase-service-account@firebase-sa-management.iam.gserviceaccount.com']

    filtered_bindings = []
    for binding in bindings:
        for member in binding['members']:
            if member.startswith(prefix) and project_id not in member:
                binding['members'].remove(member)
            if member.startswith('user:'):
                binding['members'].remove(member)
            if member in excludes:
                binding['members'].remove(member)
        if binding['members']:
            filtered_bindings.append(binding)

    return filtered_bindings


def policies_to_bindings(policies):
    """Transform an odrlPolicy to IAM bindings object"""

    bindings = []
    for policy in policies:
        binding = {
            'role': policy['action'],
            'member': policy['assignee']
        }
        bindings.append(binding)

    return bindings


def get_default_bindings(iam_bindings_file):
    """Get default IAM member bindings from a file"""

    bindings = open(iam_bindings_file)
    default_bindings = json.load(bindings).get('default', [])

    return default_bindings


def delete_iam_binding(binding, project_id):
    """Deletes a single IAM member binding"""

    _ = exec_shell_command([
        'gcloud', 'projects',
        'remove-iam-policy-binding', project_id,
        '--member={}'.format(binding['member']),
        '--role={}'.format(binding['role'])
    ])

    logging.info('REMOVED {}'.format(binding))


def get_iam_bindings(service, project_id):
    """Get IAM member bindings for a given project id"""

    request = service.projects().getIamPolicy(
        resource=project_id, body={})
    response = request.execute()
    bindings = response.get('bindings', [])

    return bindings


def set_iam_bindings(service, bindings, project_id):
    """Get IAM member bindings for a given project id"""

    request = service.projects().getIamPolicy(
        resource=project_id, body={})
    response = request.execute()
    bindings = response.get('bindings', [])

    return bindings


def get_project_number(service, project_id):
    """Get a project number corresponding a project id"""

    request = service.projects().get(projectId=project_id)
    response = request.execute()
    project_number = response.get('projectNumber')

    return project_number


def make_service():
    """Makes a google cloudresourcemanager service"""

    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)

    return service


def exec_shell_command(command):
    """Executes a shell command"""

    logging.info(' '.join(command))
    process = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)

    return process.stdout


def parse_args():
    """A simple function to parse command line arguments"""

    parser = argparse.ArgumentParser(description='Remove undocumented iam roles')
    parser.add_argument('-p', '--projects-file',
                        required=True,
                        help='path to projects.json file')
    parser.add_argument('-i', '--iam-bindings-file',
                        required=True,
                        help='path to iam_bindings.json file')
    return parser.parse_args()


def main(args):
    service = make_service()

    projects = json.load(open(args.projects_file))

    for project in projects.get('projects', []):
        project_id = project['projectId']
        project_number = get_project_number(service, project_id)

        default_bindings = list(map(lambda x: transform_binding(x, service, project_id),
                                    get_default_bindings(args.iam_bindings_file)))

        documented_policies = get_documented_policies(project)
        documented_bindings = list(map(lambda x: transform_binding(x, service, project_id),
                                       policies_to_bindings(documented_policies)))

        iam_bindings = get_iam_bindings(service, project_id)
        filtered_bindings = filter_bindings(iam_bindings, project_number, project_id)
        flattened_bindings = flatten_bindings(filtered_bindings)

        undocumented_bindings = []
        for binding in flattened_bindings:
            if binding not in documented_bindings + default_bindings:
                undocumented_bindings.append(binding)

        for binding in undocumented_bindings:
            delete_iam_binding(binding, project_id)


if __name__ == '__main__':
    main(parse_args())
