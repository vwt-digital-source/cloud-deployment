#!/bin/bash
# shellcheck disable=SC2181,SC2030,SC2031,SC2086,SC2016

PROJECT_ID=${1}
PROJECT_CATALOG=${2}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${PROJECT_CATALOG}" ]] || error_exit "Missing required PROJECT_CATALOG"

basedir=$(dirname "$0")
result=0

echo "Creating firewall rules for ${PROJECT_ID}..."

python3 "${basedir}"/firewall_rules_setup.py "${PROJECT_CATALOG}" |
  while read -r -a rule; do
    rule_name=$(gcloud compute firewall-rules list \
      --filter="name=${rule[0]}" \
      --project="${PROJECT_ID}" \
      --format="value(NAME)")

    if [ -n "${rule_name}" ]; then
      echo " - Delete firewall rule ${rule_name}"
      gcloud compute firewall-rules delete "${rule_name}" --project="${PROJECT_ID}" --quiet
    fi

    echo "+ Create firewall rule ${rule[0]} for project ${PROJECT_ID}..."

    gcloud compute --project="${PROJECT_ID}" firewall-rules create ${rule[3]} \
      --direction=${rule[2]} \
      --${rule[0]} ${rule[6]} \
      --description=${rule[1]} \
      --network=${rule[4]} \
      --priority=${rule[5]} \
      --source-ranges=${rule[7]}
    result=$?

    if [ ${result} -ne 0 ]; then
      echo "ERROR creating firewall rule ${rule[0]} in project ${PROJECT_ID}"
    fi
    exit $result

  done
