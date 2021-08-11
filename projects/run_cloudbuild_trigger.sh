#!/bin/bash

PROJECT_ID=${1}
REPO_NAME=${2}
BRANCH_NAME=${3}
FILE_NAME='cloudbuild.yaml'

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${REPO_NAME}" ]] || error_exit "Missing required REPO_NAME"
[[ -n "${BRANCH_NAME}" ]] || error_exit "Missing required BRANCH_NAME"


trigger_id=$(gcloud beta builds triggers list \
                --project="${PROJECT_ID}" \
                --format="value(ID)" \
                --filter="github.name=${REPO_NAME} \
                          AND github.push.branch=${BRANCH_NAME} \
                          AND filename=${FILE_NAME}")

if [[ -n "${trigger_id}" ]]
then
    gcloud beta builds triggers run "$trigger_id" \
      --branch="${BRANCH_NAME}" \
      --project="${PROJECT_ID}"
else
  trigger_ids=$(gcloud beta builds triggers list --format="json")
  trigger_id_via_python=$(python3 ./get_trigger_from_json.py -r "${REPO_NAME}" -b "${BRANCH_NAME}" -t "${trigger_ids}" -f "${FILE_NAME}")
  if [[ -z "${trigger_id_via_python}" ]]
  then
      echo "ERROR getting trigger."
      exit 1
  fi
  gcloud beta builds triggers run "${trigger_id_via_python}" \
    --branch="${BRANCH_NAME}" \
    --project="${PROJECT_ID}"
fi
