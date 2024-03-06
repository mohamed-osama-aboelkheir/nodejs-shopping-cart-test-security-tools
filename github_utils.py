import requests
from urllib.parse import quote
import re


def get_pr_semgrep_comments(owner,repo,pr_number,token):

    fingerprints = {}

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
                fingerprints[match.group(1)] = comment

    return fingerprints

def create_semgrep_comments(owner,repo,pr_number,token,latest_commit,finding):

    # Set up the headers for the GitHub API request
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

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


def reply_to_pr_comment(owner,repo,pr_number,token,comment_id,latest_commit):

    resolve_comment_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    payload = {
        "body": f"Resolved by the commit [{latest_commit}](https://github.com/{owner}/{repo}/pull/{pr_number}/commits/{latest_commit})",
    }

    response = requests.post(
        resolve_comment_url,
        json=payload,
        headers=headers
    )

    if response.status_code == 201:
        print("Comment posted successfully to resolve the thread.")
    else:
        print(f"Failed to post comment. Status code: {response.status_code}, Response: {response.json()}")



