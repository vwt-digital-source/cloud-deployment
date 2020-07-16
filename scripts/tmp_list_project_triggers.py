import json
import sys

cloud_deployment_branch = 'develop'

projectsfile = open(sys.argv[1])
project = json.load(projectsfile)
for tr in project.get('triggers', []):
    if 'triggerTemplate' in tr:
        if not 'projectId':
            tr['triggerTemplate']['projectId'] = project['projectId']

        tr['description'] = 'Push to {} {} branch'.format(
            tr['triggerTemplate']['repoName'],
            tr['triggerTemplate']['branchName'])
        tr['name'] = tr['description'].replace(' ', '-')

    if 'github' in tr:

        if 'tag' in tr['github']['push']:
            tr['description'] = 'Push to {} tag'.format(
                tr['github']['name'])
            tr['name'] = tr['description'].replace(' ', '-')
            regex = tr['github']['push']['tag'].replace('\\\\', '\\')
            tr['github']['push']['tag'] = regex

        if 'branch' in tr['github']['push']:
            tr['description'] = 'Push to {} {} branch'.format(
                tr['github']['name'],
                tr['github']['push']['branch'])
            tr['name'] = tr['description'].replace(' ', '-')

    if 'runTrigger' in tr:
        tr['build'] = {
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
                            tr['runTrigger']['repoName'],
                            tr['runTrigger']['branchName'])
                    ],
                    'dir': 'cloud-deployment/scripts'
                }
            ]
        }
        del tr['runTrigger']
    print(json.dumps(tr))
