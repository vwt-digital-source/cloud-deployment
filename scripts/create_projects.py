import sys


def generate_config(context):
    resources = []

    for project in projects['projects']:
        resources.append({
            'name': project['projectId'],
            'type': 'cloudresourcemanager.v1.project',
            'properties': {
                'name': project['projectId'],
                'projectId': project['projectId'],
                'parent': {
                    'type': 'folder',
                    'id': '{}'.format(context.properties['parent_folder_id'])
                }
            }
        })
        resources.append({
            'name': 'billing_{}'.format(project['projectId']),
            'type': 'deploymentmanager.v2.virtual.projectBillingInfo',
            'metadata': {
                'dependsOn': [project['projectId']]
            },
            'properties': {
                'name': 'projects/{}'.format(project['projectId']),
                'billingAccountName': context.properties['billing_account_name']
            }
        })
        index = 0
        for service in project.get('services', []):
            depends_on = [project['projectId'], 'billing_{}'.format(project['projectId'])]
            if index != 0:
                depends_on.append('{}-{}-api'.format(project['projectId'], project['services'][index-1]))
            resources.append({
                'name': '{}-{}-api'.format(project['projectId'], service),
                'type': 'deploymentmanager.v2.virtual.enableService',
                'metadata': {
                    'dependsOn': depends_on
                },
                'properties': {
                    'consumerId': 'project:{}'.format(project['projectId']),
                    'serviceName': service
                }
            })
            index += 1
        depends_on = [project['projectId'], 'billing_{}'.format(project['projectId'])]
        for keyring in project.get('keyrings', []):
            resources.append({
                'name': '{}-{}-keyring'.format(project['projectId'], keyring['name']),
                'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings',
                'metadata': {
                    'dependsOn': depends_on
                },
                'properties': {
                    'parent': 'projects/' + project['projectId'] + '/locations/' + keyring['region'],
                    'keyRingId': keyring['name']
                }
            })
            depends_on = ['{}-{}-keyring'.format(project['projectId'], keyring['name'])]
            for key in keyring['keys']:
                resources.append({
                    'name': '{}-{}-{}-key'.format(project['projectId'], keyring['name'], key['name']),
                    'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings.cryptoKeys',
                    'metadata': {
                        'dependsOn': depends_on
                    },
                    'properties': {
                        'parent': '$(ref.{}-{}-keyring.name)'.format(project['projectId'], keyring['name']),
                        'cryptoKeyId': key['name'],
                        'purpose': key['purpose']
                    }
                })
                depends_on = ['{}-{}-{}-key'.format(project['projectId'], keyring['name'], key['name'])]

    return {'resources': resources}
