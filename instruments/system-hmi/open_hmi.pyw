"""open_hmi.pyw -- windowless launcher for the LIVE system-hmi page (2026-09-22).

The live page (served by `hmi.py serve`) has the refresh buttons; the static out/mimic.html cannot
run anything. open-hmi.bat did the same job but left a console window open for the service's whole
life. This launcher runs under pythonw (no console at all):

  1. ask 127.0.0.1:8787/api/meta. A service that answers is REUSED ONLY IF the code it loaded equals
     the code on disk (hmi.server.code_fingerprint). A service from before a code change - or one too old
     to report its code - is stopped and replaced (2026-09-23: the shortcut kept showing the pre-change
     page because a service started earlier held the old template in memory). Only a process whose
     command line is `hmi.py serve` is ever stopped; anything else on the port is reported, not killed;
  2. if nothing answers, start `hmi.py serve --idle-exit 15` detached and windowless -- the service stops
     by itself 15 min after the page is closed (the page polls every 20 s), so nothing lingers;
  3. confirm the answering service runs the code on disk, then open the page in a Chrome app window
     (no address bar); the default browser if Chrome is absent.

Failures announce themselves in a message box, and the service's output goes to out/serve.log.
Stopping an old service does not stop a collect it had started: that child holds the collector lock
and finishes on its own. Started from the desktop shortcut 「系統監看（可重跑）」.
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

PORT = 8787
URL = f"http://127.0.0.1:{PORT}/"
TOOL = Path(__file__).resolve().parent
LOG = TOOL / "out" / "serve.log"
NO_WINDOW = 0x08000000

sys.path.insert(0, str(TOOL))
from hmi.server import code_fingerprint  # noqa: E402


def meta():
    """The service's /api/meta as a dict, or None when nothing answers."""
    try:
        with urllib.request.urlopen(URL + "api/meta", timeout=2) as r:
            return json.loads(r.read().decode("utf-8")) if r.status == 200 else None
    except (OSError, ValueError):
        return None


def needs_restart(m, disk):
    """A service that answers but whose loaded code is not the code on disk (or that does not report it)."""
    return m is not None and m.get("code") != disk


def fail(msg):
    ctypes.windll.user32.MessageBoxW(None, msg, "system-hmi", 0x10)
    sys.exit(1)


def ps(command):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=NO_WINDOW, timeout=20)
    return (r.stdout or "").strip()


def port_owner():
    out = ps(f"(Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue"
             " | Select-Object -First 1).OwningProcess")
    return int(out) if out.isdigit() else None


def is_hmi_serve(pid):
    cmd = ps(f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine")
    return "hmi.py" in cmd and " serve" in cmd


def stop_stale(m):
    pid = m.get("pid") or port_owner()
    if not pid:
        fail(f"{URL} 上有舊版服務，但找不到它的程序編號，無法換新。\n請關掉它後再開一次捷徑。")
    if not is_hmi_serve(pid):
        fail(f"連接埠 {PORT} 被另一個程式佔用（PID {pid}），不是 system-hmi 服務，所以沒有動它。")
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, creationflags=NO_WINDOW)
    for _ in range(40):
        time.sleep(0.25)
        if meta() is None:
            with open(LOG, "a", encoding="utf-8") as log:
                log.write(f"launcher: stopped stale service pid={pid} (code {m.get('code')} != disk)\n")
            return
    fail(f"舊版服務（PID {pid}）停不下來，所以沒辦法換新版。")


def start():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "a", encoding="utf-8")
    flags = 0x00000008 | NO_WINDOW | 0x00000200   # DETACHED | NO_WINDOW | NEW_PROCESS_GROUP
    subprocess.Popen([python_windowless(), "-X", "utf8", str(TOOL / "hmi.py"), "serve",
                      "--port", str(PORT), "--idle-exit", "15"],
                     cwd=str(TOOL), stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                     creationflags=flags, close_fds=True)
    for _ in range(40):
        time.sleep(0.25)
        m = meta()
        if m is not None:
            return m
    fail(f"system-hmi 服務沒有在 10 秒內回應 {URL}。\n詳細輸出：{LOG}")


def python_windowless():
    exe = Path(sys.executable)
    w = exe.with_name("pythonw.exe")
    return str(w if w.exists() else exe)


def chrome():
    import winreg
    key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, key) as k:
                path = winreg.QueryValue(k, None)
                if path and os.path.exists(path):
                    return path
        except OSError:
            continue
    return None


def main():
    disk = code_fingerprint(TOOL)
    m = meta()
    if needs_restart(m, disk):
        stop_stale(m)
        m = None
    if m is None:
        m = start()
    if m.get("code") != disk:
        fail(f"服務回報的程式版本（{m.get('code')}）和磁碟上的（{disk}）不一致，所以沒有打開頁面。\n詳細輸出：{LOG}")
    exe = chrome()
    if exe:
        subprocess.Popen([exe, f"--app={URL}", "--window-size=1500,900"],
                         creationflags=NO_WINDOW, close_fds=True)
    elif not webbrowser.open(URL):
        fail(f"找不到瀏覽器可開啟 {URL}")


if __name__ == "__main__":
    main()
