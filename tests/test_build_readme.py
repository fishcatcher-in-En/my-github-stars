# -*- coding: utf-8 -*-
"""build_readme 的单元测试。运行：py -3 -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from build_readme import escape_cell, format_stars, render  # noqa: E402


def repo(name, stars=10, desc="desc", lang="Python", archived=False):
    return {
        "full_name": name,
        "url": f"https://github.com/{name}",
        "description": desc,
        "language": lang,
        "stars": stars,
        "archived": archived,
    }


CONFIG = {
    "categories": [
        {"id": "a", "name": "🅰️ 分类A", "description": "A 的说明"},
        {"id": "b", "name": "🅱️ 分类B", "description": "B 的说明"},
    ],
    "repos": {
        "x/low": {"category": "a", "note": ""},
        "x/high": {"category": "a", "note": "很好用"},
        "y/one": {"category": "b", "note": ""},
    },
}


class FormatStarsTest(unittest.TestCase):
    def test_small_numbers_unchanged(self):
        self.assertEqual(format_stars(999), "999")

    def test_thousands_use_k(self):
        self.assertEqual(format_stars(1531), "1.5k")
        self.assertEqual(format_stars(120650), "120.7k")

    def test_trailing_zero_dropped(self):
        self.assertEqual(format_stars(2000), "2k")


class EscapeCellTest(unittest.TestCase):
    def test_pipe_and_newline(self):
        self.assertEqual(escape_cell("a | b\nc\r\nd"), "a \\| b c d")

    def test_html_brackets(self):
        self.assertEqual(escape_cell("<script>"), "&lt;script&gt;")

    def test_none(self):
        self.assertEqual(escape_cell(None), "")


class RenderTest(unittest.TestCase):
    def render(self, stars):
        return render(stars, CONFIG, user="tester", today="2026-01-02")

    def test_header_has_user_total_and_date(self):
        out = self.render([repo("x/low"), repo("y/one")])
        self.assertIn("tester", out)
        self.assertIn("共 2 个项目", out)
        self.assertIn("2026-01-02", out)

    def test_sorted_by_stars_within_category(self):
        out = self.render([repo("x/low", stars=5), repo("x/high", stars=500)])
        self.assertLess(out.index("[x/high]"), out.index("[x/low]"))

    def test_note_shown(self):
        out = self.render([repo("x/high")])
        self.assertIn("很好用", out)

    def test_category_order_and_toc_counts(self):
        out = self.render([repo("y/one"), repo("x/low"), repo("x/high")])
        self.assertLess(out.index("## 🅰️ 分类A"), out.index("## 🅱️ 分类B"))
        self.assertIn("[🅰️ 分类A](#a)（2）", out)
        self.assertIn("[🅱️ 分类B](#b)（1）", out)

    def test_empty_category_omitted(self):
        out = self.render([repo("x/low")])
        self.assertNotIn("分类B", out)

    def test_uncategorized_section(self):
        out = self.render([repo("x/low"), repo("new/repo")])
        self.assertIn("## 📥 未分类", out)
        self.assertGreater(out.index("[new/repo]"), out.index("## 📥 未分类"))

    def test_no_uncategorized_section_when_all_classified(self):
        out = self.render([repo("x/low")])
        self.assertNotIn("## 📥 未分类", out)

    def test_archived_marked(self):
        out = self.render([repo("x/low", archived=True)])
        self.assertIn("已归档", out)

    def test_description_escaped_in_table(self):
        out = self.render([repo("x/low", desc="a|b")])
        self.assertIn("a\\|b", out)

    def test_unknown_category_raises(self):
        config = {"categories": [], "repos": {"x/low": {"category": "nope", "note": ""}}}
        with self.assertRaises(ValueError):
            render([repo("x/low")], config, user="t", today="2026-01-02")


if __name__ == "__main__":
    unittest.main()
