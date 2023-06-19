import os
from pathlib import Path
from typing import List, Dict, Any

import yaml
from jinja2 import Environment, select_autoescape, FileSystemLoader
from pydantic import BaseModel, RootModel
from github import Github


GH_TOKEN = os.getenv("GH_TOKEN")
g = Github(login_or_token=GH_TOKEN)


class Issue(BaseModel):
    project: str
    issue: int
    title: str | None = None
    state: str | None = None
    assignee: str | None = None


Issues = RootModel[List[Issue]]


def gather_issues() -> Issues:
    with Path("issues.yml").open() as f:
        issues = Issues.model_validate(yaml.safe_load(f))
    return issues


def rewrite_readme(table: List[Dict[str, Any]]) -> None:
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template("README.md.jinja")

    with Path("README.md").open("w") as f:
        f.write(template.render(table=table))


def rewrite_issues(issues: List[Dict[str, Any]]) -> None:
    with Path("issues.yml").open("w") as f:
        yaml.safe_dump(issues, f)


if __name__ == "__main__":
    issues = gather_issues()

    for issue in issues.root:
        # Skip if issue was already closed
        if issue.state == "closed" and issue.assignee is not None:
            continue

        repo = g.get_repo(issue.project)
        gh_issue = repo.get_issue(issue.issue)
        issue.title = gh_issue.title
        issue.state = gh_issue.state
        issue.assignee = gh_issue.assignee.login if gh_issue.assignee else None

    issue_list: list[dict[str, Any]] = issues.model_dump()  # type: ignore
    sorted_issues = sorted(issue_list, key=lambda x: x["project"])
    rewrite_issues(sorted_issues)
    rewrite_readme(sorted_issues)
