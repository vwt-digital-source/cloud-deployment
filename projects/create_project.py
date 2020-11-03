import re
from hashlib import sha256


def gather_permissions(resource_name, odrlPolicy, bindings=[]):

    if odrlPolicy:
        for permission in [p for p in odrlPolicy.get('permission', [])
                           if 'serviceAccount:' not in p.get('target', '') and p.get('target', '') == resource_name]:
            role_to_add = permission['action']
            binding = next((b for b in bindings if b['role'] == role_to_add), None)
            if not binding:
                binding = {
                    'role': role_to_add,
                    'members': []
                }
                bindings.append(binding)
            if not permission['assignee'] in binding['members']:
                binding['members'].append(permission['assignee'])

    return bindings


def generate_config(context):

    resources = []

    for project in [projects]:  # noqa: F821

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

        all_services = []
        for service in list(set(project.get('services', []) + services.get('default', []))):  # noqa: F821
            resource_name = '{}-{}-api'.format(project['projectId'], service)
            resources.append({
                'name': resource_name,
                'type': 'deploymentmanager.v2.virtual.enableService',
                'metadata': {
                    'dependsOn': ['billing_{}'.format(project['projectId'])]
                },
                'properties': {
                    'consumerId': 'project:{}'.format(project['projectId']),
                    'serviceName': service
                }
            })
            all_services.append(resource_name)

        all_service_accounts = []
        for account in list(set(project.get('serviceAccounts', []) + service_accounts.get('default', []))):  # noqa: F821
            resource_name = '{}-{}-svcaccount'.format(project['projectId'], account)
            resources.append({
                'name': resource_name,
                'type': 'iam.v1.serviceAccount',
                'metadata': {
                    'dependsOn': all_services
                },
                'properties': {
                    'accountId': account,
                    'displayName': '{} service account'.format(account),
                    'projectId': project['projectId']
                }
            })
            all_service_accounts.append(resource_name)

        odrlPolicy = project.get('odrlPolicy')
        if odrlPolicy and odrlPolicy.get('permission'):
            for permission in odrlPolicy.get('permission', []):
                if permission['target'] == project['projectId']:
                    suffix = sha256('{}-{}-{}'.format(
                        permission['action'],
                        permission['assignee'],
                        permission['target']).encode('utf-8')).hexdigest()[:10]
                    resources.append({
                        'name': '{}-iampolicy'.format(suffix),
                        'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                        'properties': {
                            'resource': project['projectId'],
                            'role': permission['action'],
                            'member': permission['assignee']
                        },
                        'metadata': {
                            'dependsOn': all_service_accounts
                        }
                    })

                if 'serviceAccount' in permission['target']:
                    target_name = permission['target'].replace('serviceAccount:', '')
                    resource_target = 'projects/{}/serviceAccounts/{}'.format(project['projectId'], target_name)
                    assignee_name = re.search(":(.*?)@", permission['assignee']).group(1).replace('.', '-')
                    resource_name = target_name.split('@')[0] + assignee_name + '-sa-iampolicy'
                    resources.append({
                        'name': resource_name,
                        'action': 'gcp-types/iam-v1:iam.projects.serviceAccounts.setIamPolicy',
                        'metadata': {
                            'dependsOn': all_service_accounts
                        },
                        'properties': {
                            'resource': resource_target,
                            'policy': {
                                'bindings': [
                                    {
                                        "role": permission['action'],
                                        "members": [permission['assignee']]
                                    }
                                ]
                            }
                        }
                    })

        for binding in iam_bindings.get('default', []):  # noqa: F821
            member = binding['member'].replace('__PROJECT_ID__', project['projectId'])
            suffix = sha256('{}-{}-{}'.format(
                binding['role'],
                member,
                project['projectId']).encode('utf-8')).hexdigest()[:10]
            resources.append({
                'name': '{}-default-iampolicy'.format(suffix),
                'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                'properties': {
                    'resource': project['projectId'],
                    'role': binding['role'],
                    'member': member
                },
                'metadata': {
                    'dependsOn': all_service_accounts
                }
            })

        for keyring in project.get('keyrings', []):
            resources.append({
                'name': '{}-{}-keyring'.format(project['projectId'], keyring['name']),
                'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings',
                'metadata': {
                    'dependsOn': ['{}-cloudkms.googleapis.com-api'.format(project['projectId'])]
                },
                'properties': {
                    'parent': 'projects/{}/locations/{}'.format(project['projectId'], keyring['region']),
                    'keyRingId': keyring['name']
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings': gather_permissions(keyring['name'], project.get('odrlPolicy'), [])
                    }
                }
            })

            for key in keyring.get('keys', []):
                resources.append({
                    'name': '{}-{}-{}-key'.format(project['projectId'], keyring['name'], key['name']),
                    'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings.cryptoKeys',
                    'metadata': {
                        'dependsOn': ['{}-{}-keyring'.format(project['projectId'], keyring['name'])]
                    },
                    'properties': {
                        'parent': '$(ref.{}-{}-keyring.name)'.format(project['projectId'], keyring['name']),
                        'cryptoKeyId': key['name'],
                        'purpose': key['purpose']
                    }
                })

    return {'resources': resources}
