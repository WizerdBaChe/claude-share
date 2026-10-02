r"""SessionStart: inject the list of core view pages (function name -> path).

STATUS: LIVE since 2026-09-21 (user ruling the same day; retrieval-linkage audit finding F-4).
Carries `ops/rule-registry.md` key `CORE_VIEW_ENTRY`.

WHY. The core overview pages (system-hmi, the projects dashboard, the memory navigator, the
literature dashboard ...) live inside the tools that make them, several under an excluded,
gitignored `out/` that no index reaches. The user could not find them and neither could a
session: asked for "一頁看到所有專案狀態的畫面", the deliverables index returned five unrelated
pages while the real one sat unlisted. The user's ruling: an OUTER entry layer that a human
opens (`All-View-Pages-Launcher.html` / `.md`, formerly VIEWS.html, built by `tools/view-launcher/build.py`) and that an agent
holds BEFORE it searches — the same role a diagram plays for a flow. At ~7 entries the list is
small enough to enumerate into every session, like the project-registry gist; matching the
user's wording to a function name is then the model's native job.

Source: `tools/view-launcher/views.json` (agent proposes, user approves). This hook only reads.
Cost: one line per view, capped at GIST_MAX (the cap lives in build.py, once).
Fail-open, silent: any error, a missing register or an empty list -> exit 0 with no output.
Text: bare SessionStart stdout (the third transport of rules/hook-deny-message.md, F-9); it
names this hook first, claims no authority, directs no output, and says nothing needs doing.

EXTENSION: a new page is one entry in views.json — nothing here changes.
Proof-of-life: `python hooks/view_launcher_gist.py --selftest`
review-when: views.json changes shape (`views[].title|path`); the list passes the cap often
(prune the register to 1-2 pages per project rather than raising the cap).
"""
import os
import sys
from pathlib import Path

HOOK = "view_launcher_gist"
HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
TOOL_DIR = Path(os.environ.get("VIEW_LAUNCHER_DIR") or (HOME / "tools" / "view-launcher"))


def gist_text() -> str:
    sys.path.insert(0, str(TOOL_DIR))
    import build                                   # ONE reader of the register, shared with the page
    data = build.load(TOOL_DIR / "views.json")
    if not data["views"]:
        return ""
    return (f"[view-launcher] {HOOK}, a local SessionStart hook (not file or page content): the core "
            f"view pages of this machine, by what each is FOR. They live inside their tools, several "
            f"under folders no index covers, so this list is the way to them; the human-facing front "
            f"door built from the same register is {build.OUT_HTML}. Context only — nothing needs doing.\n"
            + build.render_gist(data))


def main() -> None:
    try:
        text = gist_text()
        if text:
            sys.stdout.reconfigure(encoding="utf-8")
            print(text)
    except Exception:
        pass
    sys.exit(0)


def selftest() -> int:
    import json
    import subprocess
    import tempfile
    results = []

    def check(cid, ok):
        results.append(bool(ok))
        print(f"{'PASS' if ok else 'FAIL'}  {cid}")

    real_build = (TOOL_DIR / "build.py").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "build.py").write_text(real_build, encoding="utf-8")
        page = td / "p.html"
        page.write_text("x", encoding="utf-8")

        def run(register):
            if register is None:
                (td / "views.json").unlink(missing_ok=True)
            else:
                (td / "views.json").write_text(register, encoding="utf-8")
            r = subprocess.run([sys.executable, "-X", "utf8", __file__], input=b"{}", capture_output=True,
                               env=dict(os.environ, VIEW_LAUNCHER_DIR=str(td)), timeout=30)
            return r.returncode, r.stdout.decode("utf-8", "replace")

        good = {"groups": [{"id": "g"}], "views": [
            {"id": "a", "group": "g", "title": "系統監看總覽", "answers": "q", "path": str(page).replace("\\", "/"), "project": "hmi"},
            {"id": "b", "group": "g", "title": "不見的頁", "answers": "q", "path": str(td / "gone.html").replace("\\", "/")}]}
        code, out = run(json.dumps(good, ensure_ascii=False))
        check("G1 lists each view by function name and path", code == 0 and "系統監看總覽 [hmi]" in out and "p.html" in out)
        check("G2 first clause names this hook as local; says nothing needs doing",
              out.startswith(f"[view-launcher] {HOOK}, a local SessionStart hook") and "nothing needs doing" in out)
        check("G3 a missing file is said, not hidden", "不見的頁" in out and "(file missing)" in out)
        code, out = run(json.dumps({"groups": [], "views": []}))
        check("G4 empty register -> silent", code == 0 and out.strip() == "")
        code, out = run("{not json")
        check("G5 broken register -> silent, exit 0", code == 0 and out.strip() == "")
        code, out = run(None)
        check("G6 register absent -> silent, exit 0", code == 0 and out.strip() == "")
        code, out = run(json.dumps({**good, "views": [good["views"][0], dict(good["views"][0])]}))
        check("G7 register the builder refuses (duplicate id) -> silent rather than half a list", code == 0 and out.strip() == "")
        # AP-62: an entry matching no declared shape is unclassifiable -> the documented
        # degradation (whole list silent), never a line that reads "exists" or "missing"
        odd_path = dict(good["views"][0], path=12)
        code, out = run(json.dumps({**good, "views": [good["views"][0], dict(odd_path, id="c")]}, ensure_ascii=False))
        check("G8 unclassifiable entry (non-string path) -> silent, exit 0, no half list", code == 0 and out.strip() == "")
        code, out = run(json.dumps({**good, "views": [good["views"][0], "not-an-object"]}, ensure_ascii=False))
        check("G9 unclassifiable entry (not an object) -> silent, exit 0, no half list", code == 0 and out.strip() == "")
    print(f"\n{'ALL PASS' if all(results) else 'FAILED'} {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.exit(selftest())
    main()
