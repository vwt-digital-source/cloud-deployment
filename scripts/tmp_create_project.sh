#!/bin/bash

PROJECT_ID=${1}
DEST_PROJECT=${2}
COMMON_CONFIG=${3}
BILLING_ACCOUNT=${4}
PARENT_ID=${5}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${DEST_PROJECT}" ]] || error_exit "Missing required DEST_PROJECT"
[[ -n "${COMMON_CONFIG}" ]] || error_exit "Missing required COMMON_CONFIG"
[[ -n "${BILLING_ACCOUNT}" ]] || error_exit "Missing required BILLING_ACCOUNT"
[[ -n "${PARENT_ID}" ]] || error_exit "Missing required PARENT_ID"

project_catalog="${COMMON_CONFIG}/projects/${DEST_PROJECT}/project.json"
services="${COMMON_CONFIG}/services.json"
iam_bindings="${COMMON_CONFIG}/iam_bindings.json"
service_accounts="${COMMON_CONFIG}/service_accounts.json"
deployment_name="${DEST_PROJECT}-project-deploy"
gcp_template=$(mktemp "${deployment_name}-XXXXX.py")

{
    echo "projects = \\"
    cat "${project_catalog}"
    echo "services = \\"
    cat "${services}"
    echo "service_accounts = \\"
    cat "${service_accounts}"
    echo "iam_bindings = \\"
    cat "${iam_bindings}"
    cat tmp_create_projects.py
} > "${gcp_template}"

# Check if deployment exists
gcloud deployment-manager deployments describe "${deployment_name}" --project="${PROJECT_ID}" >/dev/null 2>&1
result=$?

if [ ${result} -ne 0 ]
then
    # Create if deployment does not yet exist
    gcloud deployment-manager deployments create "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="PARENT_ID:${PARENT_ID},BILLING_ACCOUNT:${BILLING_ACCOUNT}" \
      --project="${PROJECT_ID}"
else
    # Update if deployment exists already
    gcloud deployment-manager deployments update "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="PARENT_ID:${PARENT_ID},BILLING_ACCOUNT:${BILLING_ACCOUNT}" \
      --project="${PROJECT_ID}" \
      --delete-policy=abandon
fi
