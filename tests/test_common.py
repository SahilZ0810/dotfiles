import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(REPO, "scripts", "agent-memory", "common.sh")


def run_vault_root(home):
    """Source common.sh with a fake $HOME and print vault_root's result."""
    return subprocess.run(
        ["bash", "-c", f'. "{COMMON}"; vault_root'],
        env={**os.environ, "HOME": home},
        capture_output=True,
        text=True,
    )


class TestVaultRoot(unittest.TestCase):
    def test_finds_linux_vault(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "obsidian-vault", ".git"))
            r = run_vault_root(home)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), os.path.join(home, "obsidian-vault"))

    def test_finds_macos_vault(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "Documents", "Obsidian Vault", ".git"))
            r = run_vault_root(home)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), os.path.join(home, "Documents", "Obsidian Vault"))

    def test_prefers_linux_path_when_both_exist(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "obsidian-vault", ".git"))
            os.makedirs(os.path.join(home, "Documents", "Obsidian Vault", ".git"))
            r = run_vault_root(home)
            self.assertEqual(r.stdout.strip(), os.path.join(home, "obsidian-vault"))

    def test_fails_when_no_vault(self):
        with tempfile.TemporaryDirectory() as home:
            r = run_vault_root(home)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(r.stdout.strip(), "")

    def test_ignores_directory_without_git(self):
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "obsidian-vault"))  # no .git
            r = run_vault_root(home)
            self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
