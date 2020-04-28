import json
import logging
import argparse

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


def main(args):
    service = make_service()

    projects = json.load(open(args.projects_file))
    default_service_accounts = json.load(open(args.service_accounts_file)).get('default', [])

    documented_service_accounts = []
    active_service_accounts = []

    for project in projects.get('projects', []):

        for service_account in project.get('serviceAccounts', []):
            documented_service_accounts.append({
                "projectId": project['projectId'],
                "serviceAccount": service_account
            })

        for service_account in default_service_accounts:
            documented_service_accounts.append({
                "projectId": project['projectId'],
                "serviceAccount": service_account
            })

        active_service_accounts.extend(get_service_accounts(service, project['projectId']))

    for service_account in active_service_accounts:
        logging.info('FOUND {}'.format(service_account))
        if 'iam.gserviceaccount.com' not in service_account['name']:
            continue
        for item in documented_service_accounts:
            if not "projects/{}/serviceAccounts/{}".format(item['projectId'], item['serviceAccount']) in service_account['name']:
                delete_service_account(service, service_account)


def get_service_accounts(service, project_id):
    service_accounts = []
    request = service.projects().serviceAccounts().list(
        name="projects/{}".format(project_id))
    while True:
        response = request.execute()
        for service_account in response.get('accounts', []):
            service_accounts.append(service_account)
        request = service.projects().serviceAccounts().list_next(
            previous_request=request,
            previous_response=response)
        if request is None:
            break
    return service_accounts


def delete_service_account(service, service_account):
    # service.projects().serviceAccounts().delete(name=service_account['name']).execute()
    logging.info("REMOVED {}".format(service_account['name']))


def make_service():
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam', 'v1', credentials=credentials)
    return service


def parse_args():
    parser = argparse.ArgumentParser(description='Remove undocumented service accounts')
    parser.add_argument('-p', '--projects-file',
                        required=True,
                        help='path to projects.json file')
    parser.add_argument('-s', '--service-accounts-file',
                        required=True,
                        help='path to service_accounts.json file')
    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())
