#!/bin/bash
# shellcheck disable=SC2181,SC2030,SC2031,SC2086

PROJECT_CATALOG=${1}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_CATALOG}" ]] || error_exit "Missing required PROJECT_CATALOG"

basedir=$(dirname "$0")
result=0

for project in $(python3 "${basedir}"/list_projects.py "${PROJECT_CATALOG}")
do
    echo "Creating build triggers in ${project}..."
    python3 "${basedir}"/list_project_triggers.py "${PROJECT_CATALOG}" "${project}" |
    while read -r trigger
    do

        echo "${trigger}" > trigger.json
        trigger_name=$(python3 "${basedir}"/get_trigger.py trigger.json "name")
        trigger_id=$(gcloud beta builds triggers list \
                          --filter="name=${trigger_name}" \
                          --project="${project}" \
                          --format="value(id)")

        if [ -n "${trigger_id}" ]
        then
            echo " - Delete build trigger ${trigger_name}"
            gcloud beta builds triggers delete "${trigger_id}" --project="${project}" --quiet
        fi

        echo " + Create new build trigger ${trigger_name}"

        gcloud beta builds triggers create github --project="${project}" --trigger-config=trigger.json

        if [ $? -ne 0 ]
        then
            echo "ERROR creating cloud build trigger ${trigger_name} in project ${project}"
            result=1
        fi

    done

done

if [ ${result} -ne 0 ]
then
    echo "At least one error occurred during cloud build trigger provisioning"
    exit 1
fi
