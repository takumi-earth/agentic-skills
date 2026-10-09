"""Independent source-install lifetime and platform runtime shutdown; no Codex patches."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback


HOME = str(Path.home())
NAMES = {"codex", "codex-code-mode-host", "logs_client", "bwrap", "codex.exe", "codex-code-mode-host.exe", "logs_client.exe", "codex-command-runner.exe", "codex-windows-sandbox-setup.exe"}


def display(value):
    if isinstance(value, str):
        return value.replace(HOME + "/", "~/").replace(HOME + "\\", "~/")
    if isinstance(value, list):
        return [display(item) for item in value]
    if isinstance(value, dict):
        return {key: display(item) for key, item in value.items()}
    return value


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(".next")
    temporary.write_text(json.dumps(display(value), indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def launch(manifest):
    manifest = Path(manifest).expanduser().resolve()
    with (manifest.parent / "supervisor.log").open("ab", buffering=0) as log:
        settings = {"start_new_session": True} if os.name != "nt" else {
            "creationflags": subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_BREAKAWAY_FROM_JOB
        }
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "run", str(manifest)],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, **settings,
        )
    print(json.dumps({"supervisor_pid": child.pid}))


def supervise(manifest):
    manifest = Path(manifest).expanduser().resolve()
    invocation = json.loads(manifest.read_text(encoding="utf-8"))
    command = [str(Path(item).expanduser()) if item.startswith("~/") else item
               for item in invocation["command"]]
    started = time.monotonic()
    environment = dict(os.environ, CODEX_SOURCE_INSTALL_WORKER=invocation["nonce"])
    child = subprocess.Popen(
        command, cwd=Path(invocation["cwd"]).expanduser(), env=environment,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    failures = []

    def drain(stream, name):
        try:
            with (manifest.parent / name).open("w", encoding="utf-8") as output:
                for line in iter(stream.readline, b""):
                    output.write(display(line.decode("utf-8", errors="replace")))
                    output.flush()
        except BaseException as error:
            failures.append(str(error))
            child.terminate()
        finally:
            stream.close()

    readers = [threading.Thread(target=drain, args=(stream, name))
               for stream, name in [(child.stdout, "stdout.log"), (child.stderr, "stderr.log")]]
    for reader in readers:
        reader.start()
    cancelled = False
    while child.poll() is None:
        if not cancelled and (manifest.parent / "cancel").exists():
            cancelled = True
            if os.name == "nt":
                child.terminate()
            else:
                child.send_signal(signal.SIGINT)
        time.sleep(0.1)
    for reader in readers:
        reader.join()
    code = child.returncode
    atomic_json(manifest.parent / "result.json", {
        **invocation, "supervisor_pid": os.getpid(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "native_return_code": code, "exit_status": 1 if failures else (code if code >= 0 else 128 - code),
        "stream_errors": failures,
    })


def linux_processes():
    processes = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            status = (directory / "status").read_text()
            uid = int(next(line for line in status.splitlines() if line.startswith("Uid:")).split()[1])
            if uid != os.getuid():
                continue
            fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] == "Z":
                continue
            try:
                executable = os.readlink(directory / "exe").removesuffix(" (deleted)")
            except PermissionError:
                name = next(line for line in status.splitlines() if line.startswith("Name:")).split()[1]
                if name in {value[:15] for value in NAMES}:
                    raise RuntimeError(f"cannot identify executable of Codex process {directory.name}")
                executable = ""
            processes.append({"pid": int(directory.name), "parent": int(fields[1]),
                              "created": fields[19], "executable": executable})
        except (FileNotFoundError, ProcessLookupError):
            continue
    return processes


def mac_processes():
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    library.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    library.proc_pidpath.restype = ctypes.c_int
    output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,uid=,lstart="], text=True)
    processes = []
    for line in output.splitlines():
        pid, parent, uid, created = line.strip().split(maxsplit=3)
        if int(uid) != os.getuid():
            continue
        buffer = ctypes.create_string_buffer(4096)
        if library.proc_pidpath(int(pid), buffer, len(buffer)) > 0:
            processes.append({"pid": int(pid), "parent": int(parent), "created": created,
                              "executable": os.fsdecode(buffer.value)})
    return processes


WINDOWS_QUERY = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
@((Get-CimInstance Win32_Process) | ForEach-Object {
    $p = $_
    if ($p.ExecutablePath) {
        $owner = Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
        if ($owner.ReturnValue -eq 0 -and $owner.Sid -eq $sid) {
            @{pid=[int]$p.ProcessId; parent=[int]$p.ParentProcessId;
              created=$p.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString(); executable=$p.ExecutablePath}
        }
    }
}) | ConvertTo-Json -Compress
"""


