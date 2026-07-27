import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "agent-memory"))

import lessons_block  # noqa: E402

FIXTURES = os.path.join(REPO, "tests", "fixtures", "lessons")


def read(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


class TestBuildBlock(unittest.TestCase):
    def setUp(self):
        self.lessons = read("agent-lessons.md")
        self.profile = read("how-sahil-works.md")
        self.block = lessons_block.build_block(self.lessons, self.profile)

    def test_profile_appears_before_lessons(self):
        self.assertLess(
            self.block.index("How Sahil works"), self.block.index("api/dto")
        )

    def test_respects_the_line_cap(self):
        self.assertLessEqual(len(self.block.splitlines()), 60)

    def test_tight_cap_truncates_and_says_so(self):
        block = lessons_block.build_block(self.lessons, self.profile, max_lines=14)
        self.assertLessEqual(len(block.splitlines()), 14)
        self.assertIn("truncated", block)

    def test_truncation_never_splits_a_lesson_mid_entry(self):
        block = lessons_block.build_block(self.lessons, self.profile, max_lines=20)
        for heading in ("api/dto", "TooltipV2", "icon variant"):
            if heading in block:
                start = block.index(heading)
                self.assertIn("evidence:", block[start:])

    def test_empty_inputs_produce_empty_block(self):
        self.assertEqual(lessons_block.build_block("", ""), "")

    def test_profile_only(self):
        block = lessons_block.build_block("", self.profile)
        self.assertIn("How Sahil works", block)

    def test_lessons_only(self):
        block = lessons_block.build_block(self.lessons, "")
        self.assertIn("api/dto", block)

    def test_output_ends_with_a_single_newline(self):
        self.assertTrue(self.block.endswith("\n"))
        self.assertFalse(self.block.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
