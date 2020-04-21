#!/bin/bash

PROJECT_ID=${1}
BRANCH_NAME=${2}
PARENT_ID=${3}
EXPIRATION_PERIOD_DAYS=${4}

if [[ -z "${PROJECT_ID}" || -z "${BRANCH_NAME}" || -z "${PARENT_ID}" || -z "${EXPIRATION_PERIOD_DAYS}" ]]
then
    echo "PROJECT_ID parameter should be set"
    echo "BRANCH_NAME parameter should be set"
    echo "PARENT_ID parameter should be set"
    echo "EXPIRATION_PERIOD_DAYS parameter should be set"
    echo "Usage: ${0} <project_id> <branch_name> <parent_id> <EXPIRATION_PERIOD_DAYS>"
    exit 1
fi

basedir=$(dirname "$0")

echo "Scheduling job to revoke service account keys..."

sed "${basedir}/cloudbuild_revoke_sa_keys.json" \
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
