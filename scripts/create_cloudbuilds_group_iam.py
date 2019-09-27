import json
import sys
import os

from google.oauth2 import service_account
import googleapiclient.discovery

def get_service(api_name, api_version, scope, key_file_location, user_impersonation_email):
    """Get a service that communicates to a Google API.

    Args:
        api_name: The name of the api to connect to.
        api_version: The api version to connect to.
        scopes: A list auth scopes to authorize for the application.
        key_file_location: The path to a valid service account JSON key file.

    Returns:
        A service that is connected to the specified API.
    """

    # Create credentials
    credentials = service_account.Credentials.from_service_account_file(
        key_file_location, scopes=[scope])

    delegated_credentials = credentials.with_subject(user_impersonation_email)

    service = googleapiclient.discovery.build(api_name, api_version, credentials=delegated_credentials)

    return service


def set_group(service, group_key):
    """Set a group within the G Suite domain.

    Args:
        service: A service that is connected to the specified API.
    """

    print(F'Group "{group_key}" is active')
    # Getting groups by email
    group_object = service.groups().list(
        domain='vwt.digital',
        maxResults=1,
        query='email:{}*'.format(group_key.split('@')[0])
    ).execute()

    # Create new group if not existing
    if 'groups' not in group_object:
        group_json = {
            "description": "All GCP cloud builder accounts",
            "name": "Cloud Builders",
            "email": '{}'.format(group_key)
        }
        service.groups().insert(body=group_json).execute()


def set_members(service, group_key, projects_list):
    """Set all members within a group based on a dictionary.

    Args:
        service: A service that is connected to the specified API.
    """

    # Getting all members of the group
    members_object = service.members().list(
        groupKey=group_key,
        roles='MEMBER'
    ).execute()
    group_members = members_object.get('members')

    # Deleting all existing group members
    if group_members:
        for member in group_members:
            service.members().delete(
                groupKey=group_key,
                memberKey=member['id']
            ).execute()

        print('All current group members are removed')

        # Add members to group
        for project in projects_list:
            new_user = {
                "status": "ACTIVE",
                "delivery_settings": "NONE",
                "role": "MEMBER",
                "type": "USER",
                "email": '{}@appspot.gserviceaccount.com'.format(project['projectId'])
            }
            service.members().insert(groupKey=group_key, body=new_user).execute()

        print('All new group members are added')


def main():
    if len(sys.argv) >= 1:
        projectsfile = open(sys.argv[1])
        projects = json.load(projectsfile)

        service = get_service(
            api_name='admin',
            api_version='directory_v1',
            scope=os.environ['SERVICE_ACCOUNT_SCOPE'],
            key_file_location=os.environ['SERVICE_ACCOUNT_JSON_FILE_PATH'],
            user_impersonation_email=os.environ['USER_IMPERSONATION_EMAIL']
        )

        set_group(
            service=service,
            group_key=os.environ['GSUITE_GROUP_KEY'])
        set_members(
            service=service,
            group_key=os.environ['GSUITE_GROUP_KEY'],
            projects_list=projects)


if __name__ == '__main__':
    main()
