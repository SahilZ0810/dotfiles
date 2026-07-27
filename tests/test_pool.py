import datetime
import importlib.machinery
import importlib.util
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_loader(
    "pool",
    importlib.machinery.SourceFileLoader("pool", os.path.join(REPO, "bin", "pool")),
)
pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pool)

NOW = datetime.datetime(2026, 7, 27, 12, 0, 0, tzinfo=datetime.timezone.utc)


class TestHeartbeatState(unittest.TestCase):
    def test_fresh_is_on(self):
        self.assertEqual(pool.heartbeat_state("2026-07-27T11:55:00Z", NOW), "ON")

    def test_stale_is_off(self):
        self.assertEqual(pool.heartbeat_state("2026-07-27T11:30:00Z", NOW), "OFF")

    def test_missing_is_off(self):
        self.assertEqual(pool.heartbeat_state(None, NOW), "OFF")

    def test_garbage_is_off(self):
        self.assertEqual(pool.heartbeat_state("not a date", NOW), "OFF")

    def test_boundary_is_on(self):
        self.assertEqual(pool.heartbeat_state("2026-07-27T11:50:01Z", NOW), "ON")


class TestRemoteWriteCmd(unittest.TestCase):
    """Regression: piping over `coder ssh` hangs forever (PTY, never sees EOF),
    which is how the token-distribution command wedged. The body must travel
    inside the command, not on stdin."""

    def test_round_trips_awkward_content(self):
        import base64 as b64
        import re

        body = "## Scope\n- don't use `Tooltip`\n- \"quoted\" & $VAR\n"
        cmd = pool.remote_write_cmd("/tmp/x.md", body)
        blob = re.search(r"echo (\S+) \| base64 -d", cmd).group(1)
        self.assertEqual(b64.b64decode(blob).decode("utf-8"), body)

    def test_payload_is_shell_safe(self):
        cmd = pool.remote_write_cmd("/tmp/x.md", "a'b\"c\n$(rm -rf /)\n")
        blob = cmd.split("echo ", 1)[1].split(" |", 1)[0]
        self.assertRegex(blob, r"^[A-Za-z0-9+/=]+$")

    def test_writes_to_the_requested_path(self):
        self.assertIn("> /tmp/pool-do-body.md", pool.remote_write_cmd("/tmp/pool-do-body.md", "x"))


class TestRenderStatus(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "config": {"pool_size": 2},
            "seats": {
                "sahil-seat-1": {"status": "implementing", "ticket": "PRO-2374",
                                 "stage": "implement", "pr_url": None},
                "sahil-seat-2": {"status": "free", "ticket": None,
                                 "stage": None, "pr_url": None},
            },
        }
        self.coder_rows = {"sahil-seat-1": "Started", "sahil-seat-2": "Stopped"}
        self.heartbeats = {"sahil-seat-1": "2026-07-27T11:58:00Z", "sahil-seat-2": None}

    def test_lists_every_seat(self):
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        self.assertIn("sahil-seat-1", out)
        self.assertIn("sahil-seat-2", out)

    def test_shows_the_ticket(self):
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        self.assertIn("PRO-2374", out)

    def test_flags_memory_off(self):
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        line = [l for l in out.splitlines() if "sahil-seat-2" in l][0]
        self.assertIn("OFF", line)

    def test_flags_memory_on(self):
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        line = [l for l in out.splitlines() if "sahil-seat-1" in l][0]
        self.assertIn("ON", line)

    def test_warns_when_a_busy_seat_is_not_running(self):
        self.coder_rows["sahil-seat-1"] = "Stopped"
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        self.assertIn("RESURRECT", out)

    def test_no_resurrect_warning_for_a_free_stopped_seat(self):
        out = pool.render_status(self.registry, self.coder_rows, self.heartbeats, NOW)
        line = [l for l in out.splitlines() if "sahil-seat-2" in l][0]
        self.assertNotIn("RESURRECT", line)

    def test_handles_an_empty_registry(self):
        out = pool.render_status({"seats": {}}, {}, {}, NOW)
        self.assertIn("no seats", out.lower())


if __name__ == "__main__":
    unittest.main()
