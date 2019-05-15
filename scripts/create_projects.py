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
                    'id': context.properties['parent_folder_id']
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
        for service in project.get('services', []):
            resources.append({
                'name': '{}-{}-api'.format(project['projectId'], service),
                'type': 'deploymentmanager.v2.virtual.enableService',
                'metadata': {
                    'dependsOn': [project['projectId'], 'billing_{}'.format(project['projectId'])]
                },
                'properties': {
                    'consumerId': 'project:{}'.format(project['projectId']),
                    'serviceName': service
                }
            })

    return {'resources': resources}