def windows_processes():
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_QUERY],
        text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
    )
    value = json.loads(output or "[]")
    return value if isinstance(value, list) else [value]


def processes():
    if sys.platform == "linux":
        return linux_processes()
    if sys.platform == "darwin":
        return mac_processes()
    if os.name == "nt":
        return windows_processes()
    raise RuntimeError(f"unsupported runtime process platform: {sys.platform}")


def selected_processes(all_processes, roots, excluded):
    resolved = [os.path.normcase(str(Path(root).expanduser().resolve())) for root in roots]
    selected = {}
    for process in all_processes:
        executable = os.path.normcase(process["executable"])
        if (process["pid"] not in excluded and Path(executable).name in NAMES
                and any(executable.startswith(root + os.sep) for root in resolved)):
            selected[process["pid"]] = process
    while True:
        children = [process for process in all_processes if process["pid"] not in excluded
                    and process["pid"] not in selected and process["parent"] in selected]
        if not children:
            return list(selected.values())
        selected.update({process["pid"]: process for process in children})


def same_process(left, right):
    return left is not None and right is not None and all(left[key] == right[key] for key in ("pid", "created", "executable"))


def terminate(process, force):
    # Recheck complete process identity immediately before signalling. A reused
    # PID, or a process that exited meanwhile, is not the captured process.
    if os.name != "nt":
        current = next((item for item in processes() if item["pid"] == process["pid"]), None)
        if not same_process(current, process):
            return
        try:
            os.kill(process["pid"], signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:
            pass
        return
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x100000 | 0x1000 | 0x1, False, process["pid"])
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # The process exited before its handle could be opened.
            return
        raise ctypes.WinError(error)
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        # CIM_DATETIME retains microseconds; FILETIME retains 100-nanosecond ticks.
        if created // 10 != int(process["created"]) // 10:
            return
        image = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        if os.path.normcase(image.value) != os.path.normcase(process["executable"]):
            return
        if not kernel.TerminateProcess(handle, 0):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)


def stop_runtime(roots):
    initial = processes()
    excluded = {os.getpid()}
    # The independent installer and its supervisor must survive this handoff.
    parent = os.getppid()
    while parent and parent not in excluded:
        excluded.add(parent)
        item = next((item for item in initial if item["pid"] == parent), None)
        parent = item["parent"] if item else 0
    targets = selected_processes(initial, roots, excluded)
    captured = {item["pid"]: item for item in targets}
    signalled = set()
    started = time.monotonic()
    while targets:
        force = os.name == "nt" or time.monotonic() - started >= 5
        for target in targets:
            identity = (target["pid"], target["created"], force)
            if identity in signalled:
                continue
            print(json.dumps(display({"phase": "stop-runtime", "process": target, "force": force})), file=sys.stderr, flush=True)
            terminate(target, force)
            signalled.add(identity)
        time.sleep(0.1)
        current = processes()
        survivors = [item for item in current if same_process(captured.get(item["pid"]), item)]
        targets = list({item["pid"]: item for item in survivors + selected_processes(current, roots, excluded)}.values())
        captured.update({item["pid"]: item for item in targets})
        if time.monotonic() - started >= 30:
            raise RuntimeError(f"runtime processes still present after shutdown: {display(targets)}")
    return {"status": "stopped", "processes": list(captured.values()), "remaining": []}


def main():
    mode, *arguments = sys.argv[1:]
    if mode == "launch":
        launch(arguments[0])
    elif mode == "run":
        try:
            supervise(arguments[0])
        except BaseException as error:
            atomic_json(Path(arguments[0]).parent / "result.json", {"exit_status": 1, "error": str(error)})
            raise
    elif mode == "stop":
        print(json.dumps(display(stop_runtime(arguments))))
    elif mode == "inspect":
        print(json.dumps(display({"processes": selected_processes(processes(), arguments, set())})))
    else:
        raise RuntimeError(f"unknown source installer operation: {mode}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(display(traceback.format_exc()), file=sys.stderr)
        sys.exit(1)
