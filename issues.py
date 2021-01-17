#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import urllib.request


def parse_iso(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def days_between(d1, d2):
    return (d2 - d1).days


def get_json(url, headers):
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    return json.loads(response.read())


def get_issues(repo):
    page = 0
    while True:
        url = f"https://api.github.com/repos/{repo}/issues?per_page=100&page={page}"
        # https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-issues-assigned-to-the-authenticated-user-preview-notices
        issues = get_json(
            url, {"Accept": "application/vnd.github.squirrel-girl-preview"}
        )
        if not issues:
            break
        for issue in issues:
            yield issue
        page += 1


def write_csv(filename, fieldnames, rows):
    with open(filename, "w") as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def synthesize_issue(issue):
    url = issue["html_url"]
    title = issue["title"]
    user = issue["user"]["login"]
    is_pr = "pull_request" in issue
    labels = ", ".join(label["name"] for label in issue["labels"])

    now = datetime.datetime.now()
    created_at = parse_iso(issue["created_at"])
    updated_at = parse_iso(issue["updated_at"])
    days_open = days_between(created_at, now)
    days_active = days_between(created_at, updated_at)
    days_inactive = days_between(updated_at, now)

    comments = issue["comments"]
    reactions = issue["reactions"]["total_count"]

    return {
        "url": url,
        "title": title,
        "user": user,
        "is_pr": is_pr,
        "labels": labels,
        "created_at": created_at.date(),
        "updated_at": updated_at.date(),
        "days_open": max(0, days_open),
        "days_active": max(0, days_active),
        "days_inactive": max(0, days_inactive),
        "comments": comments,
        "reactions": reactions,
    }


def synthesize_issues(issues):
    for issue in issues:
        yield synthesize_issue(issue)


def write_issues_csv(filename, issues):
    fieldnames = [
        "url",
        "title",
        "user",
        "is_pr",
        "labels",
        "created_at",
        "updated_at",
        "days_open",
        "days_active",
        "days_inactive",
        "comments",
        "reactions",
    ]
    write_csv(filename, fieldnames, synthesize_issues(issues))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    args = parser.parse_args()

    filename = (
        f"{args.repo.replace('/','-')}-issues-{datetime.date.today().isoformat()}.csv"
    )
    write_issues_csv(filename, get_issues(args.repo))
    print(f"Written to {filename}")


if __name__ == "__main__":
    main()
