import json
import sys
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()
service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

def modify_policy_remove_member(policy, role, member):
    """Removes a  member from a role binding."""
    binding = next(b for b in policy['bindings'] if b['role'] == role)
    if 'members' in binding and member in binding['members']:
        binding['members'].remove(member)
    print(binding)
    return policy

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)

    for pr in projects['projects']:

        documented_userroles = []
        if 'odrlPolicy' in pr: 
            for perm in pr['odrlPolicy']['permission']:
                if 'vwt.digital' in perm['assignee'] and pr['projectId'] == perm['target']:
                    documented_userroles.append(perm)
                    print("ODRL {}".format(perm))

        request = service.projects().getIamPolicy(resource=pr['projectId'])
        policy = request.execute()

        policy_updated = False
        for binding in policy['bindings']:
            for member in binding['members']:
                if 'vwt.digital' in member:
                    if next((item for item in documented_userroles if item['assignee'] == member and item['action'] == binding['role']), False) == False:
                        print("NOT FOUND {} {} {}".format(pr['projectId'], member, binding['role']))
                        policy = modify_policy_remove_member(policy, binding['role'], member)
                        policy_updated = True
        
        if policy_updated == True:
            policy = service.projects().setIamPolicy(resource=pr['projectId'], body={'policy': policy}).execute()

