#!/bin/bash

PROJECT_ID=${1}
REPO_NAME=${2}
BRANCH_NAME=${3}

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
                          AND filename=cloudbuild.yaml")

if [[ -z "${trigger_id}" ]]
then
    gcloud beta builds triggers run "$trigger_id" \
      --branch="${BRANCH_NAME}" \
      --project="${PROJECT_ID}"
fi
