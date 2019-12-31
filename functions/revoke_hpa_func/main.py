import json

import googleapiclient.discovery
from oauth2client.client import GoogleCredentials


def get_policy(project_id):
    """Gets IAM policy for a project."""
    credentials = GoogleCredentials.get_application_default()
    service = googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)
    policy = service.projects().getIamPolicy(resource=project_id, body={}).execute()
    print(policy)
    return policy


def modify_policy_remove_member(policy, role, member):
    """Removes a  member from a role binding."""

    binding = next(b for b in policy['bindings'] if b['role'] == role)
    if 'members' in binding and member in binding['members']:
        binding['members'].remove(member)
    print(binding)
    return policy


def set_policy(project_id, policy):
    """Sets IAM policy for a project."""

    credentials = GoogleCredentials.get_application_default()
    service = googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)

    policy = service.projects().setIamPolicy(resource=project_id, body={'policy': policy}).execute()
    print(policy)
    return policy


def revoke_HPA(request):
    projects = json.load(open('projects.json'))

    for pr in projects['projects']:
        policy = get_policy(pr['projectId'])
        modified = False
        for binding in policy['bindings']:
            for member in binding['members']:
                if 'user:' in member:
                    modified = True
                    policy = modify_policy_remove_member(policy, binding['role'], member)
                    print("Removed [{}],[{}]".format(member, binding['role']))

        if modified:
            print("New Policy {}".format(policy))
            # set_policy(pr['projectId'], policy)

    # Returning any 2xx status indicates successful receipt of the message.
    # 204: no content, delivery successful, no further actions needed
    return 'OK', 204
