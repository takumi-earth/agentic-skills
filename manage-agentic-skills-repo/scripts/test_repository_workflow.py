"""Exercise the repository workflow against isolated, local Git remotes."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PULL = ("pull", "--no-rebase", "--no-autostash", "--ff", "--no-commit")
PUSH = ("push", "--no-follow-tags", "origin", "HEAD:refs/heads/main")


class RepositoryWorkflowTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / ".scratchpad"
        scratch.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix="repository-workflow-", dir=scratch
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.remote = self.root / "upstream.git"
        self.local = self.root / "local"
        self.peer = self.root / "peer"
        self.env = {
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.root, "clone", str(self.remote), str(self.local))
        self.configure(self.local)
        self.write(self.local, "shared.txt", "baseline\n")
        self.commit(self.local)
        self.git(self.local, *PUSH)
        self.git(self.root, "clone", str(self.remote), str(self.peer))
        self.configure(self.peer)

    def git(self, repository, *args, expected=0):
        result = subprocess.run(
            ["git", "-C", str(repository), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"git {args}: expected exit {expected}; received "
            f"{result.returncode}\n{result.stdout}\n{result.stderr}",
        )
        return result.stdout.strip()

    def configure(self, repository):
        self.git(repository, "config", "user.name", "Workflow Fixture")
        self.git(repository, "config", "user.email", "workflow@example.invalid")

    def write(self, repository, name, contents):
        (repository / name).write_text(contents, encoding="utf-8")

    def commit(self, repository):
        self.git(repository, "add", ".")
        self.git(
            repository,
            "commit",
            "-m",
            "test(workflow): record the complete fixture state\n\n"
            "Fixture state\n"
            "- Preserve the selected file contents\n"
            "- Include the complete staged fixture scope\n"
            "- Retain existing committed history",
        )
        return self.git(repository, "rev-parse", "HEAD")

    def assert_published(self, commit):
        self.git(self.local, "fetch", "origin")
        self.git(self.local, "merge-base", "--is-ancestor", commit, "@{upstream}")
        self.assertEqual(
            self.git(self.local, "rev-list", "--left-right", "--count", "HEAD...@{upstream}"),
            "0\t0",
        )
        self.assertEqual(self.git(self.remote, "rev-parse", "refs/heads/main"), commit)
        self.assertEqual(self.git(self.local, "status", "--porcelain"), "")

    def test_fast_forward_imports_changes_without_creating_a_merge(self):
        before = self.git(self.local, "rev-parse", "HEAD")
        self.write(self.peer, "remote.txt", "incoming content\n")
        incoming = self.commit(self.peer)
        self.git(self.peer, *PUSH)

        self.git(self.local, *PULL)

        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), incoming)
        self.git(self.local, "merge-base", "--is-ancestor", before, incoming)
        self.assertEqual((self.local / "remote.txt").read_text(), "incoming content\n")
        self.assertFalse((self.local / ".git" / "MERGE_HEAD").exists())
        self.assertEqual(self.git(self.local, "status", "--porcelain"), "")

    def test_divergent_commits_merge_and_publish_without_rewriting_either_history(self):
        self.write(self.local, "local.txt", "local content\n")
        original_local = self.commit(self.local)
        self.write(self.peer, "remote.txt", "incoming content\n")
        original_remote = self.commit(self.peer)
        self.git(self.peer, *PUSH)

        self.git(self.local, *PULL)

        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), original_local)
        self.assertTrue((self.local / ".git" / "MERGE_HEAD").exists())
        self.assertEqual((self.local / "local.txt").read_text(), "local content\n")
        self.assertEqual((self.local / "remote.txt").read_text(), "incoming content\n")
        self.assertEqual(self.git(self.local, "diff", "--name-only", "--diff-filter=U"), "")
        merged = self.commit(self.local)
        for predecessor in (original_local, original_remote):
            self.git(self.local, "merge-base", "--is-ancestor", predecessor, merged)
        self.git(self.local, *PUSH)
        self.assert_published(merged)

    def test_rejected_push_preserves_changes_and_succeeds_after_pulling_incoming_commits(self):
        self.write(self.local, "local.txt", "local content\n")
        original_local = self.commit(self.local)
        self.write(self.peer, "remote.txt", "concurrent content\n")
        original_remote = self.commit(self.peer)
        self.git(self.peer, *PUSH)

        self.git(self.local, *PUSH, expected=1)

        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), original_local)
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), original_remote)
        self.assertEqual((self.local / "local.txt").read_text(), "local content\n")
        self.git(self.local, *PULL)
        merged = self.commit(self.local)
        self.git(self.local, *PUSH)
        for predecessor in (original_local, original_remote):
            self.git(self.local, "merge-base", "--is-ancestor", predecessor, merged)
        self.assert_published(merged)

    def test_incompatible_edits_remain_visible_without_an_automatic_commit_or_push(self):
        self.write(self.local, "shared.txt", "local intent\n")
        original_local = self.commit(self.local)
        self.write(self.peer, "shared.txt", "remote intent\n")
        original_remote = self.commit(self.peer)
        self.git(self.peer, *PUSH)

        self.git(self.local, *PULL, expected=1)

        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), original_local)
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), original_remote)
        self.assertEqual(
            self.git(self.local, "diff", "--name-only", "--diff-filter=U"),
            "shared.txt",
        )
        conflicted = (self.local / "shared.txt").read_text()
        self.assertIn("local intent", conflicted)
        self.assertIn("remote intent", conflicted)
        self.assertTrue((self.local / ".git" / "MERGE_HEAD").exists())


if __name__ == "__main__":
    unittest.main()
