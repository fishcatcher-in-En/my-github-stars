# -*- coding: utf-8 -*-
"""脚本共用的配置和路径。"""
import os

# 要整理的 GitHub 用户；可用环境变量 STARS_USER 覆盖（GitHub Actions 中自动设为仓库所有者）
DEFAULT_USER = "fishcatcher-in-En"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARS_PATH = os.path.join(ROOT, "data", "stars.json")
CATEGORIES_PATH = os.path.join(ROOT, "data", "categories.json")
README_PATH = os.path.join(ROOT, "README.md")


def get_user():
    return os.environ.get("STARS_USER") or DEFAULT_USER
