#!/bin/bash

repoName=${1}
branchName=${2}

if [ -z "${repoName}" -o -z "${branchName}" ]
then
    echo "Please specify repository name and branch name to run the build trigger for"
    echo "Syntax: $0 <repoName> <branchName>"
    exit 1
fi

gcp_access_token=$(gcloud config config-helper --format='value(credential.access_token)')
echo $gcp_access_token
curl -X GET -H "Authorization: Bearer ${gcp_access_token}" "https://cloudbuild.googleapis.com/v1/projects/${PROJECT_ID}/triggers" > triggers.json
python3 gettriggertemplate.py triggers.json ${repoName} ${branchName} | tee triggertemplate.json
triggerid=$(python3 gettriggerid.py triggers.json ${repoName} ${branchName})
echo "triggerid: ${triggerid}"
echo "triggertemplate: ${triggertemplate}"
curl -X POST -T triggertemplate.json -H "Authorization: Bearer ${gcp_access_token}" "https://cloudbuild.googleapis.com/v1/projects/${PROJECT_ID}/triggers/${triggerid}:run"
