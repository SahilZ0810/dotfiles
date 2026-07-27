import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "agent-memory"))

import harvest  # noqa: E402

FIXTURES = os.path.join(REPO, "tests", "fixtures")
SESSION = "11111111-2222-3333-4444-555555555555"


def fixture_lines(name):
    with open(os.path.join(FIXTURES, "run1", name), encoding="utf-8") as fh:
        return fh.readlines()


class TestParseTranscript(unittest.TestCase):
    def setUp(self):
        self.corrections = harvest.parse_transcript(fixture_lines("transcript.jsonl"), SESSION)

    def test_extracts_the_rejected_plan_reply_verbatim(self):
        rejected = [c for c in self.corrections if c["kind"] == "plan-rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(
            rejected[0]["text"],
            "don't add a new util file, put the icon map next to the picker",
        )

    def test_records_the_approval(self):
        approved = [c for c in self.corrections if c["kind"] == "plan-approved"]
        self.assertEqual([c["text"] for c in approved], ["PRO-2374"])

    def test_captures_human_replies_as_corrections(self):
        replies = [c["text"] for c in self.corrections if c["kind"] == "reply"]
        self.assertIn("don't add a new util file, put the icon map next to the picker", replies)
        self.assertIn("approved", replies)

    def test_skips_slash_commands(self):
        replies = [c["text"] for c in self.corrections if c["kind"] == "reply"]
        self.assertNotIn("/agent-loop PRO-2374", replies)

    def test_skips_system_reminder_blocks(self):
        for c in self.corrections:
            self.assertNotIn("system-reminder", c["text"])

    def test_filters_by_session_id(self):
        for c in self.corrections:
            self.assertNotIn("different session", c["text"])

    def test_no_session_filter_includes_everything(self):
        allc = harvest.parse_transcript(fixture_lines("transcript.jsonl"), None)
        self.assertIn(
            "this belongs to a different session",
            [c["text"] for c in allc if c["kind"] == "reply"],
        )

    def test_tolerates_top_level_content_shape(self):
        replies = [c["text"] for c in self.corrections if c["kind"] == "reply"]
        self.assertIn("legacy top-level content shape", replies)

    def test_skips_malformed_json_without_raising(self):
        # The fixture's last line is not JSON; reaching this assertion proves no raise.
        self.assertTrue(len(self.corrections) > 0)

    def test_assistant_text_is_not_a_correction(self):
        replies = [c["text"] for c in self.corrections if c["kind"] == "reply"]
        self.assertNotIn("Plan posted to Linear.", replies)

    def test_every_entry_has_the_three_keys(self):
        for c in self.corrections:
            self.assertEqual(set(c.keys()), {"timestamp", "kind", "text"})

    def test_collapses_consecutive_duplicates(self):
        dup = [
            '{"type":"user","sessionId":"s","timestamp":"t","message":{"role":"user","content":"same"}}',
            '{"type":"user","sessionId":"s","timestamp":"t","message":{"role":"user","content":"same"}}',
        ]
        self.assertEqual(len(harvest.parse_transcript(dup, "s")), 1)


class TestDeriveOutcome(unittest.TestCase):
    def test_blocked_wins_over_any_stage(self):
        self.assertEqual(
            harvest.derive_outcome(["agent:implementing", "agent:blocked"]), "blocked"
        )

    def test_furthest_stage_wins(self):
        self.assertEqual(
            harvest.derive_outcome(["agent:planning", "agent:ready-to-verify"]),
            "ready-to-verify",
        )

    def test_unknown_when_no_agent_labels(self):
        self.assertEqual(harvest.derive_outcome(["Bug", "UI"]), "unknown")

    def test_empty_labels(self):
        self.assertEqual(harvest.derive_outcome([]), "unknown")


if __name__ == "__main__":
    unittest.main()
