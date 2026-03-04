import os
import json
import re
import requests
from github import Github, Auth

gh_token = os.environ.get("GITHUB_TOKEN")
model_token = os.environ.get("GH_MODELS_TOKEN")
repo_name = os.environ.get("REPOSITORY")
event_name = os.environ.get("EVENT_NAME")
allowed_users = [u.strip().lower() for u in os.environ.get("ALLOWED_USER", "").split(",")]

MODEL_NAME = "Llama-3.3-70B-Instruct"
ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"

auth = Auth.Token(gh_token)
gh = Github(auth=auth)
repo = gh.get_repo(repo_name)

diff_text = ""
event_context = ""
author_login = ""
trigger_labels = []

if event_name == "push":
    commit_sha = os.environ.get("COMMIT_SHA")
    commit = repo.get_commit(commit_sha)
    if not commit.author: exit(0)
    author_login = commit.author.login.strip().lower()
    if author_login not in allowed_users: exit(0)
    event_context = f"Commit Message: {commit.commit.message}"
    trigger_labels = [m.lower() for m in re.findall(r'\[(.*?)\]', commit.commit.message)]
    for file in commit.files:
        diff_text += f"File: {file.filename}\nPatch:\n{file.patch}\n\n"
elif event_name == "pull_request":
    pr_number = int(os.environ.get("PR_NUMBER"))
    pr = repo.get_pull(pr_number)
    author_login = pr.user.login.strip().lower()
    if author_login not in allowed_users: exit(0)
    event_context = f"PR Title: {pr.title}\nPR Body: {pr.body}"
    trigger_labels = [label.name.lower() for label in pr.labels]
    for file in pr.get_files():
        diff_text += f"File: {file.filename}\nPatch:\n{file.patch}\n\n"

selected_prompt = f"Analyze changes: {diff_text}. Context: {event_context}"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {model_token}"
}

payload = {
    "messages": [
        {"role": "system", "content": "You are a professional code auditor. Return ONLY raw JSON with keys: issue_title, issue_body, labels."},
        {"role": "user", "content": selected_prompt}
    ],
    "model": MODEL_NAME,
    "temperature": 0.1,
    "max_tokens": 4096
}

response = requests.post(ENDPOINT, headers=headers, json=payload)
res_data = response.json()

try:
    raw_content = res_data['choices'][0]['message']['content'].strip()
    raw_content = re.sub(r'^```json\s*|```$', '', raw_content, flags=re.MULTILINE)
    result = json.loads(raw_content)

    repo.create_issue(
        title=result['issue_title'],
        body=result['issue_body'] + f"\n\n---\n*Analyzed by {MODEL_NAME}*",
        labels=result.get('labels', [])
    )
except Exception as e:
    print(f"Error parsing Llama response: {e}")
    print(f"Raw response: {res_data}")
