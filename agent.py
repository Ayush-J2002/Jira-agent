import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from Tools import get_issue_summary,get_bug_details,list_all_bugs,create_jira_ticket

load_dotenv()

llm = ChatOpenAI(
    model="kgpt-reasoning-text",
    base_url="https://llm-proxy.kpit.com",
    api_key=os.getenv("OPENAI_API_KEY")
)

tools = [get_issue_summary,get_bug_details,list_all_bugs]

data_agent = create_react_agent(
    llm,
    tools,
    prompt="""
You are a Jira Data Agent.

You must:
1. Understand user request
2. Generate correct JQL
3. Call appropriate tool
4. Return clean summary

Rules:

Always use get_issue_summary when user asks:
- summary or count of expired tickets, bugs and testcase

JQL Knowledge:

Expired:
duedate < now() AND statusCategory != Done

Bug:
issuetype = Bug

Always include:
project = SWT

Output:
- Total count
- Table grouped by assignee
- Clean format
"""
)

create_agent=create_react_agent(
    llm,
    tools=[create_jira_ticket],
    prompt=""" 
    You are a Jira task creat agent.
    If user ask to create task, ticket or issue:
    - Use create_jira_ticket function 
    Do not show explanation
"""
)

def agent_respond(user_msg, history):

    router_prompt = f"""
Decide intent:

If user wants to CREATE task → respond: CREATE
Else → respond: DATA

User: {user_msg}
"""

    decision = llm.invoke(router_prompt).content.strip().upper()

    if "CREATE" in decision:
        result = create_agent.invoke({"messages": history + [{"role": "user", "content": user_msg}]})
    else:
        result = data_agent.invoke({"messages": history + [{"role": "user", "content": user_msg}]})

    return result["messages"][-1].content