import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(REPO, "install.sh")

BEGIN = "# >>> agent lessons >>>"
END = "# <<< agent lessons <<<"


class InstallRoleCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.vault = os.path.join(self.tmp, "obsidian-vault")
        os.makedirs(os.path.join(self.vault, ".git"))
        os.makedirs(os.path.join(self.vault, "wiki"))
        with open(os.path.join(self.vault, "wiki", "agent-lessons.md"), "w") as fh:
            fh.write("### frontend: use TooltipV2\n- evidence: PRO-1 (2 hits)\n")
        with open(os.path.join(self.vault, "wiki", "how-sahil-works.md"), "w") as fh:
            fh.write("# How Sahil works\n\n- Wants real test output.\n")

    def install(self, role=None):
        """Run only the agent-memory portion of install.sh in a sandboxed HOME."""
        if role:
            open(os.path.join(self.tmp, role), "w").close()
        return subprocess.run(
            ["bash", "-c",
             f'. "{INSTALL}" 2>/dev/null; install_agent_memory'],
            env={**os.environ, "HOME": self.tmp,
                 "AGENT_MEMORY_SOURCE_ONLY": "1",
                 # Never spawn a real harvester daemon from a test run.
                 "AGENT_MEMORY_NO_START": "1"},
            capture_output=True, text=True,
        )

    def claude_md(self):
        path = os.path.join(self.tmp, ".claude", "CLAUDE.md")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def test_injects_the_lessons_block(self):
        self.install()
        body = self.claude_md()
        self.assertIn(BEGIN, body)
        self.assertIn(END, body)
        self.assertIn("TooltipV2", body)

    def test_block_is_idempotent(self):
        self.install()
        self.install()
        self.assertEqual(self.claude_md().count(BEGIN), 1)

    def test_seat_role_starts_the_harvester_marker(self):
        r = self.install(role=".agent-pool-seat")
        self.assertIn("harvester", (r.stdout + r.stderr).lower())

    def test_mac_role_does_not_mention_the_harvester(self):
        r = self.install()
        self.assertNotIn("harvester", (r.stdout + r.stderr).lower())

    def test_exits_zero_without_a_vault(self):
        import shutil

        shutil.rmtree(self.vault)
        r = self.install()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_refuses_to_write_through_a_symlink_into_the_repo(self):
        """Regression: ~/.claude/CLAUDE.md may still be the legacy symlink into the
        repo. Following it would commit the generated block into config/CLAUDE.md
        and ship it to every workspace."""
        target = os.path.join(REPO, "config", "CLAUDE.md")
        claude_dir = os.path.join(self.tmp, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        link = os.path.join(claude_dir, "CLAUDE.md")
        os.symlink(target, link)
        with open(target, encoding="utf-8") as fh:
            before = fh.read()

        r = self.install()

        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("refusing to inject", r.stdout + r.stderr)
        with open(target, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)

    def test_counts_a_restart_as_a_preemption_for_the_live_ticket(self):
        import json

        pool = os.path.join(self.tmp, "agent-pool")
        os.makedirs(pool, exist_ok=True)
        with open(os.path.join(pool, "current.json"), "w") as fh:
            json.dump({"ticket": "PRO-2374"}, fh)
        self.install(role=".agent-pool-seat")
        self.install()
        with open(os.path.join(pool, "preemptions-PRO-2374"), encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), "2")


class PoolBootHooksCase(unittest.TestCase):
    """pool-onboard Phase 6 requires the dotfiles entrypoint to carry these hooks,
    because Coder cannot push to a personal dotfiles repo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def hooks(self):
        return subprocess.run(
            ["bash", "-c", f'. "{INSTALL}" 2>/dev/null; run_pool_boot_hooks; echo "rc=$?"'],
            env={**os.environ, "HOME": self.tmp, "AGENT_MEMORY_SOURCE_ONLY": "1"},
            capture_output=True, text=True,
        )

    def test_no_op_without_role_markers(self):
        r = self.hooks()
        self.assertIn("rc=0", r.stdout)

    def test_hq_marker_alone_does_not_fail(self):
        # start-orchestrator.sh is placed by provision-box.sh, not by us. On a box's
        # first boot the dotfiles run first, so the guard must tolerate its absence.
        open(os.path.join(self.tmp, ".agent-pool-hq"), "w").close()
        r = self.hooks()
        self.assertIn("rc=0", r.stdout)

    def test_hq_marker_runs_the_orchestrator_when_present(self):
        open(os.path.join(self.tmp, ".agent-pool-hq"), "w").close()
        pool_dir = os.path.join(self.tmp, "agent-pool")
        os.makedirs(pool_dir)
        script = os.path.join(pool_dir, "start-orchestrator.sh")
        with open(script, "w") as fh:
            fh.write("#!/usr/bin/env bash\necho ORCHESTRATOR_STARTED\n")
        os.chmod(script, 0o755)
        r = self.hooks()
        self.assertIn("ORCHESTRATOR_STARTED", r.stdout)

    def test_seat_marker_alone_does_not_fail(self):
        open(os.path.join(self.tmp, ".agent-pool-seat"), "w").close()
        r = self.hooks()
        self.assertIn("rc=0", r.stdout)


if __name__ == "__main__":
    unittest.main()
