#!/bin/bash

projects_catalog=${1}
services=${2}
service_accounts=${3}
iam_bindings=${4}

if [ -z "${iam_bindings}" ]
then
    echo "Usage: $0 <projects_catalog> <default-services> <default-service-accounts> <default-iam-bindings>"
    exit 1
fi

tmpscript=$(mktemp /tmp/XXXXXXX.py)


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
    cat << EOF
import json


class Context:
    def __init__(self):
        self.properties = {'billing_account_name': 'billingAccount',
                           'parent_folder_id': '0',
                           'region': 'europe-west1'}

print(json.dumps(generate_config(Context())))
EOF
} > "${tmpscript}"

python3 "${tmpscript}"
rm "${tmpscript}"
