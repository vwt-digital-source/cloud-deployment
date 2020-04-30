import re
import logging
import argparse

from datetime import datetime
from dateutil.parser import parse
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

logging.basicConfig(level=logging.INFO, format='%(levelname)7s: %(message)s')
logging.getLogger('googleapiclient').setLevel(logging.WARNING)


def make_service():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials, cache_discovery=False)
    return service


def list_keys(service, project_id, service_account):
    name = 'projects/{}/serviceAccounts/{}'.format(project_id, service_account['email'])
    response = service.projects().serviceAccounts().keys().list(
        name=name).execute()
    return response.get('keys')


def list_service_accounts(service, project_id):
    name = 'projects/{}'.format(project_id)
    response = service.projects().serviceAccounts().list(
        name=name).execute()
    return response.get('accounts')


def delete_service_account_key(service, key):
    service.projects().serviceAccounts().keys().delete(
        name=key['name']).execute()


def is_expired(key, valid_days):
    created = parse(key.get('validAfterTime')).replace(tzinfo=None)
    now = datetime.utcnow().replace(tzinfo=None)
    delta = now - created
    if delta.days > valid_days:
        return True


def main(args):
    service = make_service()
    for project_id in args.projects:
        logging.info('Checking service account keys for project {}...'.format(project_id))
        service_accounts = list_service_accounts(service, project_id)

        sa_keys = []
        for sa in service_accounts:
            sa_keys.extend(list_keys(service, project_id, sa))

        user_managed_keys = []
        for key in sa_keys:
            if key['keyType'] == 'USER_MANAGED':
                user_managed_keys.append(key)

        expired_keys = []
        for key in user_managed_keys:
            if is_expired(key, args.days):
                expired_keys.append(key)

        logging.info('Found {} key(s) older than {} days!'.format(len(expired_keys), args.days))

        for key in expired_keys:
            logging.info('Deleting key {}...'.format(key['name']))
            delete_service_account_key(service, key)


def parse_args():
    parser = argparse.ArgumentParser(description='Revoke service account keys in projects after x days')
    parser.add_argument('-p', '--projects',
                        type=lambda s: re.split(' |\n|, ', s),
                        required=True,
                        help='a new line, space or comma delimited list of projects')
    parser.add_argument('-d', '--days',
                        type=int,
                        required=True,
                        help='number of days')
    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())
