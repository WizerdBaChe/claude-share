"""pid-carrying lock, dead-pid reclaim (INV-11: single collector)."""
import json
import os
import time
from pathlib import Path


def _pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return False
            try:
                code = ctypes.c_ulong()
                if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return None
                return code.value == 259  # STILL_ACTIVE
            finally:
                k32.CloseHandle(handle)
        except Exception:
            return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return None


def acquire(lock_path):
    """(ok, info). ok=False with the holder's info when a live pid holds the lock."""
    lock_path = Path(lock_path)
    if lock_path.exists():
        try:
            info = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            info = {}
        pid = info.get("pid")
        alive = _pid_alive(pid)
        if alive:
            return False, info
        # dead or undeterminable-but-absent pid -> reclaim below
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    info = {"pid": os.getpid(), "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    lock_path.write_text(json.dumps(info), encoding="utf-8")
    return True, info


def release(lock_path):
    try:
        Path(lock_path).unlink()
    except FileNotFoundError:
        pass
