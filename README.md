[![CodeFactor](https://www.codefactor.io/repository/github/vwt-digital/cloud-deployment/badge)](https://www.codefactor.io/repository/github/vwt-digital/cloud-deployment)

# cloud-deployment

Automated deployment of projects, logsinks and service account key management to Google Cloud Platform implemented using Google _Cloud Build_, _Cloud Functions_ and _Deployment Manager_.

## Functionality

This repository contains GCP Cloud Builds, Deployment Manager and helper scripts to provision GCP projects from project catalogs specified in JSON (see [config/projects/](config/projects/) for example projects). The [project_cloudbuild.yaml](project_cloudbuild.yaml) generates the following GCP resources from this specification:
* GCP project
* IAM bindings
* Enabled APIs & services
* App Engines
* Cloud Build triggers from GitHub
* [Google KMS](https://cloud.google.com/kms/) keys and permissions

Next to GCP project resources, it can also setup logsinks and automated service account keys clean-up.

## Setup

It is advisable to run the cloud-deployment from a specific GCP project that is only used as a project to provision other projects, as the actions performed require elevated privileges. The next section describes the setup of these elevated privileges, followed by a section about customising the configuration.

All projects will be created in a specific GCP [folder](https://cloud.google.com/resource-manager/docs/creating-managing-folders), the projects-parent folder, which should be created upfront. The cloud-deployment project requires some Google Services, which can be enabled by executing this gcloud command:
~~~
gcloud services enable deploymentmanager.googleapis.com  \
                cloudresourcemanager.googleapis.com  \
                cloudbilling.googleapis.com \
                iam.googleapis.com \
                servicemanagement.googleapis.com \
                cloudbuild.googleapis.com \
                pubsub.googleapis.com \
                cloudfunctions.googleapis.com \
                appengine.googleapis.com
~~~

As both Cloud Build and Deployment Manager are used to perform the cloud-deployment, the respective service accounts require specific privileges. These should be granted on the projects-parent folder as specified in the following table.

Service account|Privilege to grant on projects-parent folder level
-----|-----
xxx@cloudbuild.gserviceaccount.com      | Cloud Build Editor, Owner
xxx@cloudservices.gserviceaccount.com   | Owner, Project Creator

### Setup config

Configuration is specified by variables in a env.sh file. By default the cloud-deployment repository contains an example configuration. The config files should be changed to describe the setup you want to deploy.

Variable         | Description
-----|-----
_AUDIT_LOGS | A comma delimited list of googleapis.com for which audit logging should be enabled.
_BILLING_ACCOUNT | The billing account name (billingAccounts/XXXXXX-XXXXXX-XXXXXX).
_PARENT_ID | The ID of the parent organization or folder.
_TOPIC_PROJECT_ID | Project that holds the topic to to which all cloud build status badges should be published.
_TOPIC_NAME | Topic to which all cloud build status badges should be published.
_GROUP | Group that holds all the development users.
_REGION | Region to which the default cloudbuild buckets should be deployed.

### Starting the cloud-deployment build deploying projects

Follow these steps to manually run the cloud-deployment:
1. Clone the cloud-deployment source repository
```git clone https://github.com/vwt-digital/cloud-deployment.git```
2. Change the config files as described in the previous section
3. Run the [projects/create_directory_triggers.sh](projects/create_directory_triggers.sh) script, which will create a build triggers for each of the project.json config files in the projects directory. These triggers will be connected to the specified repository in the specified github organization, triggering on the specified branch.
```
$ projects/create_directory_triggers.sh \
          ${PROJECT_ID} \
          config/projects \
          my-branch \
          my-github-organisation \
          my-github-repo
```

After the project deployment triggers are there, these will deploy the GCP resources as specified in the project.json config files. When chaning a configuration for a project, the project's trigger will update the existing resources to match the new configuration. However, any resources that are removed from the configuration will not be deleted, but only abandoned from the deployment.

### Starting the cloud-deployment build deploying logsinks

Deployment of logsinks can be done by running the logsinks_cloudbuild.yaml, after changing the logsinks specification in [config/logsinks/logsinks.json](config/logsinks/logsinks.json).
```
$ cd cloud-deployment
$ gcloud builds submit . --config=logsinks_cloudbuild.yaml
```

### Starting the cloud-deployment build for service account key clean-up

Automatically revoking service account keys after a specific period of time can be scheduled by running the jobs_cloudbuild.yaml. The expiration period of keys can be specified in [config/jobs/env.sh](config/jobs/env.sh).
The revoke job can be scheduled by running the cloudbuild:
```
$ cd cloud-deployment
$ gcloud builds submit . --config=jobs_cloudbuild.yaml
```

## Acknowledgements

The GCP project creation and setup is implemented according to techniques described in [Automating project creation with Google Cloud Deployment Manager](
https://cloud.google.com/blog/products/gcp/automating-project-creation-with-google-cloud-deployment-manager) and implemented in the Deployment Manager [example](https://github.com/GoogleCloudPlatform/deploymentmanager-samples/tree/master/examples/v2/project_creation)
The odrlPolicy structure, used to specify permissions on projects and keyrings, is based on the [Open Digital Rights Language (ODRL)](https://www.w3.org/TR/odrl/).
