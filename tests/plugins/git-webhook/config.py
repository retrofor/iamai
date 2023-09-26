EVENT_DESCRIPTIONS = {
    "commit_comment": "{comment[user][login]} commented on \"{comment[commit_id]}\" in \"{repository[full_name]}\"\n{comment[body]}",
    "create": "{sender[login]} created {ref_type} ({ref}) in " "{repository[full_name]}",
    "delete": "{sender[login]} deleted {ref_type} ({ref}) in " "{repository[full_name]}",
    "deployment": "{sender[login]} deployed {deployment[ref]} to "
    "{deployment[environment]} in {repository[full_name]}",
    "deployment_status": "deployment of {deployement[ref]} to "
    "{deployment[environment]} "
    "{deployment_status[state]} in "
    "{repository[full_name]}",
    "fork": "\"{forkee[owner][login]}\" forked \"{forkee[name]}\" (Total {repository[forks_count]} forkee)",
    "gollum": "{sender[login]} edited wiki pages in {repository[full_name]}",
    "issue_comment": {
		"created": "{sender[login]} commented on issue #{issue[number]} in \"{repository[full_name]}\"\n{comment[body]}"
	},
    "issues": {
		"opened": "{sender[login]} {action} issue #{issue[number]} in \"{repository[full_name]}\"\n\"{issue[title]}\"\n{issue[body]}",
		"closed": "{sender[login]} {action} issue #{issue[number]} in \"{repository[full_name]}\""
	},
    "member": "{sender[login]} {action} member {member[login]} in " "{repository[full_name]}",
    "membership": "{sender[login]} {action} member {member[login]} to team " "{team[name]} in {repository[full_name]}",
    "page_build": "{sender[login]} built pages in {repository[full_name]}",
    "ping": "ping from {sender[login]}",
    "public": "{sender[login]} publicized {repository[full_name]}",
    "pull_request": "{sender[login]} {action} pull #{pull_request[number]} in " "{repository[full_name]}",
    "pull_request_review": "{sender[login]} {action} {review[state]} "
    "review on pull #{pull_request[number]} in "
    "{repository[full_name]}",
    "pull_request_review_comment": "{comment[user][login]} {action} comment "
    "on pull #{pull_request[number]} in "
    "{repository[full_name]}",
    "push": "{pusher[name]} pushed {ref} in \"{repository[full_name]}\"\n{commits[0][message]}",
    "release": "{release[author][login]} {action} {release[tag_name]} in \"{repository[full_name]}\"",
    "repository": "{sender[login]} {action} repository " "{repository[full_name]}",
    "status": "{sender[login]} set {sha} status to {state} in " "{repository[full_name]}",
    "team_add": "{sender[login]} added repository {repository[full_name]} to " "team {team[name]}",
    "watch": "{sender[login]} {action} watch in repository \"{repository[full_name]}\"(Total {repository[stargazers_count]} stargazers)"
}

