import re
import asyncio
import argparse
import logging

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials

logging.basicConfig(level=logging.INFO, format='%(levelname)7s: %(message)s')


async def main(args):
    service = make_service()
    await asyncio.gather(
        *[process(service, project, args.services, args.config) for project in args.projects]
    )


async def process(service, project_id, services, config):
    logging.info('Updating {} for project {}...'.format(config, project_id))
    policy = await get_iam_policy(service, project_id)
    updated_policy = await set_policy(policy, services, config)
    await set_iam_policy(service, project_id, updated_policy, config)
    logging.info('Updated {} for project {}'.format(config, project_id))


async def get_iam_policy(service, project_id):
    try:
        request = service.projects().getIamPolicy(resource=project_id, body={})
        response = request.execute()
        return response
    except HttpError:
        logging.exception('Request getIamPolicy failed for project {}'.format(project_id))
        raise


async def set_iam_policy(service, project_id, policy, config):
    try:
        body = {
            'policy': policy,
            'updateMask': config
        }
        request = service.projects().setIamPolicy(resource=project_id, body=body)
        response = request.execute()
        return response
    except HttpError:
        logging.exception('Request setIamPolicy failed for project {}'.format(project_id))
        raise


async def set_policy(policy, services, config):
    if config == 'auditConfigs':
        policy[config] = []
        for service in services:
            policy[config].append({
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
    parser = argparse.ArgumentParser(description='Add gcp audit log configuration async')
    parser.add_argument('-p', '--projects',
                        type=lambda s: re.split(' |\n|, ', s),
                        required=True,
                        help='a new line, space or comma delimited list of services')
    parser.add_argument('-s', '--services',
                        type=lambda s: re.split(' |\n|, ', s),
                        required=True,
                        help='a new line, space or comma delimited list of services')
    parser.add_argument('-c', '--config',
                        choices=['auditConfigs'],
                        required=True,
                        help='the name of the iam policy config to set')
    return parser.parse_args()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(parse_args()))
    loop.close()
