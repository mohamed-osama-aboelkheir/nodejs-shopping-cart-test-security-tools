from slack_sdk.webhook import WebhookClient
from urllib.parse import quote
import re

def submit_slack_notification(webhook_url,finding,pr_number,pr_url,notification_type="open"):

    if notification_type == "open" or notification_type == "reopen": 
        finding_details = f'''
*Rule ID:* {finding['check_id']}
*File:* {finding['path']}
*Line:* {finding['start']['line']}
*Severity:* {finding['extra']['severity']}
*Description:* {finding['extra']['message']}
*Semgrep Rule:* <https://semgrep.dev/r/{quote(finding['check_id'])}|Link>
''' 
    else:
        finding_details = convert_format_to_slack(finding)


    if notification_type == "open": 
        message = f'''
Added the below finding to PR <{pr_url}|#{pr_number}>
{finding_details}
        '''
    elif notification_type == "reopen":
        message = f'''
Re-opened the below finding in PR <{pr_url}|#{pr_number}>
{finding_details}
        '''
    elif notification_type == "resolved":
        message = f'''
Resolved the below finding in PR <{pr_url}|#{pr_number}>
{finding_details}
        '''
    else:
        print("ERROR: invalid notification type")
        return false


    webhook = WebhookClient(webhook_url)
    response = webhook.send(
        text="Semgpre PR notification",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type":"divider"
            }
        ]
    )
    return response.status_code == 200


def convert_format_to_slack(message):
    new_message=[]
    for line in message.split('\n'):
        if line.startswith('*'):
            # Remove * from beginning of line
            new_line = re.sub(r'^\* ','',line)
            # Replace ** to * for bold
            new_line = re.sub(r"\*\*","*",new_line)
            # Replace link to slack format
            link_pattern = r'(.*)\[(.+)\]\((.+)\)(.*)'
            #if re.match(link_pattern, new_line):
            new_line = re.sub(link_pattern,r'\1<\3|\2>\4', new_line)
            new_message.append(new_line)

    new_message = ('\n').join(new_message)

    return new_message

