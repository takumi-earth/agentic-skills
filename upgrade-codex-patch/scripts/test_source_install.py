"""Exercise detached outcomes and real scoped process shutdown without a live Codex restart."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).with_name("source_install.py")
spec = importlib.util.spec_from_file_location("source_install", SCRIPT)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
SCRATCH = SCRIPT.parents[2] / ".scratchpad" / "upgrade-codex-patch"


def wait_for(path, timeout=15):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise AssertionError(f"missing completed outcome: {worker.display(str(path))}")
        time.sleep(0.05)
    return json.loads(path.read_text())


class SourceInstallTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=SCRATCH, prefix="source-install-test-")
        self.root = Path(self.directory.name)
        self.children = []

    def tearDown(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
            child.wait()
        self.directory.cleanup()

    def invocation(self, body):
        manifest = self.root / "invocation.json"
        worker.atomic_json(manifest, {"nonce": "fixture", "command": [sys.executable, "-c", body], "cwd": str(self.root)})
        return manifest

    def launch(self, manifest):
        result = subprocess.run([sys.executable, str(SCRIPT), "launch", str(manifest)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_failed_child_keeps_native_exit_and_both_streams(self):
        manifest = self.invocation("import sys; print('outcome'); print('diagnostic',file=sys.stderr); sys.exit(17)")
        self.launch(manifest)
        result = wait_for(self.root / "result.json")
        self.assertEqual((result["exit_status"], result["native_return_code"], result["stream_errors"]), (17, 17, []))
        self.assertEqual((self.root / "stdout.log").read_text(), "outcome\n")
        self.assertEqual((self.root / "stderr.log").read_text(), "diagnostic\n")

    def test_large_pipes_and_final_partial_utf8_are_drained(self):
        manifest = self.invocation("import sys; sys.stdout.write('α'*100000+'end'); sys.stderr.write('β'*100000+'tail')")
        self.launch(manifest)
        result = wait_for(self.root / "result.json")
        self.assertEqual(result["exit_status"], 0)
        self.assertEqual((self.root / "stdout.log").read_text(), "α" * 100000 + "end")
        self.assertEqual((self.root / "stderr.log").read_text(), "β" * 100000 + "tail")

    @unittest.skipIf(os.name == "nt", "launch-parent signal fixture uses Unix session signals")
    def test_installation_survives_the_launching_session_exit(self):
        manifest = self.invocation("import time; time.sleep(.4); print('completed after parent exit')")
        parent = subprocess.Popen([sys.executable, "-c",
            "import subprocess,sys,time; subprocess.run([sys.executable,sys.argv[1],'launch',sys.argv[2]],check=True); print('launched',flush=True); time.sleep(30)",
            str(SCRIPT), str(manifest)], stdout=subprocess.PIPE, text=True, start_new_session=True)
        self.children.append(parent)
        self.assertIsNotNone(json.loads(parent.stdout.readline())["supervisor_pid"])
        self.assertEqual(parent.stdout.readline().strip(), "launched")
        os.killpg(parent.pid, 15)
        parent.wait()
        parent.stdout.close()
        result = wait_for(self.root / "result.json")
        self.assertEqual(result["exit_status"], 0)
        self.assertEqual((self.root / "stdout.log").read_text(), "completed after parent exit\n")

    def test_selection_preserves_unrelated_roots_and_tracks_runtime_descendants(self):
        scope = self.root / "runtime packages"
        records = [
            {"pid": 10, "parent": 1, "created": "a", "executable": str(scope / "old" / "bin" / "codex")},
            {"pid": 11, "parent": 10, "created": "b", "executable": "/usr/bin/node"},
            {"pid": 12, "parent": 1, "created": "c", "executable": str(self.root / "unrelated" / "codex")},
            {"pid": 13, "parent": 1, "created": "d", "executable": str(scope / "old" / "bin" / "codex-code-mode-host")},
        ]
        self.assertEqual({value["pid"] for value in worker.selected_processes(records, [scope], set())}, {10, 11, 13})
        self.assertEqual(worker.selected_processes(records, [scope], {10, 13}), [])
        reparented = {**records[1], "parent": 1}
        self.assertTrue(worker.same_process(records[1], reparented))
        self.assertFalse(worker.same_process(records[1], {**reparented, "created": "replacement"}))

    @unittest.skipUnless(sys.platform == "linux", "native Linux process fixture")
    def test_real_scoped_runtime_and_helper_stop_preserve_other_processes(self):
        owned = self.root / "runtime packages"
        unrelated = self.root / "unrelated runtime"
        owned.mkdir()
        unrelated.mkdir()
        for directory, name in [(owned, "codex"), (owned, "codex-code-mode-host"), (unrelated, "codex")]:
            destination = directory / name
            shutil.copy2(shutil.which("sleep"), destination)
            self.children.append(subprocess.Popen([str(destination), "30"]))
        time.sleep(0.05)
        stopped = worker.stop_runtime([owned])
        self.assertEqual(stopped["remaining"], [])
        self.assertEqual({value["pid"] for value in stopped["processes"]}, {child.pid for child in self.children[:2]})
        for child in self.children[:2]:
            self.assertEqual(child.wait(timeout=2), -15)
        self.assertIsNone(self.children[2].poll())

    @unittest.skipUnless(sys.platform == "linux", "native Linux forced-shutdown fixture")
    def test_forced_shutdown_removes_ignoring_runtime_and_its_child(self):
        owned = self.root / "runtime packages"
        owned.mkdir()
        executable = owned / "codex"
        shutil.copy2("/bin/bash", executable)
        marker = self.root / "signal-handler-ready.json"
        child = subprocess.Popen([str(executable), "-c",
            'trap "" TERM; sleep 30 & task_child=$!; printf \'{"child":%s}\' "$task_child" > "$1"; wait',
            "codex", str(marker)])
        self.children.append(child)
        ready = wait_for(marker)
        before = worker.selected_processes(worker.processes(), [owned], set())
        self.assertEqual({item["pid"] for item in before}, {child.pid, ready["child"]})
        stopped = worker.stop_runtime([owned])
        self.assertEqual(stopped["remaining"], [])
        self.assertEqual({item["pid"] for item in stopped["processes"]}, {item["pid"] for item in before})
        self.assertEqual(child.wait(timeout=2), -9)
        self.assertFalse(any(worker.same_process(old, current) for old in before for current in worker.processes()))


if __name__ == "__main__":
    unittest.main()
