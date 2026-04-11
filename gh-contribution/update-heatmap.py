#!/usr/bin/env python3
"""
update-heatmap.py
arcwolf.github.io/project/ 히트맵 DATA 자동 업데이트 스크립트
- GitHub API로 최근 31일 커밋 수집
- project.md의 DATA=[...] 부분을 치환
- GitHub API PUT으로 push
"""

import subprocess, json, re, base64, sys
from datetime import datetime, timedelta, timezone

GH_USER = "arcwolf"
REPO_TARGET = "arcwolf.github.io"
FILE_PATH = "project.md"
DAYS = 31

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[WARN] cmd failed: {' '.join(cmd)}\n  stderr: {r.stderr.strip()}", file=sys.stderr)
    return r.stdout.strip()

def get_active_repos(cutoff_days=35):
    out = run(["gh", "repo", "list", "--limit", "60", "--json", "name,pushedAt"])
    if not out:
        return []
    repos = json.loads(out)
    cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
    return [
        r["name"] for r in repos
        if datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00")) > cutoff
    ]

def get_commits(repo, since):
    out = run([
        "gh", "api",
        f"repos/{GH_USER}/{repo}/commits?since={since}&per_page=100",
        "--jq", '[.[] | .commit.committer.date[:10]] | sort'
    ])
    try:
        return json.loads(out) if out else []
    except Exception:
        return []

def build_data(repos, since):
    data = []
    for repo in repos:
        dates = get_commits(repo, since)
        if dates:
            data.append({
                "name": repo,
                "url": f"https://github.com/{GH_USER}/{repo}",
                "dates": dates
            })
    data.sort(key=lambda x: len(x["dates"]), reverse=True)
    return data

def get_file():
    out = run(["gh", "api", f"repos/{GH_USER}/{REPO_TARGET}/contents/{FILE_PATH}",
               "--jq", "{sha:.sha,content:.content}"])
    obj = json.loads(out)
    content = base64.b64decode(obj["content"]).decode("utf-8")
    return obj["sha"], content

def put_file(sha, content, message):
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    run([
        "gh", "api", f"repos/{GH_USER}/{REPO_TARGET}/contents/{FILE_PATH}",
        "-X", "PUT",
        "-f", f"message={message}",
        "-f", f"content={encoded}",
        "-f", f"sha={sha}"
    ])

def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=DAYS)
    since = start.strftime("%Y-%m-%dT00:00:00Z")
    date_label = f"{start.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"

    print(f"[INFO] Fetching commits since {since}")
    repos = get_active_repos(cutoff_days=35)
    print(f"[INFO] Active repos ({len(repos)}): {repos}")

    data = build_data(repos, since)
    print(f"[INFO] Repos with commits: {[d['name'] for d in data]}")

    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    sha, content = get_file()

    # Replace DATA=[...] in the inline script block
    new_content = re.sub(
        r'var DATA=\[.*?\];',
        f'var DATA={data_json};',
        content,
        count=1,
        flags=re.DOTALL
    )

    if new_content == content:
        print("[ERROR] DATA pattern not found in project.md", file=sys.stderr)
        sys.exit(1)

    today = now.strftime("%Y-%m-%d")
    message = f"chore: 히트맵 데이터 업데이트 ({today})"
    put_file(sha, new_content, message)
    print(f"[INFO] Done — {message}")

if __name__ == "__main__":
    main()
