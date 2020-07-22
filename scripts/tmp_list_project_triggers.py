import json
import uuid
import sys

cloud_deployment_branch = 'develop'

if len(sys.argv) > 2:
    project_id = sys.argv[2]
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)
    for pr in projects['projects']:
        if pr['projectId'] == project_id and 'triggers' in pr and len(pr['triggers']) > 0:
            for tr in pr['triggers']:
                if 'triggerTemplate' in tr:
                    if not 'projectId':
                        tr['triggerTemplate']['projectId'] = pr['projectId']

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

                if 'includedFiles' in tr or 'excludedFiles' in tr:
                    tr['name'] = tr['name'] + '-' + str(uuid.uuid4())[:4]

                print(json.dumps(tr))
