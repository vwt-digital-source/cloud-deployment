#!/usr/bin/env python3

import config
import json
import sys
import logging
import google
import googleapiclient.discovery

from google.auth import iam
from google.auth.transport import requests
from google.oauth2 import service_account

logging.getLogger().setLevel(logging.INFO)

TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'  # nosec


def create_adminsdk_service():
    credentials, project_id = google.auth.default(scopes=['https://www.googleapis.com/auth/iam'])

    try:
        request = requests.Request()
        credentials.refresh(request)

        signer = iam.Signer(request, credentials, config.SERVICE_ACCOUNT)
        delegated_credentials = service_account.Credentials(
            signer=signer,
            service_account_email=config.SERVICE_ACCOUNT,
            token_uri=TOKEN_URI,
            scopes=config.SERVICE_ACCOUNT_SCOPES,
            subject=config.USER_IMPERSONATION_EMAIL)
    except Exception:
        raise

    gs_service = googleapiclient.discovery.build(
        'admin', 'directory_v1', credentials=delegated_credentials,
        cache_discovery=False)
    rm_service = googleapiclient.discovery.build(
        'cloudresourcemanager', 'v1beta1', credentials=delegated_credentials,
        cache_discovery=False)
    return gs_service, rm_service


def get_project_numbers(project_ids, rm_service):
    project_list = {}
    response = rm_service.projects().list().execute()

    for project in response.get('projects', []):
        if project['projectId'] in project_ids:
            project_list[str(project['projectId'])] = int(project['projectNumber'])

    return project_list


def create_gsuite_groups(gs_service, group_list):
    for group in group_list:
        group_object = gs_service.groups().list(
            domain='vwt.digital',
            maxResults=1,
            query='email:{}*'.format(group['email'].split('@')[0])
        ).execute()

        if 'groups' not in group_object:
            group_json = {
                "description": '{}'.format(group['description']),
                "name": '{}'.format(group['name']),
                "email": '{}'.format(group['email'])
            }
            gs_service.groups().insert(body=group_json).execute()

        logging.info('Group "{}" is existing'.format(group['email']))


def process_gsuite_groups(gs_service, group_info, new_group_members):
    # Getting all members of the group
    members_object = gs_service.members().list(
        groupKey=group_info['email'],
        roles='MEMBER'
    ).execute()
    group_members = members_object.get('members')

    if group_members:
        # Create list with existing group emails
        group_member_ids = []
        for member in group_members:
            group_member_ids.append(member['email'])

        # Compare existing with new emails
        to_remove = list(
            set(group_member_ids).difference(new_group_members))
        new_group_members = list(
            set(new_group_members).difference(group_member_ids))

        if len(to_remove) > 0:
            # Remove all emails from group that are not in projects list
            for project_id in to_remove:
                gs_service.members().delete(
                    groupKey=group_info['email'],
                    memberKey=project_id
                ).execute()

        logging.info(
            '{} non-existing projects have been deleted from group "{}"'.format(
                len(to_remove), group_info['email']))

    # Add new projects to group
    for project_id in new_group_members:
        new_user = {
            "status": "ACTIVE",
            "delivery_settings": "NONE",
            "role": "MEMBER",
            "type": "USER",
            "email": '{}'.format(project_id)
        }
        gs_service.members().insert(groupKey=group_info['email'],
                                    body=new_user).execute()

    logging.info(
        '{} projects have been added to group "{}"'.format(
            len(new_group_members), group_info['email']))


def create_gsuite_group_iam():
    if len(sys.argv) >= 2 and \
            all(hasattr(config, attr) for attr in ["USER_IMPERSONATION_EMAIL",
                                                   "SERVICE_ACCOUNT_SCOPES",
                                                   "GSUITE_GROUPS"]):
        # Create list with project ids
        projects = json.load(open(sys.argv[1]))
        project_ids = {str(project['projectId']) for project in
                       projects['projects']}

        gs_service, rm_service = create_adminsdk_service()
        project_ids = get_project_numbers(project_ids, rm_service)

        # Create G Suite Groups
        create_gsuite_groups(gs_service, config.GSUITE_GROUPS)

        # Create object will all project e-mails
        project_list = {
            'appspot': [],
            'cloudbuild': []
        }
        for project in project_ids:
            project_list['appspot'].append(
                '{}@appspot.gserviceaccount.com'.format(project))
            project_list['cloudbuild'].append(
                '{}@cloudbuild.gserviceaccount.com'.format(project_ids[project]))

        # Process groups
        for group in config.GSUITE_GROUPS:
            if group['members'] in project_list and \
                    len(project_list[group['members']]) > 0:
                process_gsuite_groups(gs_service, group,
                                      project_list[group['members']])


create_gsuite_group_iam()
