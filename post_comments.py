import json
import os
from github_utils import get_pr_semgrep_comments, create_semgrep_comments, reply_to_pr_comment, update_status_in_comment
from slack_utils import submit_slack_notification

# Load the findings from the JSON file
with open('findings.json', 'r') as f:
    findings = json.load(f)

# Get the needed context from the env variables
pr_number = os.environ['GITHUB_REF'].split('/')[2]
owner = os.environ['GITHUB_REPOSITORY_OWNER']
repo = os.environ['GITHUB_REPOSITORY'].split('/')[1]
token = os.environ["GITHUB_TOKEN"]
latest_commit = os.environ["LATEST_COMMIT"]
slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"

# get existing semgrep comments and fingerprints
existing_fingerprints = get_pr_semgrep_comments(owner,repo,pr_number,token)
print("---------------------------------------")
print("EXISTING:")
print(existing_fingerprints.keys())
print("---------------------------------------")

# Iterate over the findings and post a comment for each new one
for finding in findings['results']:
    new_fingerprint = finding['extra']['fingerprint']
    if new_fingerprint not in existing_fingerprints.keys():
        create_semgrep_comments(owner,repo,pr_number,token,latest_commit,finding)
        submit_slack_notification(slack_webhook_url,finding,pr_number,pr_url,"open")
        print(finding)
    if new_fingerprint in existing_fingerprints.keys() and existing_fingerprints[new_fingerprint]["status"] == "resolved":
        comment_id = existing_fingerprints[new_fingerprint]["id"]
        comment_body = existing_fingerprints[new_fingerprint]["body"]
        update_status_in_comment(owner,repo,comment_id,token,comment_body,"open")
        reply_to_pr_comment(owner,repo,pr_number,token,comment_id,latest_commit,"reopen")
        submit_slack_notification(slack_webhook_url,finding,pr_number,pr_url,"reopen")

# Get list of the new semgrep finding fingerprints        
new_fingerprints = [finding['extra']['fingerprint'] for finding in findings['results']]
print("---------------------------------------")
print("NEW:")
print(new_fingerprints)
print("---------------------------------------")

# Get the list of existing semgrep finding fingerprints that have been resolved
resolved_fingerprints = [fingerprint for fingerprint in existing_fingerprints.keys() if fingerprint not in new_fingerprints and
                          existing_fingerprints[fingerprint]["status"] != "resolved"]
print("---------------------------------------")
print("RESOLVED:")
print(resolved_fingerprints)
print("---------------------------------------")

# Add comment to resolved findings
for fingerprint in resolved_fingerprints:
    comment_id = existing_fingerprints[fingerprint]["id"]
    comment_body = existing_fingerprints[fingerprint]["body"]
    reply_to_pr_comment(owner,repo,pr_number,token,comment_id,latest_commit)
    update_status_in_comment(owner,repo,comment_id,token,comment_body,"resolved")
    submit_slack_notification(slack_webhook_url,comment_body,pr_number,pr_url,"resolved")
    print(existing_fingerprints[fingerprint]["id"])

