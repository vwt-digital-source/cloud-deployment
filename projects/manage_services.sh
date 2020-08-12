#!/bin/bash

PROJECT_ID=${1}
PROJECT_CATALOG=${2}
SERVICE_CATALOG=${3}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${PROJECT_CATALOG}" ]] || error_exit "Missing required PROJECT_CATALOG"
[[ -n "${SERVICE_CATALOG}" ]] || error_exit "Missing required SERVICE_CATALOG"

basedir=$(dirname "$0")
result=0

echo "Managing services for ${PROJECT_ID}..."

enabled="/tmp/${PROJECT_ID}.enabled"
specified="/tmp/${PROJECT_ID}.specified"
excluded="/tmp/${PROJECT_ID}.excluded"

echo "source.googleapis.com" > "${excluded}"
gcloud services list --enabled --format="value(NAME)" --project "${PROJECT_ID}" > "${enabled}"
python3 "${basedir}"/list_services.py "${PROJECT_ID}" "${SERVICE_CATALOG}" "${PROJECT_CATALOG}" > "${specified}"

disable=$(python3 "${basedir}"/compare_lists.py "${enabled}" "${specified}" "${excluded}")

for service in $disable
do
    echo " + disable ${service} in ${PROJECT_ID}"
    gcloud services disable "${service}" --project "${PROJECT_ID}" --force
done

enable=$(python3 "${basedir}"/compare_lists.py "${specified}" "${enabled}" "${excluded}")

for service in $enable
do
    echo " + enable ${service} in ${PROJECT_ID}"
    gcloud services enable "${service}" --project "${PROJECT_ID}"
done

result=$?

if [ $result -ne 0 ]
then
    echo "ERROR enabling/disabling services for ${PROJECT_ID}"
    exit $result
fi
