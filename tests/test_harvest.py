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


class TestBuildRecord(unittest.TestCase):
    def setUp(self):
        import json

        with open(os.path.join(FIXTURES, "run1", "issue.json"), encoding="utf-8") as fh:
            self.issue = json.load(fh)
        with open(os.path.join(FIXTURES, "run1", "evidence-PRO-2374.md"), encoding="utf-8") as fh:
            self.evidence = fh.read()
        self.corrections = harvest.parse_transcript(fixture_lines("transcript.jsonl"), SESSION)
        self.meta = {
            "ticket": "PRO-2374",
            "seat": "sahil-seat-2",
            "repo": "frontend",
            "branch": "sahil/pro-2374-update-share-dataset-copy",
            # Equals `ended` because the golden record is a FIRST sync: no prior
            # file existed, so the CLI's `existing_started(out) or ended` fell back
            # to `ended`. Preservation on re-sync is covered by TestPreservesStarted.
            "started": "2026-07-27T11:40:00Z",
            "ended": "2026-07-27T11:40:00Z",
            "preemptions": 2,
            "pr": "https://github.com/Zampfi/application-platform-frontend/pull/1234",
        }
        self.record = harvest.build_record(
            self.meta, self.evidence, self.issue, self.corrections
        )

    def test_matches_the_golden_record(self):
        with open(os.path.join(FIXTURES, "run1", "expected-record.md"), encoding="utf-8") as fh:
            self.assertEqual(self.record, fh.read())

    def test_is_byte_stable_across_calls(self):
        again = harvest.build_record(
            self.meta, self.evidence, self.issue, self.corrections
        )
        self.assertEqual(self.record, again)

    def test_plan_rounds_counts_rejections_plus_one(self):
        self.assertIn("plan_rounds: 2", self.record)

    def test_outcome_comes_from_labels(self):
        self.assertIn("outcome: ready-to-verify", self.record)

    def test_records_the_rejected_plan_under_human_corrections(self):
        body = self.record.split("## Human corrections", 1)[1]
        self.assertIn("put the icon map next to the picker", body)

    def test_failures_section_reports_preemptions(self):
        body = self.record.split("## Failures", 1)[1].split("##", 1)[0]
        self.assertIn("preempted 2", body)

    def test_missing_evidence_is_stated_not_omitted(self):
        record = harvest.build_record(self.meta, "", self.issue, self.corrections)
        self.assertIn("(no evidence recorded)", record)

    def test_no_corrections_is_stated_not_omitted(self):
        record = harvest.build_record(self.meta, self.evidence, self.issue, [])
        self.assertIn("(none)", record)
        self.assertIn("plan_rounds: 1", record)


class TestUnchangedExceptEnded(unittest.TestCase):
    """A re-sync of an unchanged run must not rewrite the record.

    Otherwise every 3-minute harvest cycle commits and pushes a record whose only
    difference is its `ended:` stamp.
    """

    def _record(self, ended):
        return "---\nticket: PRO-1\nended: %s\noutcome: planning\n---\n\nbody\n" % ended

    def test_true_when_only_ended_differs(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PRO-1.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._record("2026-07-27T10:00:00Z"))
            self.assertTrue(
                harvest.unchanged_except_ended(self._record("2026-07-27T10:03:00Z"), path)
            )

    def test_false_when_the_body_changed(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PRO-1.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._record("2026-07-27T10:00:00Z"))
            newer = self._record("2026-07-27T10:03:00Z").replace("planning", "pr-open")
            self.assertFalse(harvest.unchanged_except_ended(newer, path))

    def test_false_when_there_is_no_existing_record(self):
        self.assertFalse(
            harvest.unchanged_except_ended(self._record("2026-07-27T10:00:00Z"),
                                           "/nonexistent/PRO-1.md")
        )


class TestPreservesStarted(unittest.TestCase):
    def test_reads_started_from_an_existing_record(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PRO-2374.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("---\nticket: PRO-2374\nstarted: 2026-07-01T00:00:00Z\n---\n")
            self.assertEqual(harvest.existing_started(path), "2026-07-01T00:00:00Z")

    def test_returns_none_when_absent(self):
        self.assertIsNone(harvest.existing_started("/nonexistent/path.md"))

    def test_stops_at_the_frontmatter_fence_without_raising(self):
        # Regression: the original implementation mixed `for line in fh` with
        # fh.tell(), which raises OSError in Python 3. A record whose frontmatter
        # has no `started:` must reach the closing fence and return None cleanly.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PRO-2374.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("---\nticket: PRO-2374\n---\n\nstarted: not-frontmatter\n")
            self.assertIsNone(harvest.existing_started(path))


if __name__ == "__main__":
    unittest.main()
