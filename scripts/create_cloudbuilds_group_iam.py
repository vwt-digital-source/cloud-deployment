import json
import sys
import pickle
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)

    # The file adminsdk_token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists('adminsdk_token.pickle'):
        with open('adminsdk_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'adminsdk_credentials.json', os.environ['SCOPES'])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('adminsdk_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('admin', 'directory_v1', credentials=creds)

    # Getting groups by email
    group_object = service.groups().list(
        domain='vwt.digital',
        maxResults=1,
        query='email:{}*'.format(os.environ['GROUP_KEY'].split('@')[0])
    ).execute()

    # Create new group if not existing
    if 'groups' not in group_object:
        group_json = {
            "description": "All GCP cloud builder accounts",
            "name": "Cloud Builders",
            "email": '{}'.format(os.environ['GROUP_KEY'])
        }
        service.groups().insert(body=group_json).execute()

    # Getting all members of the group
    members_object = group_object = service.members().list(
        groupKey=os.environ['GROUP_KEY'],
        roles='MEMBER'
    ).execute()
    group_members = members_object.get('members')

    # Deleting all existing group members
    if group_members:
        for member in group_members:
            service.members().delete(
                groupKey=os.environ['GROUP_KEY'],
                memberKey=member['id']
            ).execute()

    # Add members to group
    for pr in projects['projects']:
        new_user = {
           "status": "ACTIVE",
           "delivery_settings": "NONE",
           "role": "MEMBER",
           "type": "USER",
           "email": '{}@appspot.gserviceaccount.com'.format(pr['projectId'])
        }
        service.members().insert(groupKey=os.environ['GROUP_KEY'], body=new_user).execute()
