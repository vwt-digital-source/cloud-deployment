#!/bin/bash


PROJECT_ID=${1}
PARENT_ID=${2}
BILLING_ACCOUNT=${3}
LOGSINK_CATALOG=${4}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${PARENT_ID}" ]] || error_exit "Missing required PARENT_ID"
[[ -n "${BILLING_ACCOUNT}" ]] || error_exit "Missing required BILLING_ACCOUNT"
[[ -n "${LOGSINK_CATALOG}" ]] || error_exit "Missing required LOGSINK_CATALOG"

basedir=$(dirname "$0")

deployment_name="${PROJECT_ID}-logsinks-deploy"
gcp_template=$(mktemp "${deployment_name}-XXXXX.py")

{
    echo "logsinks = \\"
    cat "${LOGSINK_CATALOG}"
    cat "$basedir/create_logsinks.py"
} > "${gcp_template}"

# Check if deployment exists
exists=$(gcloud deployment-manager deployments list \
           --project="${PROJECT_ID}" \
           --format="value(name)" \
           --filter="name=${deployment_name}")

if [[ -z "${exists}" ]]
then
    # Create if deployment does not yet exist
    gcloud deployment-manager deployments create "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="parent_folder_id:${PARENT_ID},billing_account_name:${BILLING_ACCOUNT}" \
      --project="${PROJECT_ID}"
else
    # Update if deployment exists already
    gcloud deployment-manager deployments update "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="parent_folder_id:${PARENT_ID},billing_account_name:${BILLING_ACCOUNT}" \
      --project="${PROJECT_ID}" \
      --delete-policy=abandon
fi
