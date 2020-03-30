#!/bin/sh

PROJECT_ID=${1}

if [ -z "${PROJECT_ID}" ]
then
    echo "PROJECT_ID parameter should be set to deployment manager project"
    echo "Usage: ${0} <project_id>"
    exit 1
fi

deployment_name="${PROJECT_ID}-projects-deploy"
project_catalog="../config/projects.json"
billing_account_name=$(cat ../config/billing_account_name.cfg)
parent_folder_id=$(cat ../config/parent_folder_id.cfg)

gcp_template=$(mktemp "${deployment_name}-XXXXX.py")

{
    echo "projects = \\"
    cat ${project_catalog}
    cat create_projects.py
} > "${gcp_template}"

# Check if deployment exists
gcloud deployment-manager deployments describe "${deployment_name}" --project="${PROJECT_ID}" >/dev/null 2>&1
result=$?

if [ ${result} -ne 0 ]
then
    # Create if deployment does not yet exist
    gcloud deployment-manager deployments create "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="parent_folder_id:${parent_folder_id},billing_account_name:${billing_account_name}" \
      --project="${PROJECT_ID}"
else
    # Update if deployment exists already
    gcloud deployment-manager deployments update "${deployment_name}" \
      --template="${gcp_template}" \
      --properties="parent_folder_id:${parent_folder_id},billing_account_name:${billing_account_name}" \
      --project="${PROJECT_ID}" \
      --delete-policy=abandon
fi

# Disable services that are not specified in projects.json
for project in $(gcloud projects list --format="value(PROJECT_ID)" --filter="parent.id=${parent_folder_id}")
do
    enabled="/tmp/${project}.enabled"
    specified="/tmp/${project}.specified"
    gcloud services list --enabled --format="value(NAME)" --project "${project}" > "${enabled}"
    python3 ./list_services.py "${project}" "${project_catalog}" > "${specified}"
    disable=$(comm -23 <(sort "${enabled}") <(sort "${specified}"))

    for service in ${disable}
    do
        gcloud services disable "${service}" --project "${project}"
    done
done
