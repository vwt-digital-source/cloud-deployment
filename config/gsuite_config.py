USER_IMPERSONATION_EMAIL = "user@example.com"
SERVICE_ACCOUNT = "user@project.iam.gserviceaccount.com"
SERVICE_ACCOUNT_SCOPES = [
  "https://www.googleapis.com/auth/admin.directory.group",
  "https://www.googleapis.com/auth/cloud-platform"
]
GSUITE_GROUPS = [
  {
    "email": "cloudbuilders-group@example",
    "name": "Cloud build group",
    "description": "All GCP cloud build accounts",
    "members": "cloudbuild"
  },
  {
    "email": "group-appengines@example.com",
    "name": "App engine group",
    "description": "All GCP app engine accounts",
    "members": "appspot"
  }
]
