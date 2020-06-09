#!/bin/bash

projects_catalog=${1}
services=${2}
service_accounts=${3}
iam_bindings=${4}
parent_folder_id=${5}
billing_account_name=${6}

if [ -z "${projects_catalog}" ] || [ -z "${services}" ] || [ -z "${service_accounts}" ] || [ -z "${parent_folder_id}" ] || [ -z "${billing_account_name}" ]
then
    echo "Usage: $0 <projects_catalog> <services> <service_accounts>"
    exit 1
fi

test_template=$(mktemp "/tmp/$(uuidgen).py")

{
    echo "projects = \\"
    cat "${projects_catalog}"
    echo "services = \\"
    cat "${services}"
    echo "service_accounts = \\"
    cat "${service_accounts}"
    echo "iam_bindings = \\"
    cat "${iam_bindings}"
    cat create_projects.py
} > "${test_template}"

echo "------------------------------------------------------------------------------------------"
cat "${test_template}"
echo "------------------------------------------------------------------------------------------"

gcloud deployment-manager deployments create test-deployment \
  --properties="parent_folder_id:${parent_folder_id},billing_account_name:${billing_account_name}" \
  --project=vwt-d-gew1-ith-dashboard \
  --template "${test_template}" \
  --preview
