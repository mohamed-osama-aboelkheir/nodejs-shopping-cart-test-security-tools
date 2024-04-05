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

        fingerprint_pattern = r'^<!--\s*semgrep_finding_fingerprint:\s*(.+)\s+-->$'
        status_pattern = r'^<!--\s*semgrep_finding_status:\s*(.+)\s+-->$'
        for comment in comments:
            first_line = comment['body'].splitlines()[0]
            fingerprint_match = re.search(fingerprint_pattern, first_line)
            if fingerprint_match: 
                second_line = comment['body'].splitlines()[1]
                status_match = re.search(status_pattern, second_line)
                comment["status"] = status_match.group(1) if status_match else "open"
                fingerprints[fingerprint_match.group(1)] = comment
    
    return fingerprints

def create_semgrep_comments(owner,repo,pr_number,token,latest_commit,finding):

    # Set up the headers for the GitHub API request
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    body = f'''<!-- semgrep_finding_fingerprint: {finding['extra']['fingerprint']} -->
<!-- semgrep_finding_status: open -->
## <img src="https://semgrep.dev/docs/img/semgrep.svg" width="30" height="30"> Semgrep finding
* **Rule ID:** {finding['check_id']}
* **Severity:** {finding['extra']['severity']}
* **Description:** {finding['extra']['message']}
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


def reply_to_pr_comment(owner,repo,pr_number,token,comment_id,latest_commit,action="resolve"):

    resolve_comment_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    if action == "resolve":
        reply_message = f"Resolved by the commit [{latest_commit}](https://github.com/{owner}/{repo}/pull/{pr_number}/commits/{latest_commit})"
    else:
        reply_message = f"Re-opened by the commit [{latest_commit}](https://github.com/{owner}/{repo}/pull/{pr_number}/commits/{latest_commit})" 

    payload = {
        "body": reply_message,
    }

    response = requests.post(
        resolve_comment_url,
        json=payload,
        headers=headers
    )

    if response.status_code == 201:
        print(f"Comment reply posted successfully to {action} the finding.")
    else:
        print(f"Failed to post comment reply. Status code: {response.status_code}, Response: {response.json()}")


def update_status_in_comment(owner,repo,comment_id,token,body,new_status):

    update_comment_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/comments/{comment_id}"

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    # Check if 2nd line has the status, if it does update it, if not insert new line
    body_lines = body.splitlines()
    second_line = body_lines[1]
    status_pattern = r'^<!--\s*semgrep_finding_status:\s*(.+)\s+-->$'
    status_match = re.search(status_pattern, second_line)
    if status_match:
        body_lines[1] = f'<!-- semgrep_finding_status: {new_status} -->'
    else:
        body_lines.insert(1,f'<!-- semgrep_finding_status: {new_status} -->')

    modified_body = "\n".join(body_lines)

    payload = {
        "body": modified_body
    }

    response = requests.patch(
        update_comment_url,
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        print("Comment status updated successfully")
    else:
        print(f"Failed to update comment. Status code: {response.status_code}, Response: {response.json()}")
