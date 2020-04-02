#!/bin/bash
# shellcheck disable=SC2181,SC1091,SC2013

PROJECT_CATALOG=${1}
PARENT_ID=${2}

basedir=$(dirname "$0")
result=0

# Enable/disable gcp services in projects
for project in $(gcloud projects list --format="value(PROJECT_ID)" --filter="parent.id=${PARENT_ID}")
do
    echo "Managing services for ${project}..."

    enabled="/tmp/${project}.enabled"
    specified="/tmp/${project}.specified"
    excluded="/tmp/${project}.excluded"

    echo "source.googleapis.com" > "${excluded}"

    gcloud services list --enabled --format="value(NAME)" --project "${project}" > "${enabled}"
    python3 "${basedir}"/list_services.py "${project}" "${PROJECT_CATALOG}" > "${specified}"

    disabled=$(python3 "${basedir}"/compare_lists.py "${enabled}" "${specified}" "${excluded}")

    for service in ${disabled}
    do
        echo " + disable ${service} in ${project}"
        # gcloud services disable "${service}" --project "${project}" --async
    done

    for service in $(cat "$specified")
    do
        echo " + enable ${service} in ${project}"
        gcloud services enable "${service}" --project "${project}" --async
    done

    if [ $? -ne 0 ]
    then
        echo "ERROR enabling/disabling services for ${project}"
        result=1
    fi

done

if [ ${result} -ne 0 ]
then
    echo "At least one error occurred during enabling/disabling services"
    exit 1
fi
