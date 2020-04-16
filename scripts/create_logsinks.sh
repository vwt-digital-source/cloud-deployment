#!/bin/bash

PROJECT_ID=${1}
PARENT_ID=${2}
BILLING_ACCOUNT=${3}
LOGSINK_CATALOG=${4}

if [[ -z "${PROJECT_ID}" || -z "${PARENT_ID}" || -z "${BILLING_ACCOUNT}" || -z "${LOGSINK_CATALOG}" ]]
then
    echo "PROJECT_ID parameter should be set to deployment manager project"
    echo "PARENT_ID parameter should be set to the parent folder/organization id"
    echo "BILLING ACCOUNT parameter should be set to: billingAccounts/xxxxxx-xxxxxx-xxxxx"
    echo "LOGSINK_CATALOG parameter should be set to the file containing the logsinks"
    echo "Usage: ${0} <project_id> <parent_id> <billing_account> <logsink_catalog>"
    exit 1
fi

deployment_name="${PROJECT_ID}-logsinks-deploy"
gcp_template=$(mktemp "${deployment_name}-tmp.py")

{
    echo "logsinks = \\"
    cat ${LOGSINK_CATALOG}
    cat create_logsinks.py
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
