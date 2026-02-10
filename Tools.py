from langchain_core.tools import tool
import requests
import os
from dotenv import load_dotenv
from collections import defaultdict
load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_PROJECT_KEY=os.getenv("JIRA_PROJECT_KEY")
JIRA_API_TOKEN =os.getenv("JIRA_API_TOKEN")


def jira_search(jql,fields="summary,assignee,status,reporter", retry=2):
    start = 0
    all_issues = []

    while True:
        url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        params = {
            "jql": jql,
            "startAt": start,
            "maxResults": 50,
            "fields": fields
        }

        r = requests.get(url, auth=(JIRA_EMAIL, JIRA_API_TOKEN), params=params)

        if r.status_code != 200:
            if retry > 0:
                return jira_search(jql, retry - 1)
            raise Exception(f"Jira error: {r.text}")

        data = r.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)

        if start + 50 >= data.get("total", 0):
            break

        start += 50

    return all_issues


@tool(description="Return total count + table grouped by assignee")
def get_issue_summary(jql: str) -> str:

    issues = jira_search(jql)
    total = len(issues)
    
    assignee_map = defaultdict(int)

    for i in issues:
        assignee = i["fields"]["assignee"]
        name = assignee["displayName"] if assignee else "Unassigned"
        assignee_map[name] += 1

    lines = []
    lines.append(f"\nTotal Tickets: {total}\n")
    lines.append("Assignee | Count")
    lines.append("-------------------")

    for name, count in sorted(assignee_map.items(), key=lambda x: -x[1]):
        lines.append(f"{name} | {count}")

    return "\n".join(lines)

@tool(description="list all bugs with key and assignee")
def list_all_bugs() -> str:

    issues = jira_search(
        jql="project=SWT AND issuetype=Bug",
        fields="assignee"
    )
    lines=[]

    for i in issues:
        key = i["key"]
        assignee = i["fields"].get("assignee")
        name = assignee["displayName"] if assignee else "Unassigned"
        lines.append(f"{key} | {name}")

    if not lines:
        return "No bugs found."

    return "\n".join(lines)

@tool(description="give details of a specific bug")
def get_bug_details(issue_key: str) -> str:
    issues=jira_search(
        jql=f"key={issue_key}",
        fields="summary,status,assignee,reporter"
    )

    if not issues:
        return f"No bug found with key {issue_key}"

    fields = issues[0]["fields"]

    summary = fields.get("summary", "N/A")
    status = fields.get("status", {}).get("name", "N/A")
    assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
    reporter = (fields.get("reporter") or {}).get("displayName", "Unknown")

    bug_link = f"{JIRA_BASE_URL}/browse/{issue_key}"

    return (
        f"Bug: {issue_key}\n"
        f"Summary: {summary}\n"
        f"Status: {status}\n"
        f"Assignee: {assignee}\n"
        f"Reporter: {reporter}\n"
        f"BUG_LINK:{bug_link}"
    )

@tool(description="creates tasks or ticket")
def create_jira_ticket():
    return "Task ticket created successfully - SWT-XXXX"


TOOLS = [get_issue_summary,get_bug_details,list_all_bugs]