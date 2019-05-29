#!/bin/bash

projects_catalog=${1}

if [ -z "${projects_catalog}" ]
then
    echo "Usage: $0 <projects_catalog>"
    exit 1
fi

tmpscript=$(mktemp /tmp/XXXXXXX.py)

{
    echo "projects = \\"
    cat ${projects_catalog}
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
} > ${tmpscript}

python3 ${tmpscript}
rm ${tmpscript}
