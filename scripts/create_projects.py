import sys


def gather_permissions(preDefinedBindings, resource_name, odrlPolicy):
    bindings = preDefinedBindings

    if odrlPolicy is not None:
        for permission in [p for p in odrlPolicy.get('permission', []) if p.get('target', '') == resource_name]:
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
        iam_policies_depends = [project['projectId']]
        if 'services' in project:
            services = project['services']
            services.append('cloudbuild.googleapis.com') if 'cloudbuild.googleapis.com' not in services else services
            services.append('pubsub.googleapis.com') if 'pubsub.googleapis.com' not in services else services
            services.append('cloudfunctions.googleapis.com') if 'cloudfunctions.googleapis.com' not in services else services
            services.append('cloudresourcemanager.googleapis.com') if 'cloudresourcemanager.googleapis.com' not in services else services
        else:
            project['services'] = ['cloudbuild.googleapis.com', 'pubsub.googleapis.com', 'cloudfunctions.googleapis.com',
                    'cloudresourcemanager.googleapis.com']
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
            iam_policies_depends.append('{}-{}-api'.format(project['projectId'], service))
        for account in project.get('serviceAccounts', []):
            resources.append({
                'name': account,
                'type': 'iam.v1.serviceAccount',
                'properties': {
                    'accountId': account
                    'displayName': account + 'service account',
                    'projectId': project['projectId']
                }
            })
        resources.append({
            'name': 'get-iam-policy-' + project['projectId'],
            'action': 'gcp-types/cloudresourcemanager-v1:cloudresourcemanager.projects.getIamPolicy',
            'properties': {
                'resource': project['projectId'],
            },
            'metadata': {
                'dependsOn': iam_policies_depends,
                'runtimePolicy': ['UPDATE_ALWAYS']
            }
        })
        projectPreDefinedBindings = [
            {
                'role': 'roles/editor',
                'members': [
                    'serviceAccount:$(ref.' + project['projectId'] + '.projectNumber)@cloudbuild.gserviceaccount.com'
                ]
            },
            {
                'role': 'roles/cloudfunctions.admin',
                'members': [
                    'serviceAccount:$(ref.' + project['projectId'] + '.projectNumber)@cloudbuild.gserviceaccount.com'
                ]
            },
            {
                'role': 'roles/owner',
                'members': [
                    'serviceAccount:$(ref.' + project['projectId'] + '.projectNumber)@cloudservices.gserviceaccount.com'
                ]
            }
        ]
        resources.append({
            'name': 'patch-iam-policy-' + project['projectId'],
            'action': 'gcp-types/cloudresourcemanager-v1:cloudresourcemanager.projects.setIamPolicy',
            'properties': {
                'resource': project['projectId'],
                'policy': '$(ref.get-iam-policy-' + project['projectId'] + ')',
                'gcpIamPolicyPatch': {
                    'add': gather_permissions(projectPreDefinedBindings, project['projectId'], project.get('odrlPolicy'))
                }
            }
        })
        depends_on = [project['projectId'], 'billing_{}'.format(project['projectId']), '{}-cloudkms.googleapis.com-api'.format(project['projectId'])]
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
