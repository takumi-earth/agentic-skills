"""Run the actual just i handoff with accepted native packages in isolated homes."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time


SCRIPT = Path(__file__).with_name("source_install.py")
spec = importlib.util.spec_from_file_location("source_install", SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def path(value):
    return Path(value).expanduser().resolve()


def link_directory(target, destination, bun):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run([bun, "--no-env-file", "-e",
                        "require('node:fs').symlinkSync(process.argv[1],process.argv[2],'junction')",
                        str(target), str(destination)], check=True)
    else:
        destination.symlink_to(target, target_is_directory=True)


def retain_file(source, destination):
    try:
        os.link(source, destination)
        return destination
    except OSError:
        return shutil.copy2(source, destination)


def command(argv, env, cwd, log, expected=0, during=None):
    print(f"native installer fixture: {runtime.display(argv)}", flush=True)
    started = time.monotonic()
    child = subprocess.Popen(argv, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    errors = []
    def intervene():
        try:
            during(child)
        except Exception as error:
            errors.append(error)
    intervention = threading.Thread(target=intervene) if during else None
    if intervention:
        intervention.start()
    stdout, stderr = child.communicate()
    if intervention:
        intervention.join()
    log.write(runtime.display(stdout + stderr))
    log.flush()
    if child.returncode != expected:
        raise AssertionError(f"expected exit {expected}, received {child.returncode}: {runtime.display(stderr)}")
    if errors:
        raise errors[0]
    return subprocess.CompletedProcess(argv, child.returncode, stdout, stderr), round(time.monotonic() - started, 3)


def probe(codex, env, repository, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run([str(codex), "app-server", "daemon", "version"], env=env, cwd=repository,
                                capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        time.sleep(0.1)
    raise AssertionError(f"server did not become ready: {runtime.display(result.stderr)}")


def case(name, args, scratch):
    extension = ".exe" if os.name == "nt" else ""
    old_metadata = json.loads((args.old_package / "codex-package.json").read_text())
    new_metadata = json.loads((args.new_package / "codex-package.json").read_text())
    assert old_metadata["version"] != new_metadata["version"], "upgrade fixture requires different versions"
    with tempfile.TemporaryDirectory(dir=scratch, prefix=f"native-{name}-") as directory:
        root = Path(directory)
        home = root / "runtime"
        cargo = root / "cargo"
        settings_file = home / "app-server-daemon" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings = {"featureOverrides": {"code_mode_host": True}, "remoteControlEnabled": False,
                    "shutdownGraceSeconds": 1, "updater": {"autoUpdateEnabled": False, "updateIntervalMinutes": 60}}
        settings_file.write_text(json.dumps(settings))
        environment = {**os.environ, "CODEX_HOME": str(home), "CARGO_HOME": str(cargo),
                       "CODEX_REPO_ROOT": str(args.repository), "CODEX_V8_REPO": str(args.v8_repository),
                       "AGENTIC_SKILLS_REPO": str(SCRIPT.parents[2]), "CODEX_V8_BUN": args.bun}
        environment.pop("CODEX_SOURCE_INSTALL_WORKER", None)
        old = home / "packages" / "app-server-daemon" / "releases" / "old-fixture"
        if name != "fresh":
            shutil.copytree(args.old_package, old, symlinks=True, copy_function=retain_file)
            link_directory(old, old.parent.parent / "current", args.bun)
        raw = None
        host = None
        reconnects = []
        log_path = scratch / f"native-{name}.log"
        with log_path.open("w", encoding="utf-8") as log:
            try:
                old_codex = old / "bin" / f"codex{extension}"
                if name == "registered":
                    command([str(old_codex), "app-server", "daemon", "restart"], environment, args.repository, log)
                elif name in ("missing-registration", "foreign", "concurrent-start"):
                    executable = old_codex
                    if name == "foreign":
                        foreign = root / "foreign package"
                        shutil.copytree(args.old_package, foreign, symlinks=True, copy_function=retain_file)
                        executable = foreign / "bin" / f"codex{extension}"
                    raw = subprocess.Popen([str(executable), "-c", "features.code_mode_host=true", "app-server", "--listen", "unix://"],
                                           env=environment, cwd=args.repository, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                before = None if name == "fresh" else probe(old_codex, environment, args.repository)
                if name == "missing-registration":
                    assert before.get("backend") is None, before
                    assert not (settings_file.parent / "daemon.pid").exists()
                if name not in ("fresh", "foreign"):
                    host = subprocess.Popen([str(old / "bin" / f"codex-code-mode-host{extension}")],
                                            env=environment, cwd=args.repository, stdin=subprocess.PIPE,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.1)
                    assert host.poll() is None, "old helper must be active before installation"
                if name == "missing-registration" and sys.platform == "linux":
                    # Require the real service to survive SIGTERM so this case
                    # also exercises forced exit and stale-socket startup.
                    os.kill(raw.pid, signal.SIGSTOP)
                roots = [home / "packages", cargo / "bin"]
                old_processes = runtime.selected_processes(runtime.processes(), roots, set())
                settings_before = settings_file.read_bytes()
                selected_before = (old.parent.parent / "current").resolve() if name != "fresh" else None
                argv = ["just", "--justfile", str(args.repository / "justfile"), "i",
                        "--entrypoint-bin", str(args.new_package / "bin" / f"codex{extension}"),
                        "--code-mode-host-bin", str(args.new_package / "bin" / f"codex-code-mode-host{extension}"),
                        "--logs-client-bin", str(args.new_package / "bin" / f"logs_client{extension}")]
                if sys.platform == "linux":
                    argv += ["--bwrap-bin", str(args.new_package / "codex-resources" / "bwrap")]
                # Agent preparation is optional; when present the user's exact
                # command must stay plain just i and discover this package.
                command(argv + ["--prepare-package"], environment, args.repository, log)
                ready = json.loads(next((home / "packages" / "standalone" / "prepared").glob("*.json")).read_text())
                assert ready["handoff"]["argv"] == ["just", "i"] and ready["handoff"]["command"] == "just i"
                assert settings_file.read_bytes() == settings_before
                argv = ["just", "--justfile", str(args.repository / "justfile"), "i"]
                def reconnect_during_selection(installer):
                    deadline = time.monotonic() + 30
                    attempts = home / "packages" / "standalone" / "source-install-attempts"
                    while time.monotonic() < deadline and installer.poll() is None:
                        for output in attempts.glob("*/stderr.log"):
                            for line in output.read_text().splitlines():
                                try:
                                    event = json.loads(line)
                                except ValueError:
                                    continue
                                if event.get("phase") == "package-selection" and event.get("status") == "begin":
                                    current_codex = home / "packages" / "standalone" / "current" / "bin" / f"codex{extension}"
                                    reconnects.append(subprocess.Popen([str(current_codex), "app-server", "--listen", "unix://"],
                                        env=environment, cwd=args.repository, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                                    return
                        time.sleep(0.02)
                    raise AssertionError("package-selection event was not observed for the reconnect fixture")
                installed, duration = command(argv, environment, args.repository, log, expected=1 if name == "foreign" else 0,
                                              during=reconnect_during_selection if name == "concurrent-start" else None)
                attempts = home / "packages" / "standalone" / "source-install-attempts"
                result = json.loads(next(attempts.glob("*/result.json")).read_text())
                assert result["exit_status"] == installed.returncode, result
                assert settings_file.read_bytes() == settings_before, "saved startup policy changed"
                if name == "foreign":
                    assert raw.poll() is None, "foreign endpoint owner was terminated"
                    assert (old.parent.parent / "current").resolve() == selected_before
                    assert not (home / "packages" / "standalone" / "source-install.json").exists()
                    assert "not managed" in installed.stderr
                    return {"case": name, "exit_status": 1, "duration_seconds": duration,
                            "foreign_pid": raw.pid, "foreign_owner_preserved": True, "outcome": result}
                receipt = json.loads((home / "packages" / "standalone" / "source-install.json").read_text())
                after = probe(path(receipt["package"]) / "bin" / f"codex{extension}", environment, args.repository)
                assert after["backend"] == "pid" and after["appServerVersion"] == new_metadata["version"], after
                current = runtime.processes()
                assert not any(runtime.same_process(previous, observed) for previous in old_processes for observed in current)
                if raw is not None:
                    raw.wait(timeout=5)
                if host is not None:
                    host.wait(timeout=5)
                for reconnect in reconnects:
                    reconnect.wait(timeout=5)
                assert receipt["runtime"]["executables"] and receipt["runtime"]["processes"]
                return {"case": name, "exit_status": 0, "duration_seconds": duration,
                        "before": before, "after": after, "old_processes": old_processes,
                        "old_processes_exited": True, "saved_settings_preserved": True,
                        "forced_shutdown": name == "missing-registration" and sys.platform == "linux",
                        "concurrent_start_exited": bool(reconnects),
                        "runtime": receipt["runtime"], "outcome": result}
            finally:
                runtime.stop_runtime([home / "packages", cargo / "bin"])
                for child in (raw, host, *reconnects):
                    if child is not None:
                        if child.poll() is None:
                            child.kill()
                        child.wait()
                        if child.stdin:
                            child.stdin.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=path, required=True)
    parser.add_argument("--v8-repository", type=path, required=True)
    parser.add_argument("--old-package", type=path, required=True)
    parser.add_argument("--new-package", type=path, required=True)
    parser.add_argument("--bun", default=shutil.which("bun"))
    parser.add_argument("--output", type=path, required=True)
    args = parser.parse_args()
    scratch = SCRIPT.parents[2] / ".scratchpad" / "upgrade-codex-patch" / "native-installer-repair"
    scratch.mkdir(parents=True, exist_ok=True)
    results = [case(name, args, scratch) for name in ("registered", "missing-registration", "fresh", "concurrent-start", "foreign")]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    runtime.atomic_json(args.output, {"platform": sys.platform, "cases": results})
    print(json.dumps({"status": "passed", "cases": [result["case"] for result in results], "evidence": runtime.display(str(args.output))}))


if __name__ == "__main__":
    main()
