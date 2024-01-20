import json
import os
import requests
from urllib.parse import quote

# Load the findings from the JSON file
with open('findings.json', 'r') as f:
    findings = json.load(f)

# Parse the repository and pull request number from the GITHUB_REF environment variable
pr_number = os.environ['GITHUB_REF'].split('/')[2]
owner = os.environ['GITHUB_REPOSITORY_OWNER']
repo = os.environ['GITHUB_REPOSITORY'].split('/')[1]

# Set up the headers for the GitHub API request
headers = {
    'Authorization': f'token {os.environ["GITHUB_TOKEN"]}',
    'Accept': 'application/vnd.github.v3+json',
}

# Set up the headers for the GitHub API request
headers = {
    'Authorization': f'token {os.environ["GITHUB_TOKEN"]}',
    'Accept': 'application/vnd.github.v3+json',
}

# Make the API request
response = requests.get(
    f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits',
    headers=headers,
)

# Parse the response JSON
commits = response.json()

# The latest commit is the first item in the list
latest_commit = commits[0]['sha']

# Iterate over the findings and post a comment for each one
for finding in findings['results']:
    body = f'''
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
