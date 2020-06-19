#!/bin/bash
# shellcheck disable=SC2181

PROJECT_CATALOG=${1}
REGION=${2}
GROUP=${3}

if [[ -z "${PROJECT_CATALOG}" || -z "${REGION}" ]]
then
    echo "PROJECT_CATALOG parameter should be set"
    echo "REGION parameter should be set"
    echo "Usage: ${0} <project_catalog> <region>"
    exit 1
fi

basedir=$(dirname "$0")
result=0

cat << EOF > lifecycle.json
{ "rule": [ { "action": { "type": "Delete" }, "condition": { "age": 30 } } ] }
EOF

for project in $(python3 "${basedir}"/list_projects.py "${PROJECT_CATALOG}")
do

    echo "Check if Cloud Build bucket exists for project ${project}..."

    gsutil ls -b -p "${project}" "gs://${project}_cloudbuild" >/dev/null 2>&1

    if [ $? -ne 0 ]
    then

        echo " + Creating cloud build bucket"
        gsutil mb -c standard -p "${project}" -l "${REGION}" -b on "gs://${project}_cloudbuild"

        if [ $? -ne 0 ]
        then
            echo "ERROR creating default Cloud Build bucket for ${project}"
            result=1
        fi

    else
        echo " + Cloud build bucket already exists"
    fi

    echo "Set lifecycle on bucket..."

    gsutil lifecycle set lifecycle.json "gs://${project}_cloudbuild"

    echo "Set permissions on bucket..."

    gsutil iam ch "group:${GROUP}:roles/storage.legacyObjectReader" "gs://${project}_cloudbuild"
    gsutil iam ch "group:${GROUP}:roles/storage.legacyBucketReader" "gs://${project}_cloudbuild"

    if [ $? -ne 0 ]
    then
        echo "ERROR setting lifecycle policy for Cloud Build bucket"
        result=1
    fi

done

if [ ${result} -ne 0 ]
then
    echo "At least one error occurred while creating default Cloud Build bucket"
    exit 1
fi
