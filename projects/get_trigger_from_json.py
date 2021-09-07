import argparse
import json


def get_trigger(repo_name, branch_name, file_name, trigger_list_json):
    for trigger in trigger_list_json:
        github = trigger.get("github")
        if github:
            github_name = github.get("name")
            github_push = github.get("push")
            if github_push:
                github_push_branch = github_push.get("branch")
        filename = trigger.get("filename")
        if (
            filename == file_name
            and github
            and github_name == repo_name
            and github_push_branch == branch_name
        ):
            return trigger.get("id")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-name", required=True)
    parser.add_argument("-b", "--branch-name", required=True)
    parser.add_argument("-f", "--file-name", required=True)
    parser.add_argument("-t", "--trigger-list", required=True)
    args = parser.parse_args()
    repo_name = args.repo_name
    branch_name = args.branch_name
    file_name = args.file_name
    trigger_list = args.trigger_list
    trigger_list_json = json.loads(trigger_list)
    print(get_trigger(repo_name, branch_name, file_name, trigger_list_json))
