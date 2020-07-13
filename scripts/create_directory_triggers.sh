#!/bin/bash

PROJECT_ID=${1}
DIRECTORY=${2}
BRANCH_NAME=${3}
REPO_OWNER=${4}
REPO_NAME=${5}

function error_exit() {
  # ${BASH_SOURCE[1]} is the file name of the caller.
  echo "${BASH_SOURCE[1]}: line ${BASH_LINENO[0]}: ${1:-Unknown Error.} (exit ${2:-1})" 1>&2
  exit "${2:-1}"
}

[[ -n "${PROJECT_ID}" ]] || error_exit "Missing required PROJECT_ID"
[[ -n "${DIRECTORY}" ]] || error_exit "Missing required DIRECTORY"
[[ -n "${BRANCH_NAME}" ]] || error_exit "Missing required BRANCH_NAME"
[[ -n "${REPO_OWNER}" ]] || error_exit "Missing required REPO_OWNER"
[[ -n "${REPO_NAME}" ]] || error_exit "Missing required REPO_NAME"


basedir=$(dirname "$0")

echo "Getting directories..."
touch "$basedir/directories.txt"
projects=$(ls "${DIRECTORY}")

for project in ${projects}
do
    printf "%s\n" "${project}" >> "$basedir/directories.txt"
done

echo "Getting triggers..."
touch "$basedir/triggers.txt"
triggers=$(gcloud beta builds triggers list --project="${PROJECT_ID}" --format="value(name)" --filter="name:Create-*-trigger" --quiet)
for trigger in ${triggers}
do
    echo "${trigger%-trigger}" | cut -d '-' -f3- >> "$basedir/triggers.txt"
done

to_create=$(ruby -e "puts File.readlines('$basedir/directories.txt') - File.readlines('$basedir/triggers.txt')")
to_delete=$(ruby -e "puts File.readlines('$basedir/triggers.txt') - File.readlines('$basedir/directories.txt')")

for project in ${to_create}
do
    echo "Creating new trigger for ${project}..."
    gcloud beta builds triggers create github \
      --repo-name="${REPO_NAME}" \
      --repo-owner="${REPO_OWNER}" \
      --description="Create project ${project} trigger" \
      --included-files="config/${PROJECT_ID}/projects" \
      --project="${PROJECT_ID}" \
      --build-config="cloudbuild.yaml" \
      --branch-pattern="${BRANCH_NAME}"
    gcloud beta builds triggers run "Create-project-${project}-trigger" \
      --branch="${BRANCH_NAME}" \
      --project="${PROJECT_ID}"
done

for project in ${to_delete}
do
    echo "Deleting trigger for ${project}..."
    gcloud beta builds triggers delete "Create-project-${project}-trigger" \
      --project="${PROJECT_ID}" \
      --quiet
done
