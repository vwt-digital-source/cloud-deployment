import re
from hashlib import sha1


def gather_permissions(preDefinedBindings, resource_name, odrlPolicy):
    bindings = preDefinedBindings

    if odrlPolicy is not None:
        for permission in [p for p in odrlPolicy.get('permission', [])
                           if 'serviceAccount:' not in p.get('target', '') and p.get('target', '') == resource_name]:
            role_to_add = permission['action']
            if not bindings:
                bindings = []
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


def gather_permissions_sa(project_id, odrl_policy, depends_on):
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
                        'dependsOn': depends_on
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


def append_gcp_policy(resource, resource_name, odrlPolicy):
    permissions = gather_permissions(None, resource_name, odrlPolicy)
    if permissions is not None:
        resource['accessControl'] = {
            'gcpIamPolicy': {
                'bindings': permissions
            }
        }


def generate_config(context):
    resources = []
    project_index = 0
    max_projects_parallel = 5
    project_depends = []

    for project in projects['projects']:  # noqa: F821
        project_def = {
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
        }
        if len(project_depends) > project_index % max_projects_parallel:
            project_def.update({
                'metadata': {
                    'dependsOn': [project_depends[project_index % max_projects_parallel]]
                }
            })
            project_depends[project_index % max_projects_parallel] = project['projectId']
        else:
            project_depends.append(project['projectId'])
        project_index += 1
        resources.append(project_def)
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

        iam_policies_depends = [project['projectId']]
        services_list = []
        all_services = list(set(project.get('services', []) + services.get('default', [])))  # noqa: F821
        for index, service in enumerate(all_services):
            depends_on = [project['projectId'], 'billing_{}'.format(project['projectId'])]
            if index != 0:
                depends_on.append('{}-{}-api'.format(project['projectId'], all_services[index-1]))
            service_to_add = '{}-{}-api'.format(project['projectId'], service)
            services_list.append(service_to_add)
            resources.append({
                'name': service_to_add,
                'type': 'deploymentmanager.v2.virtual.enableService',
                'metadata': {
                    'dependsOn': depends_on
                },
                'properties': {
                    'consumerId': 'project:{}'.format(project['projectId']),
                    'serviceName': service
                }
            })
            iam_policies_depends.append('{}-{}-api'.format(project['projectId'], service))

        default_service_accounts = service_accounts.get('default', [])  # noqa: F821

        documented_service_accounts = project.get('serviceAccounts', [])
        documented_service_accounts.extend(default_service_accounts)

        service_accounts_list = []
        for account in list(set(documented_service_accounts)):
            resource_name = '{}-{}-svcaccount'.format(project['projectId'], account)
            resources.append({
                'name': resource_name,
                'type': 'iam.v1.serviceAccount',
                'metadata': {
                    'dependsOn': [project['projectId']]
                },
                'properties': {
                    'accountId': account,
                    'displayName': account + ' service account',
                    'projectId': project['projectId']
                }
            })
            service_accounts_list.append(resource_name)

        resources.extend(gather_permissions_sa(project['projectId'], project.get('odrlPolicy'), iam_policies_depends))

        odrlPolicy = project.get('odrlPolicy')
        if odrlPolicy and odrlPolicy.get('permission'):
            for permission in odrlPolicy.get('permission', []):
                if permission['target'] == project['projectId']:
                    suffix = sha1('{}-{}-{}'.format(permission['action'], permission['assignee'], permission['target']).encode('utf-8')).hexdigest()[:10]
                    resources.append({
                        'name': '{}-iampolicy'.format(suffix),
                        'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                        'properties': {
                            'resource': project['projectId'],
                            'role': permission['action'],
                            'member': permission['assignee']
                        },
                        'metadata': {
                            'dependsOn': service_accounts_list
                        }
                    })

        for binding in iam_bindings.get('default', []):  # noqa: F821
            binding['member'] = binding['member'].replace('__PROJECT_ID__', project['projectId'])
            suffix = sha1('{}-{}-{}'.format(binding['role'], binding['member'], project['projectId']).encode('utf-8')).hexdigest()[:10]
            resources.append({
                'name': '{}-default-iampolicy'.format(suffix),
                'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                'properties': {
                    'resource': project['projectId'],
                    'role': binding['role'],
                    'member': binding['member']
                },
                'metadata': {
                    'dependsOn': service_accounts_list
                }
            })

        depends_on = [project['projectId'], 'billing_{}'.format(project['projectId']),
                      '{}-cloudkms.googleapis.com-api'.format(project['projectId'])] + \
            services_list + service_accounts_list

        for keyring in project.get('keyrings', []):
            keyringResource = {
                'name': '{}-{}-keyring'.format(project['projectId'], keyring['name']),
                'type': 'gcp-types/cloudkms-v1:projects.locations.keyRings',
                'metadata': {
                    'dependsOn': depends_on
                },
                'properties': {
                    'parent': 'projects/' + project['projectId'] + '/locations/' + keyring['region'],
                    'keyRingId': keyring['name']
                }
            }
            append_gcp_policy(keyringResource, keyring['name'], project.get('odrlPolicy'))
            resources.append(keyringResource)
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
