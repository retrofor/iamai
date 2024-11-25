import re
from examples.plugins._github.lib.opengraph import Tag

URL_PCHAR = r"(?:[a-zA-Z0-9\-._~!$&'()*+,;=:@]|%[0-9a-fA-F]{2})"
URL_QUERY_REGEX = rf"(?:\?(?:{URL_PCHAR}|[/?])*)?"

OWNER_REGEX = r"(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?)"
REPO_REGEX = r"(?P<repo>[a-zA-Z0-9_\-\.]+)"
FULLREPO_REGEX = rf"{OWNER_REGEX}/{REPO_REGEX}"
COMMIT_HASH_REGEX = r"(?P<commit>[0-9a-f]{5,40})"
ISSUE_REGEX = r"(?P<issue>\d+)"
ISSUE_COMMENT_REGEX = r"(?:#issuecomment-(?P<comment>\d+))?"

GITHUB_LINK_REGEX = r"github\.com"
GITHUB_REPO_LINK_REGEX = rf"{GITHUB_LINK_REGEX}/{FULLREPO_REGEX}"
GITHUB_COMMIT_LINK_REGEX = rf"{GITHUB_REPO_LINK_REGEX}/commit/{COMMIT_HASH_REGEX}"
GITHUB_ISSUE_LINK_REGEX = (
    rf"{GITHUB_REPO_LINK_REGEX}/issues/{ISSUE_REGEX}"
    rf"{URL_QUERY_REGEX}{ISSUE_COMMENT_REGEX}"
)
GITHUB_PR_LINK_REGEX = (
    rf"{GITHUB_REPO_LINK_REGEX}/pull/{ISSUE_REGEX}"
    rf"{URL_QUERY_REGEX}{ISSUE_COMMENT_REGEX}"
)
GITHUB_ISSUE_OR_PR_LINK_REGEX = (
    rf"{GITHUB_REPO_LINK_REGEX}/(?:issues|pull)/{ISSUE_REGEX}"
    rf"{URL_QUERY_REGEX}{ISSUE_COMMENT_REGEX}"
)
GITHUB_PR_COMMIT_LINK_REGEX = rf"{GITHUB_PR_LINK_REGEX}/commits/{COMMIT_HASH_REGEX}"
GITHUB_PR_FILE_LINK_REGEX = rf"{GITHUB_PR_LINK_REGEX}/files"
GITHUB_RELEASE_LINK_REGEX = (
    rf"{GITHUB_REPO_LINK_REGEX}/releases/tag/(?P<tag>{URL_PCHAR}+)"
)


def match_github_links(url):
    """
    根据优先级匹配 GitHub 链接。
    按照以下优先级进行匹配：
    1. GITHUB_REPO_LINK_REGEX
    2. FULLREPO_REGEX
    3. GITHUB_COMMIT_LINK_REGEX
    4. GITHUB_ISSUE_LINK_REGEX
    5. GITHUB_PR_LINK_REGEX
    6. GITHUB_ISSUE_OR_PR_LINK_REGEX
    7. GITHUB_PR_COMMIT_LINK_REGEX
    8. GITHUB_PR_FILE_LINK_REGEX
    9. GITHUB_RELEASE_LINK_REGEX
    """
    patterns = [
        re.compile(GITHUB_RELEASE_LINK_REGEX),
        re.compile(GITHUB_PR_FILE_LINK_REGEX),
        re.compile(GITHUB_COMMIT_LINK_REGEX),
        re.compile(GITHUB_ISSUE_LINK_REGEX),
        re.compile(GITHUB_PR_LINK_REGEX),
        re.compile(GITHUB_ISSUE_OR_PR_LINK_REGEX),
        re.compile(GITHUB_PR_COMMIT_LINK_REGEX),
        re.compile(GITHUB_REPO_LINK_REGEX),
        re.compile(FULLREPO_REGEX),
    ]

    for pattern in patterns:
        match = pattern.search(url)
        if match:
            return match

    return None


repo_link = match_github_links(
    "https://github.com/HydroRoll-Team/infini/pull/55"
)  # {'owner': 'HydroRoll-Team', 'repo': 'infini', 'issue': '55', 'comment': None}

if __name__ == "__main__":
    print(repo_link)
    print(Tag(**repo_link.groupdict()))
