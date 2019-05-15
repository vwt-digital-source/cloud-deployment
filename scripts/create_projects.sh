#!/bin/sh

deployment_name="${PROJECT_ID}-projects-deploy"
project_catalog="../config/projects.json"
billing_account_name=$(cat ../config/billing_account_name.cfg)
parent_folder_id=$(cat ../config/parent_folder_id.cfg)

if [ -z "${PROJECT_ID}" ]
then
    echo "PROJECT_ID should be set to deployment manager project"
    exit 1
fi


gcp_template=$(mktemp ${deployment_name}-XXXXX.py)

{
    echo "projects = \\"
    cat ${project_catalog}
    cat create_projects.py
} > ${gcp_template}

# Check if deployment exists
gcloud deployment-manager deployments describe ${deployment_name} --project=${PROJECT_ID} >/dev/null 2>&1
result=$?

if [ ${result} -ne 0 ]
then
    # Create if deployment does not yet exist
    gcloud deployment-manager deployments create ${deployment_name} --template=${gcp_template} --properties="parent_folder_id:${parent_folder_id},billing_account_name:${billing_account_name}" --project=${PROJECT_ID}
else
    # Update if deployment exists already
    gcloud deployment-manager deployments update ${deployment_name} --template=${gcp_template} --properties="parent_folder_id:${parent_folder_id},billing_account_name:${billing_account_name}" --project=${PROJECT_ID}
fi

