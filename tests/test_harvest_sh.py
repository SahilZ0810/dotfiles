import json
import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARVEST_SH = os.path.join(REPO, "scripts", "agent-memory", "harvest.sh")
FIXTURES = os.path.join(REPO, "tests", "fixtures")


def git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True,
    )


class HarvestShCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.remote = os.path.join(self.tmp, "remote.git")
        self.vault = os.path.join(self.tmp, "vault")
        self.pool = os.path.join(self.tmp, "agent-pool")
        # capture_output keeps git's "cloned an empty repository" notice off the
        # test report — an empty clone is exactly what this fixture wants.
        subprocess.run(["git", "init", "--bare", "-q", self.remote],
                       check=True, capture_output=True)
        subprocess.run(["git", "clone", "-q", self.remote, self.vault],
                       check=True, capture_output=True)
        os.makedirs(os.path.join(self.vault, "reports", "agent-runs"))
        with open(os.path.join(self.vault, "reports", "agent-runs", ".gitkeep"), "w") as fh:
            fh.write("")
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "-q", "-m", "init")
        git(self.vault, "push", "-q", "origin", "HEAD:refs/heads/main")

        os.makedirs(self.pool)
        with open(os.path.join(self.pool, "current.json"), "w") as fh:
            json.dump(
                {"ticket": "PRO-2374",
                 "session_id": "11111111-2222-3333-4444-555555555555",
                 "repo": "frontend"}, fh)
        with open(os.path.join(self.pool, "evidence-PRO-2374.md"), "w") as fh:
            fh.write("- `npm run test` -> 412 passed\n")

        # Stub linear.py: prints the fixture issue JSON for `get <ID> --json`,
        # nothing for `pr`. Keeps the test offline.
        self.stub = os.path.join(self.tmp, "linear.py")
        with open(self.stub, "w") as fh:
            fh.write(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                f"issue = open({json.dumps(os.path.join(FIXTURES, 'run1', 'issue.json'))}).read()\n"
                "print(issue if sys.argv[1] == 'get' else '')\n"
            )
        os.chmod(self.stub, 0o755)

    def run_once(self, extra_env=None):
        env = {
            **os.environ,
            "HOME": self.tmp,
            "AGENT_MEMORY_VAULT": self.vault,
            "AGENT_MEMORY_POOL_DIR": self.pool,
            "AGENT_MEMORY_LINEAR": self.stub,
            "CODER_WORKSPACE_NAME": "sahil-seat-2",
            **(extra_env or {}),
        }
        return subprocess.run(
            ["bash", HARVEST_SH, "--once"], env=env, capture_output=True, text=True
        )

    def test_writes_the_run_record(self):
        r = self.run_once()
        self.assertEqual(r.returncode, 0, r.stderr)
        path = os.path.join(self.vault, "reports", "agent-runs", "PRO-2374.md")
        self.assertTrue(os.path.exists(path), r.stdout + r.stderr)
        with open(path, encoding="utf-8") as fh:
            self.assertIn("ticket: PRO-2374", fh.read())

    def test_pushes_to_the_remote(self):
        self.run_once()
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=self.remote, capture_output=True, text=True,
        ).stdout
        self.assertIn("reports/agent-runs/PRO-2374.md", listing)

    def test_writes_the_heartbeat(self):
        self.run_once()
        beat = os.path.join(self.pool, "memory-heartbeat")
        self.assertTrue(os.path.exists(beat))
        with open(beat, encoding="utf-8") as fh:
            self.assertRegex(fh.read().strip(), r"^\d{4}-\d{2}-\d{2}T")

    def test_is_idempotent_second_run_makes_no_new_commit(self):
        self.run_once()
        first = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.vault,
                               capture_output=True, text=True).stdout
        self.run_once()
        second = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.vault,
                                capture_output=True, text=True).stdout
        self.assertEqual(first, second)

    def test_exits_zero_and_writes_nothing_without_current_json(self):
        os.remove(os.path.join(self.pool, "current.json"))
        r = self.run_once()
        self.assertEqual(r.returncode, 0)
        self.assertFalse(
            os.path.exists(os.path.join(self.vault, "reports", "agent-runs", "PRO-2374.md"))
        )

    def test_exits_zero_without_a_vault(self):
        r = self.run_once({"AGENT_MEMORY_VAULT": os.path.join(self.tmp, "nope")})
        self.assertEqual(r.returncode, 0)

    def test_no_heartbeat_when_there_is_no_vault(self):
        self.run_once({"AGENT_MEMORY_VAULT": os.path.join(self.tmp, "nope")})
        self.assertFalse(os.path.exists(os.path.join(self.pool, "memory-heartbeat")))


if __name__ == "__main__":
    unittest.main()
