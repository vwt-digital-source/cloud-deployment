#!/bin/bash
# shellcheck disable=SC2181

PROJECT_CATALOG=${1}
REGION=${2}

basedir=$(dirname "$0")
result=0

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

done

if [ ${result} -ne 0 ]
then
    echo "At least one error occurred while creating default Cloud Build bucket"
    exit 1
fi
