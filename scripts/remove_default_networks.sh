#!/bin/bash
# shellcheck disable=SC2181,SC1091

PROJECT_CATALOG=${1}
PARENT_ID=${2}

basedir=$(dirname "$0")
result=0

for project in $(gcloud projects list --format="value(PROJECT_ID)" --filter="parent.id=${PARENT_ID}")
do

    # Check if default network should be deleted
    default_network=$(python3 "${basedir}"/has_default_network.py "${project}" "${PROJECT_CATALOG}")
    if [[ "${default_network}" == "false" ]]
    then

        # Enable compute.googleapis.com if disabled
        compute=$(gcloud services list --enabled --format="value(NAME)" --project "${project}" | grep compute.googleapis.com)
        if [[ -z "${compute}" ]]
        then
            gcloud services enable compute.googleapis.com --project "${project}"
        fi

        if [[ -n $(gcloud compute networks list --project "${project}" --filter="name=default" --format="value(NAME)") ]]
        then

            echo "Removing default network for ${project}..."

            # Remove default firewall rules
            for fw in $(gcloud compute firewall-rules list --filter="network=default" --format="value(NAME)" --project "${project}")
            do
                gcloud compute firewall-rules delete "${fw}" --project "${project}" --quiet
                echo " + removed default firewall rule ${fw}"
            done

            # Remove default network
            gcloud compute networks delete default --project "${project}" --quiet
            echo " + removed default network"

        fi

        # Disable compute.googleapis.com
        if [[ -z "${compute}" ]]
        then
            gcloud services disable compute.googleapis.com --project "${project}"
        fi

        if [ $? -ne 0 ]
        then
            echo "ERROR removing default network for ${project}"
            result=1
        fi

    fi

done

if [ ${result} -ne 0 ]
then
    echo "At least one error occurred during removing default networks"
    exit 1
fi
