import json
import os
import requests
from urllib.parse import quote
import re



# Load the findings from the JSON file
with open('findings.json', 'r') as f:
    findings = json.load(f)

# Parse the repository and pull request number from the GITHUB_REF environment variable
pr_number = os.environ['GITHUB_REF'].split('/')[2]
owner = os.environ['GITHUB_REPOSITORY_OWNER']
repo = os.environ['GITHUB_REPOSITORY'].split('/')[1]
token = os.environ["GITHUB_TOKEN"] 


def get_pr_semgrep_comments():

    fingerprints = []

    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments'

    # Set the required headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    # Send a GET request to retrieve the comments
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Extract the comments from the response
        comments = response.json()

        pattern = r'^<!--\s*semgrep_finding_fingerprint:\s*(.+)\s+-->$'
        for comment in comments:
            first_line = comment['body'].splitlines()[0]
            match = re.search(pattern, first_line)
            if match:
                fingerprints.append(match.group(1))

    return fingerprints

    



# Set up the headers for the GitHub API request
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json',
}

# The latest commit is the first item in the list
latest_commit = os.environ["LATEST_COMMIT"]

# fingerprints
existing_fingerprints = get_pr_semgrep_comments()
print(existing_fingerprints)

# Iterate over the findings and post a comment for each one
for finding in findings['results']:
    if finding['extra']['fingerprint'] not in existing_fingerprints:
        print(finding['extra']['fingerprint'])
        body = f'''<!-- semgrep_finding_fingerprint: {finding['extra']['fingerprint']} -->
## <img src="https://semgrep.dev/docs/img/semgrep.svg" width="30" height="30"> Semgrep finding
* **Rule ID:** {finding['check_id']}
* **File:** {finding['path']}
* **Line:** {finding['start']['line']}
* **Description:** {finding['extra']['message']}
* **Impact:** {finding['extra']['metadata']['impact']}
* **Confidence:** {finding['extra']['metadata']['confidence']}
* **Semgrep Rule:** [Link](https://semgrep.dev/r/{quote(finding['check_id'])})
'''

        payload = {
            'body': body,
            'commit_id': latest_commit,
            'path': finding['path'],
            'line': finding['start']['line'],
        }

        response = requests.post(
            f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments',
            headers=headers,
            json=payload,
        )

        if response.status_code != 201:
            raise Exception(f'Failed to post comment: {response.content}')

