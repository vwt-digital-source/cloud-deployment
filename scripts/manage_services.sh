#!/bin/bash
# shellcheck disable=SC2181,SC1091,SC2013,SC2046,SC2086

PROJECT_CATALOG=${1}
PARENT_ID=${2}

basedir=$(dirname "$0")
result=0

# Disable gcp services in projects
for project in $(gcloud projects list --format="value(PROJECT_ID)" --filter="parent.id=${PARENT_ID}")
do
    echo "Managing services for ${project}..."

    excluded="source.googleapis.com"
    specified=$(python3 "${basedir}"/list_services.py "${project}" "${PROJECT_CATALOG}")

    enabled=$(gcloud services list --enabled --format="value(NAME)" --project "${project}")
    disable=$(python3 "${basedir}"/compare_lists.py "${enabled}" "${specified}" "${excluded}")

    for service in $disable
    do
        echo " + disable ${service} in ${project}"
    done

    gcloud services disable ${disable} --project "${project}" --force

    enabled=$(gcloud services list --enabled --format="value(NAME)" --project "${project}")
    enable=$(python3 "${basedir}"/compare_lists.py "${specified}" "${enabled}" "${excluded}")

    for service in $enable
    do
        echo " + enable ${service} in ${project}"
    done

    gcloud services enable ${enable} --project "${project}"

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
