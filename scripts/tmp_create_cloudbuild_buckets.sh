#!/bin/bash
# shellcheck disable=SC2181

PROJECT_ID=${1}
REGION=${2}
GROUP=${3}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${REGION}" ]] || error_exit "Missing required REGION"
[[ -n "${GROUP}" ]] || error_exit "Missing required GROUP"


cat << EOF > lifecycle.json
{ "rule": [ { "action": { "type": "Delete" }, "condition": { "age": 180 } } ] }
EOF

echo "Check if cloudbuild bucket exists for project ${PROJECT_ID}..."

gsutil ls -b -p "${PROJECT_ID}" "gs://${PROJECT_ID}_cloudbuild" >/dev/null 2>&1

if [ $? -ne 0 ]
then

    echo " + Creating cloudbuild bucket"
    gsutil mb -c standard -p "${PROJECT_ID}" -l "${REGION}" -b on "gs://${PROJECT_ID}_cloudbuild"

    if [ $? -ne 0 ]
    then
        echo "ERROR creating default cloudbuild bucket for ${PROJECT_ID}"
        exit 1
    fi

else

    echo " + Cloud cloudbuild already exists"

fi

echo "Set lifecycle on cloudbuild bucket..."

gsutil lifecycle set lifecycle.json "gs://${PROJECT_ID}_cloudbuild"

echo "Set permissions on cloudbuild bucket..."

gsutil iam ch "group:${GROUP}:roles/storage.legacyObjectReader" "gs://${PROJECT_ID}_cloudbuild"
gsutil iam ch "group:${GROUP}:roles/storage.legacyBucketReader" "gs://${PROJECT_ID}_cloudbuild"
