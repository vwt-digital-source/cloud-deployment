import re
import asyncio
import argparse
import logging

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from argparse import RawTextHelpFormatter

logging.basicConfig(level=logging.INFO, format='%(levelname)7s: %(message)s')


async def main(args):
    service = make_service()
    await asyncio.gather(
        *[process(service, project, args.services) for project in args.projects]
    )


async def process(service, project_id, services):
    logging.info('Updating audit log configuration for project {}...'.format(project_id))
    policy = await get_iam_policy(service, project_id)
    if policy:
        updated_policy = await add_audit_configs(policy, services)
        await set_iam_policy(service, project_id, updated_policy)


async def get_iam_policy(service, project_id):
    try:
        request = service.projects().getIamPolicy(resource=project_id, body={})
        response = request.execute()
        return response
    except HttpError:
        logging.error('Request setIamPolicy failed for project {}'.format(project_id))


async def set_iam_policy(service, project_id, policy):
    try:
        request = service.projects().setIamPolicy(resource=project_id, body={'policy': policy})
        response = request.execute()
        return response
    except HttpError:
        logging.error('Request getIamPolicy failed for project {}'.format(project_id))


async def add_audit_configs(policy, services):
    if services:
        policy['auditConfigs'] = []
    for service in services:
        policy['auditConfigs'].append({
            'auditLogConfigs': [
                {
                    'logType': 'ADMIN_READ'
                },
                {
                    'logType': 'DATA_READ'
                },
                {
                    'logType': 'DATA_WRITE'
                },
            ],
            'service': service
        })
    return policy


def make_service():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)
    return service


def parse_args():
    parser = argparse.ArgumentParser(description='Add gcp audit log configuration async', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-p', '--projects',
                        type=lambda s: re.split(' |\n|, ', s),
                        required=True,
                        help='a new line, space or comma delimited list of services')
    parser.add_argument('-s', '--services',
                        type=lambda s: re.split(' |\n|, ', s),
                        required=True,
                        help='a new line, space or comma delimited list of services')
    return parser.parse_args()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(parse_args()))
    loop.close()
