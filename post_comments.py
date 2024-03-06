import json
import os
from github_utils import get_pr_semgrep_comments, create_semgrep_comments, reply_to_pr_comment

# Load the findings from the JSON file
with open('findings.json', 'r') as f:
    findings = json.load(f)

# Get the needed context from the env variables
pr_number = os.environ['GITHUB_REF'].split('/')[2]
owner = os.environ['GITHUB_REPOSITORY_OWNER']
repo = os.environ['GITHUB_REPOSITORY'].split('/')[1]
token = os.environ["GITHUB_TOKEN"]
latest_commit = os.environ["LATEST_COMMIT"]

# get existing semgrep comments and fingerprints
existing_fingerprints = get_pr_semgrep_comments(owner,repo,pr_number,token)
print("---------------------------------------")
print("EXISTING:")
print(existing_fingerprints.keys())
print("---------------------------------------")

# Iterate over the findings and post a comment for each new one
for finding in findings['results']:
    if finding['extra']['fingerprint'] not in existing_fingerprints.keys():
        create_semgrep_comments(owner,repo,pr_number,token,latest_commit,finding)
        print(finding)

# Get list of the new semgrep finding fingerprints        
new_fingerprints = [finding['extra']['fingerprint'] for finding in findings['results']]
print("---------------------------------------")
print("NEW:")
print(new_fingerprints)
print("---------------------------------------")

# Get the list of existing semgrep finding fingerprints that have been resolved
resolved_fingerprints = [fingerprint for fingerprint in existing_fingerprints.keys() if fingerprint not in new_fingerprints]
print("---------------------------------------")
print("RESOLVED:")
print(resolved_fingerprints)
print("---------------------------------------")

# Add comment to resolved findings
for fingerprint in resolved_fingerprints:
    comment_id = existing_fingerprints[fingerprint]["id"]
    reply_to_pr_comment(owner,repo,pr_number,token,comment_id,latest_commit)
    print(existing_fingerprints[fingerprint]["id"])

