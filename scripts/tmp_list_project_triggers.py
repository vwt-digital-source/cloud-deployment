import json
import uuid
import sys

cloud_deployment_branch = 'develop'

projectfile = open(sys.argv[2])
project = json.load(projectfile)
for trigger in project['triggers']:
    if 'triggerTemplate' in trigger:
        if not 'projectId':
            trigger['triggerTemplate']['projectId'] = project['projectId']

        trigger['description'] = 'Push to {} {} branch'.format(
            trigger['triggerTemplate']['repoName'],
            trigger['triggerTemplate']['branchName'])
        trigger['name'] = trigger['description'].replace(' ', '-')

    if 'github' in trigger:

        if 'tag' in trigger['github']['push']:
            trigger['description'] = 'Push to {} tag'.format(
                trigger['github']['name'])
            trigger['name'] = trigger['description'].replace(' ', '-')
            regex = trigger['github']['push']['tag'].replace('\\\\', '\\')
            trigger['github']['push']['tag'] = regex

        if 'branch' in trigger['github']['push']:
            trigger['description'] = 'Push to {} {} branch'.format(
                trigger['github']['name'],
                trigger['github']['push']['branch'])
            trigger['name'] = trigger['description'].replace(' ', '-')

    if 'runTrigger' in trigger:
        trigger['build'] = {
            'steps': [
                {
                    'name': 'gcr.io/cloud-builders/git',
                    'args': [
                        'clone',
                        '--branch={}'.format(cloud_deployment_branch),
                        'https://github.com/vwt-digital/cloud-deployment.git'
                    ]
                },
                {
                    'name': 'gcr.io/cloud-builders/gcloud',
                    'entrypoint': 'bash',
                    'args': [
                        '-c',
                        './runcloudbuildtrigger.sh ${{PROJECT_ID}} {} {}'.format(
                            trigger['runTrigger']['repoName'],
                            trigger['runTrigger']['branchName'])
                    ],
                    'dir': 'cloud-deployment/scripts'
                }
            ]
        }
        del trigger['runTrigger']

    if 'includedFiles' in trigger or 'excludedFiles' in trigger:
        trigger['name'] = trigger['name'] + '-' + str(uuid.uuid4())[:4]

    print(json.dumps(trigger))
