#!/bin/bash

project_id=${1}
repoName=${2}
branchName=${3}

if [ -z "${repoName}" ] || [ -z "${branchName}" ]
then
    echo "Please specify repository name and branch name to run the build trigger for"
    echo "Syntax: $0 <projectId> <repoName> <branchName>"
    exit 1
fi

gcp_access_token=$(gcloud config config-helper --format='value(credential.access_token)')
curl -X GET -H "Authorization: Bearer ${gcp_access_token}" "https://cloudbuild.googleapis.com/v1/projects/${project_id}/triggers" > triggers.json
python3 gettriggertemplate.py triggers.json "${project_id}" "${repoName}" "${branchName}" | tee triggertemplate.json
triggerid=$(python3 gettriggerid.py triggers.json "${repoName}" "${branchName}")
echo "triggerid: ${triggerid}"
curl -X POST -T triggertemplate.json -H "Authorization: Bearer ${gcp_access_token}" "https://cloudbuild.googleapis.com/v1/projects/${project_id}/triggers/${triggerid}:run"
