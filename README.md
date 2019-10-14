[![CodeFactor](https://www.codefactor.io/repository/github/vwt-digital/cloud-deployment/badge)](https://www.codefactor.io/repository/github/vwt-digital/cloud-deployment)

# cloud-deployment

Automated deployment of projects and build status badges to Google Cloud Platform, also managing GitHub branch protection rules, implemented using Google _Cloud Build_ and _Deployment Manager_.

## Functionality

This repository contains GCP Cloud Build, Deployment Manager and helper scripts to provision GCP projects from a project catalog specified in JSON (see [config/projects.json](config/projects.json) for an example). The [cloudbuild.yaml](cloudbuild.yaml) generates the following GCP resources from this specification:
* GCP project and additional IAM bindings if specified in odrlPolicy
* Linked billing account (specified in [config/billing_account_name.cfg](config/billing_account_name.cfg))
* Enabled services (GCP APIs)
* App Engine (if App Engine API service is enabled and appEngineRegion specified in [projects.json](config/projects.json))
* Cloud Build triggers (the actual Source Repository connection to be manually created)
* [Google KMS](https://cloud.google.com/kms/) Keyrings, keys and IAM on the keyring

Next to GCP resources, it will also report build status to GitHub through the [GitHub Statuses API](https://developer.github.com/v3/repos/statuses/), and create a storage bucket containing status badges images for all builds triggered from a source repository, which will contain one of the following images, matching the status of the latest build:
* [Image of successful build](functions/create_build_badge_func/badge-passing.png)
* [Image of failing build](functions/create_build_badge_func/badge-failing.png)
* [Image of running build](functions/create_build_badge_func/badge-pending.png)

The status badges are updated by Cloud Functions, passing the build result Pub/Sub messages of each project on to the project running the cloud-deployment.

The cloud-deployment build will also set branch protection rules on all github repositories that are specified in the [data catalog](config/data_catalog.json). The rules that will be set are specified in [scripts/set_github_restrictions.json](scripts/set_github_restrictions.json). The GitHub API is used to set the branch protection rules.

## Setup

It is advisable to run the cloud-deployment from a specific GCP project that is only used for cloud-deployment, as the functions performed require elevated privileges. The next section describes the setup of these elevated privileges, followed by a section about customizing the configuration.

### Setup credentials

All projects will be created in a specific GCP [folder](https://cloud.google.com/resource-manager/docs/creating-managing-folders), the projects-parent folder, which should be created upfront.

The cloud-deployment project requires some Google Services, which can be enabled by executing this gcloud command:
~~~
gcloud services enable deploymentmanager.googleapis.com  \
                cloudresourcemanager.googleapis.com  \
                cloudbilling.googleapis.com \
                iam.googleapis.com \
                servicemanagement.googleapis.com \
                cloudbuild.googleapis.com \
                pubsub.googleapis.com \
                cloudfunctions.googleapis.com \
                sourcerepo.googleapis.com \
                appengine.googleapis.com
~~~

As both Cloud Build and Deployment Manager are used to perform the cloud-deployment, the respective service accounts require specific privileges. These should be granted on the projects-parent folder as specified in the following table.

Service account|Privilege to grant on projects-parent folder level
-----|-----
xxx@cloudbuild.gserviceaccount.com      | Cloud Build Editor, Owner
xxx@cloudservices.gserviceaccount.com   | Owner, Project Creator

### Setup config

Configuration is specified in the files in the config directory. By default the cloud-deployment repository contains an example configuration. The config files should be changed to describe the setup you want to deploy.

Config file         | Contents
-----|-----
[billing_account_name.cfg](config/billing_account_name.cfg) | Specifies billing account to link to the created projects
[create_build_badge_func.config.sh](config/create_build_badge_func.config.sh) | Specifies region, deployment status bucket and deployment status topic for build status badges
[data_catalog.json](config/data_catalog.json) | Specifies storage and topic to create for build status badges and github repositories to set branch protection rules for. See [Project Company Data](https://vwt-digital.github.io/project-company-data.github.io/) for more information on the data catalog format.
[github_access_token.enc](config/github_access_token.enc) | [Encoded](https://cloud.google.com/cloud-build/docs/securing-builds/use-encrypted-secrets-credentials) github access token, keyring to be manually created in the project (keyring=github, key=github-access-token), can also be done from the projects.json, but that makes encryption of the secret before deployment impossible.
[parent_folder_id.cfg](config/parent_folder_id.cfg) | The id of the projects-parent folder
[projects.json](config/projects.json)  | Specifies projects to create, services to enable and Cloud Build triggers to create
[publish_build_result_func.config.sh](config/publish_build_result_func.config.sh) | Specifies region, cloud-deployment project and topic name for build status badges

### Submit the cloud-deployment build

Follow these steps to manually run the cloud-deployment:
1. Clone the cloud-deployment source repository
```git clone https://github.com/vwt-digital/cloud-deployment.git```
2. Change the config files as described in the previous section
3. Submit the cloud-deployment build from the root of cloud-deployment repository clone
```gcloud builds submit .```

This will deploy all you specified in the configuration files. When re-running with a different configuration, the existing resources will be updated to match the new configuration. However, any resources that are removed from the configuration will not be deleted, but only abandoned from the deployment.

## Acknowledgements

The GCP project creation and setup is implemented according to techniques described in [Automating project creation with Google Cloud Deployment Manager](
https://cloud.google.com/blog/products/gcp/automating-project-creation-with-google-cloud-deployment-manager) and implemented in the Deployment Manager [example](https://github.com/GoogleCloudPlatform/deploymentmanager-samples/tree/master/examples/v2/project_creation)
The odrlPolicy structure, used to specify permissions on projects and keyrings, is based on the [Open Digital Rights Language (ODRL)](https://www.w3.org/TR/odrl/).

## Next steps

One of the next steps is to make sure the Service Account from the created Error Logging Sink (production and development folder level) has publish rights on the ODH Error Reporting topic.
