#!/usr/bin/env python

import sys
import json
import requests

# Authentication for the user who is filing the issue. Username/API_KEY
USERNAME = 'HsiangNianian'
API_KEY = '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'

# The repository to add this issue to
REPO_OWNER = 'HsiangNianian'
REPO_NAME = 'rssSub'


def create_github_issue(title, body=None, labels=None):
    """
    Create an issue on github.com using the given parameters.
    :param title: This is the title of the GitHub Issue
    :param body: Optional - This is the body of the issue, or the main text
    :param labels: Optional - What type of issue are we creating
    :return:
    """
    # Our url to create issues via POST
    url = 'https://api.github.com/repos/%s/%s/issues' % (REPO_OWNER, REPO_NAME)
    # Create an authenticated session to create the issue
    session = requests.Session()
    session.auth = (USERNAME, API_KEY)
    # Create the issue
    issue = {'title': title,
             'body': body,
             'labels': labels}
    # Add the issue to our repository
    r = session.post(url, json.dumps(issue))
    if r.status_code == 201:
        print('Successfully created Issue "%s"' % title)
    else:
        print('Failed to create Issue "%s"' % title)
        print('Response:', r.content)


# if __name__ == '__main__':
#     with open(sys.argv[1], 'r') as jsp:
#         payload = json.loads(jsp.read())
#     # What was done to the repo
#     action = payload['action']
#     # What is the repo name
#     repo = payload['repository']['full_name']
#     # Create an issue if the repository was deleted
#     if action == 'deleted':
#         create_github_issue('%s was deleted' % repo, 'Seems we\'ve got ourselves a bit of an issue here.\n\n@<repository-owner>',
#                             ['deleted'])
#     # Log the payload to a file
#     outfile = '/tmp/webhook-{}.log'.format(repo)
#     with open(outfile, 'w') as f:
#         f.write(json.dumps(payload))

def create_github_issue(title, body=None, labels=None):
    """
    Create an issue on github.com using the given parameters.
    :param title: This is the title of the GitHub Issue
    :param body: Optional - This is the body of the issue, or the main text
    :param labels: Optional - What type of issue are we creating
    :return:
    """
    # Our url to create issues via POST
    url = 'https://api.github.com/repos/%s/%s/issues' % (REPO_OWNER, REPO_NAME)
    # Create an authenticated session to create the issue
    session = requests.Session()
    session.auth = (USERNAME, API_KEY)
    # Create the issue
    issue = {'title': title,
             'body': body,
             'labels': labels}
    # Add the issue to our repository
    r = session.post(url, json.dumps(issue))
    if r.status_code == 201:
        print('Successfully created Issue "%s"' % title)
    else:
        print('Failed to create Issue "%s"' % title)
        print('Response:', r.content)
        
create_github_issue('%s was deleted' % repo, 'Seems we\'ve got ourselves a bit of an issue here.\n\n@<repository-owner>',
                             ['deleted'])