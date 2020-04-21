import json
import sys
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()
service = discovery.build('iam', 'v1', credentials=credentials)

documented_serviceaccounts = []
active_serviceaccounts = []
to_be_removed_service_accounts = []

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)

    for pr in projects['projects']:
        if 'serviceAccounts' in pr:
            for sa in pr['serviceAccounts']:
                documented_serviceaccounts.append({"projectId": pr['projectId'], "serviceAccount": sa})

        request = service.projects().serviceAccounts().list(name="projects/{}".format(pr['projectId']))
        while True:
            response = request.execute()

            for service_account in response.get('accounts', []):
                active_serviceaccounts.append(service_account)

            request = service.projects().serviceAccounts().list_next(previous_request=request, previous_response=response)
            if request is None:
                break

    for sa in active_serviceaccounts:
        remove = False
        if 'iam.gserviceaccount.com' in sa['name']:
            if not next((item for item in documented_serviceaccounts if "projects/{}/serviceAccounts/{}".format(item['projectId'], item['serviceAccount']) in sa['name']), False):
                remove = True
            else:
                print("FOUND {}".format(sa))

        if remove:
            to_be_removed_service_accounts.append(sa)

    for sa in to_be_removed_service_accounts:
        service.projects().serviceAccounts().delete(name=sa['name']).execute()
        print("remove {}".format(sa['name']))
