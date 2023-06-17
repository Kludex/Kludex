import os
from pathlib import Path
from typing import List

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


Issues = RootModel[List[Issue]]


def write_readme(table: List[Issue]) -> None:
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template("README.md.jinja")

    with Path("README.md").open("w") as f:
        f.write(template.render(table=table))


def gather_issues() -> Issues:
    with Path("issues.yml").open() as f:
        issues = Issues.model_validate(yaml.safe_load(f))
    return issues


def rewrite_issues(issues: List[Issue]):
    with Path("issues.yml").open("w") as f:
        yaml.safe_dump(issues, f)


if __name__ == "__main__":
    issues = gather_issues()

    table: List[Issue] = []
    for issue in issues.root:
        repo = g.get_repo(issue.project)
        gh_issue = repo.get_issue(issue.issue)
        issue.title = gh_issue.title

        if gh_issue.state == "open":
            table.append(issue)

    if len(table) != len(issues.root):
        rewrite_issues(table)

    write_readme(table)
