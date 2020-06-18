import re
from hashlib import sha1


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


def gather_permissions_sa(project_id, odrl_policy):
    resources = []
    if odrl_policy is not None:
        for permission in [p for p in odrl_policy.get('permission', []) if 'serviceAccount' in p.get('target', '')]:
            target_name = permission['target'].replace('serviceAccount:', '')
            resource_name = 'patch-sa-policy-' + re.sub(r'[^A-Za-z0-9]+', '-', target_name)
            resource_target = 'projects/{}/serviceAccounts/{}'.format(
                project_id, target_name)

            resource = next((p for p in resources if p.get('name', '') == resource_name), None)
            if not resource:
                resource = {
                    'name': resource_name,
                    'action': 'gcp-types/iam-v1:iam.projects.serviceAccounts.setIamPolicy',
                    'metadata': {
                        'dependsOn': [project_id]
                    },
                    'properties': {
                        'resource': resource_target,
                        'policy': {
                            'bindings': []
                        }
                    }
                }
                resources.append(resource)

            binding = next((b for b in resource['properties']['policy']['bindings'] if
                            b.get('role', '') == permission['action']), None)
            if not binding:
                binding = {
                    'role': permission['action'],
                    'members': []
                }
                resource['properties']['policy']['bindings'].append(binding)

            if not permission['assignee'] in binding['members']:
                binding['members'].append(permission['assignee'])

    return resources


def generate_config(context):

    resources = []

    for project in projects['projects']:  # noqa: F821

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

        services = []
        for service in list(project.get('services', []) + services.get('default', [])):  # noqa: F821
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
            services.append(resource_name)

        service_accounts = []
        for account in list(project.get('serviceAccounts', []) + service_accounts.get('default', [])):  # noqa: F821
            resource_name = '{}-{}-svcaccount'.format(project['projectId'], account)
            resources.append({
                'name': resource_name,
                'type': 'iam.v1.serviceAccount',
                'metadata': {
                    'dependsOn': [project['projectId']]
                },
                'properties': {
                    'accountId': account,
                    'displayName': '{} service account'.format(account),
                    'projectId': project['projectId']
                }
            })
            service_accounts.append(resource_name)

        resources.extend(gather_permissions_sa(project['projectId'], project.get('odrlPolicy')))

        odrlPolicy = project.get('odrlPolicy')
        if odrlPolicy and odrlPolicy.get('permission'):
            for permission in odrlPolicy.get('permission', []):
                if permission['target'] == project['projectId']:
                    suffix = sha1('{}-{}-{}'.format(
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
                            'dependsOn': service_accounts
                        }
                    })

        for binding in iam_bindings.get('default', []):  # noqa: F821
            member = binding['member'].replace('__PROJECT_ID__', project['projectId'])
            suffix = sha1('{}-{}-{}'.format(binding['role'], member, project['projectId']).encode('utf-8')).hexdigest()[:10]
            resources.append({
                'name': '{}-default-iampolicy'.format(suffix),
                'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                'properties': {
                    'resource': project['projectId'],
                    'role': binding['role'],
                    'member': member
                },
                'metadata': {
                    'dependsOn': service_accounts
                }
            })

        for keyring in project.get('keyrings', []):
            resources.append({
                'name': '{}-{}-keyring'.format(project['projectId'], keyring['name']),
                'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings',
                'metadata': {
                    'dependsOn': ['{}-cloudkms.googleapis.com-api'.format(project['projectId'])] + service_accounts
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
