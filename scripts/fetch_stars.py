# -*- coding: utf-8 -*-
"""拉取 GitHub 用户的 Star 列表，保存到 data/stars.json。

用法：py -3 scripts/fetch_stars.py
可选环境变量：
  STARS_USER    要拉取的用户名（默认见 common.py）
  GITHUB_TOKEN  提高 API 限额（未设置时每小时 60 次请求）
"""
import json
import os
import sys
import urllib.error
import urllib.request

from common import STARS_PATH, get_user

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def fetch_page(user, page, token):
    url = f"https://api.github.com/users/{user}/starred?per_page=100&page={page}"
    req = urllib.request.Request(url)
    # star+json 格式会额外返回 starred_at（加星时间）
    req.add_header("Accept", "application/vnd.github.star+json")
    req.add_header("User-Agent", "my-github-stars")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def simplify(item):
    repo = item["repo"]
    return {
        "full_name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description") or "",
        "language": repo.get("language") or "",
        "topics": repo.get("topics") or [],
        "stars": repo.get("stargazers_count", 0),
        "archived": repo.get("archived", False),
        "pushed_at": repo.get("pushed_at"),
        "homepage": repo.get("homepage") or "",
        "license": (repo.get("license") or {}).get("spdx_id") or "",
        "starred_at": item.get("starred_at"),
    }


def main():
    user = get_user()
    token = os.environ.get("GITHUB_TOKEN")
    repos, page = [], 1
    try:
        while True:
            items = fetch_page(user, page, token)
            if not items:
                break
            repos.extend(simplify(i) for i in items)
            page += 1
    except urllib.error.HTTPError as e:
        # 出错时直接退出，不覆盖已有数据
        body = e.read().decode("utf-8", errors="replace")
        print(f"请求 GitHub API 失败（HTTP {e.code}）：{body}", file=sys.stderr)
        if e.code in (403, 429):
            print("可能是触发了限流，可设置环境变量 GITHUB_TOKEN 后重试。", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(STARS_PATH), exist_ok=True)
    with open(STARS_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{user} 共 {len(repos)} 个 Star，已保存到 {STARS_PATH}")


if __name__ == "__main__":
    main()
