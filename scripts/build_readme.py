# -*- coding: utf-8 -*-
"""根据 data/stars.json 和 data/categories.json 生成 README.md。

用法：py -3 scripts/build_readme.py
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from common import CATEGORIES_PATH, README_PATH, STARS_PATH, get_user

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

UNCATEGORIZED = {
    "id": "uncategorized",
    "name": "📥 未分类",
    "description": "新 Star 的项目，还没来得及分类。",
}


def format_stars(n):
    """1531 -> 1.5k，2000 -> 2k，999 -> 999。"""
    if n < 1000:
        return str(n)
    k = (Decimal(n) / 1000).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{k.normalize():f}k"


def escape_cell(text):
    """让任意文本可以安全放进 Markdown 表格单元格。"""
    if not text:
        return ""
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("|", "\\|").strip()


def group_repos(stars, config):
    """按分类分组，返回 [(分类, [(repo, note), ...]), ...]，空分类不返回。"""
    categories = list(config["categories"])
    known_ids = {c["id"] for c in categories}
    groups = {c["id"]: [] for c in categories}
    groups[UNCATEGORIZED["id"]] = []

    for r in stars:
        entry = config["repos"].get(r["full_name"])
        if entry is None:
            groups[UNCATEGORIZED["id"]].append((r, ""))
            continue
        if entry["category"] not in known_ids:
            raise ValueError(f"{r['full_name']} 的分类 {entry['category']!r} 不存在于 categories 中")
        groups[entry["category"]].append((r, entry.get("note", "")))

    result = []
    for c in categories + [UNCATEGORIZED]:
        items = sorted(groups[c["id"]], key=lambda x: x[0]["stars"], reverse=True)
        if items:
            result.append((c, items))
    return result


def render_row(r, note):
    name = f"[{r['full_name']}]({r['url']})"
    if r.get("archived"):
        name += " 🗄️已归档"
    cells = [
        name,
        escape_cell(r.get("description")),
        escape_cell(note),
        escape_cell(r.get("language")) or "-",
        format_stars(r["stars"]),
    ]
    return "| " + " | ".join(cells) + " |"


def render(stars, config, user, today):
    groups = group_repos(stars, config)
    lines = [
        "# 🌟 My GitHub Stars",
        "",
        f"[{user}](https://github.com/{user}) 在 GitHub 上 Star 过的项目，按用途分类整理。"
        f"共 {len(stars)} 个项目，每天自动更新。",
        "",
        f"> 最后更新：{today}",
        "",
        "## 目录",
        "",
    ]
    for c, items in groups:
        lines.append(f"- [{c['name']}](#{c['id']})（{len(items)}）")
    lines.append("")

    for c, items in groups:
        lines += [
            f'<a id="{c["id"]}"></a>',
            "",
            f"## {c['name']}",
            "",
            c.get("description", ""),
            "",
            "| 项目 | 简介 | 我的点评 | 语言 | ⭐ Star |",
            "| --- | --- | --- | --- | --- |",
        ]
        lines += [render_row(r, note) for r, note in items]
        lines.append("")

    lines += [
        "---",
        "",
        "## 关于这个仓库",
        "",
        "- 数据由 [`scripts/fetch_stars.py`](scripts/fetch_stars.py) 通过 GitHub API 拉取，"
        "README 由 [`scripts/build_readme.py`](scripts/build_readme.py) 生成，请不要手动修改 README。",
        "- 分类和点评写在 [`data/categories.json`](data/categories.json) 里，新 Star 的项目会先出现在「未分类」。",
        "- GitHub Actions 每天自动更新一次，也可以在 Actions 页面手动运行。",
        "",
        "想给自己也做一个？Fork 本仓库，改好 `data/categories.json`，"
        "再到 Actions 页面启用工作流即可，用户名会自动用你的。",
        "",
    ]
    return "\n".join(lines)


def main():
    with open(STARS_PATH, encoding="utf-8") as f:
        stars = json.load(f)
    with open(CATEGORIES_PATH, encoding="utf-8") as f:
        config = json.load(f)

    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    content = render(stars, config, user=get_user(), today=today)
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    starred = {r["full_name"] for r in stars}
    new = [r["full_name"] for r in stars if r["full_name"] not in config["repos"]]
    gone = [name for name in config["repos"] if name not in starred]
    print(f"已生成 README：{len(stars)} 个项目")
    if new:
        print(f"未分类（{len(new)}）：" + "、".join(new))
    if gone:
        print(f"已取消 Star，可从 categories.json 删除（{len(gone)}）：" + "、".join(gone))


if __name__ == "__main__":
    main()
