#!/bin/bash
# shellcheck disable=SC2086

PROJECT_ID=${1}
BRANCH_NAME=${2}
PARENT_ID=${3}
EXPIRATION_PERIOD_DAYS=${4}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit ${2:-1}
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${BRANCH_NAME}" ]] || error_exit "Missing required BRANCH_NAME"
[[ -n "${PARENT_ID}" ]] || error_exit "Missing required PARENT_ID"
[[ -n "${EXPIRATION_PERIOD_DAYS}" ]] || error_exit "Missing required EXPIRATION_PERIOD_DAYS"

basedir=$(dirname "$0")

echo "Scheduling job to revoke service account keys..."

gsed "${basedir}/cloudbuild_revoke_sa_keys.json" \
    -e "s|__BRANCH_NAME__|${BRANCH_NAME}|" \
    -e "s|__EXPIRATION_PERIOD_DAYS__|${EXPIRATION_PERIOD_DAYS}|" \
    -e "s|__PARENT_ID__|${PARENT_ID}|" > cloudbuild_revoke_sa_keys_gen.json

echo " + Check if job ${PROJECT_ID}-revoke-sa-keys-job exists..."
job_exists=$(gcloud scheduler jobs list --project="${PROJECT_ID}" | grep "${PROJECT_ID}-revoke-sa-keys-job")

if [[ -n "${job_exists}" ]]
then
    echo " + Deleting existing job ${PROJECT_ID}-revoke-sa-keys-job..."
    gcloud scheduler jobs delete "${PROJECT_ID}-revoke-sa-keys-job" \
      --project="${PROJECT_ID}" --quiet
fi

echo " + Creating job ${PROJECT_ID}-revoke-sa-keys-job..."
gcloud scheduler jobs create http "${PROJECT_ID}-revoke-sa-keys-job" \
  --schedule="0 0 * * *" \
  --project="${PROJECT_ID}" \
  --uri="https://cloudbuild.googleapis.com/v1/projects/${PROJECT_ID}/builds" \
  --message-body-from-file=cloudbuild_revoke_sa_keys_gen.json \
  --oauth-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
  --oauth-token-scope=https://www.googleapis.com/auth/cloud-platform
