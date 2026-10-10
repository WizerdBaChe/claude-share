r"""Two-sided calibration for tools/hook-backtest (harness, adapters, CLI).

    python -X utf8 tools/hook-backtest/tests/test_harness.py

Every behaviour is pinned by a case that must hold AND a case that must not:
a dedupe that never merges, a record filter that never drops, a redactor that
never masks, or an adapter that never fires would all pass a one-sided suite.
Adapter cases run against the LIVE hooks (harness.HOOKS_DIR), so a hook whose
main() changed shape under its adapter fails here, not silently in a rate.
Fixtures are synthetic transcripts written to a temp dir; the token in them is
cred-sweep's own self-test shape, not a real value.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import harness as hb  # noqa: E402
import adapters  # noqa: E402
import hook_backtest  # noqa: E402

RESULTS = []
FAKE_TOKEN = "ghp_" + "a1B2" * 9          # cred-sweep SELFTEST_POS github-token shape


def check(name, ok, detail=""):
    RESULTS.append((bool(ok), name, detail))


def rec(tool, inp, ts="2026-10-01T10:00:00Z", rtype="assistant", sid="sess-aaaa", tid="toolu_1"):
    return json.dumps({"type": rtype, "timestamp": ts, "sessionId": sid,
                       "message": {"content": [{"type": "tool_use", "id": tid,
                                                "name": tool, "input": inp}]}})


def write_corpus(root, lines, name="sess-aaaa.jsonl", proj="proj-x"):
    d = os.path.join(root, proj)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


tmp = tempfile.mkdtemp(prefix="hook-backtest-test-")
try:
    # ---------------------------------------------------------------- dedupe
    root = os.path.join(tmp, "dedupe")
    write_corpus(root, [
        rec("Bash", {"command": "ls"}),                                  # 1
        rec("Bash", {"command": "ls"}),                                  # same ts: rewrite
        rec("Bash", {"command": "ls"}, ts="2026-10-02T10:00:00Z"),       # retyped later
        "not json at all",
        rec("Bash", {"command": "ls"}, rtype="user"),                    # not assistant
    ])
    n_ts = len(list(hb.iter_calls([root], dedupe=hb.key_ts_head)))
    n_ct = len(list(hb.iter_calls([root], dedupe=hb.key_content)))
    n_no = len(list(hb.iter_calls([root], dedupe=None)))
    check("D1 ts-head merges a same-ts rewrite, keeps a later retype (2)", n_ts == 2, n_ts)
    check("D2 content merges the later retype too (1)", n_ct == 1, n_ct)
    check("D3 no dedupe keeps all three assistant calls (3)", n_no == 3, n_no)
    n_all = len(list(hb.iter_calls([root], dedupe=None, assistant_only=False)))
    check("R1 assistant_only=False also counts the user-typed record (4)", n_all == 4, n_all)

    corpus = hb.Corpus()
    list(hb.iter_calls([root, os.path.join(tmp, "absent")], corpus=corpus, on_missing=None))
    check("C1 corpus counts files, days, missing roots",
          corpus.files == 1 and corpus.days == {"2026-10-01", "2026-10-02"}
          and corpus.missing == [os.path.join(tmp, "absent")], (corpus.files, corpus.days))

    # ------------------------------------------------------ tool filter + locator
    root = os.path.join(tmp, "loc")
    write_corpus(root, [rec("Read", {"file_path": "a.txt"}),
                        rec("Bash", {"command": "echo " + FAKE_TOKEN}, tid="toolu_X")])
    calls = list(hb.iter_calls([root], tools=["Bash"]))
    check("F1 tool filter keeps only the named tool", [c.tool for c in calls] == ["Bash"])
    c = calls[0]
    check("L1 locator = project/file:line of the record",
          c.locator == "proj-x/sess-aaaa.jsonl:2" and c.session == "sess-aaaa"
          and c.tool_use_id == "toolu_X", c.locator)
    check("L2 locator carries no input text", FAKE_TOKEN not in c.locator and "echo" not in c.locator)

    # -------------------------------------------------------------- redaction
    ex = hb.excerpt(c, 200)
    check("X1 positive control: a token-shaped value is masked",
          FAKE_TOKEN not in ex and "<redacted:github-token>" in ex, ex)
    benign = hb.Call("", "Bash", {"command": "git   status  --short"}, "p", 1, "s", "proj", "")
    check("X2 negative control: a benign command passes unchanged (whitespace collapsed)",
          hb.excerpt(benign, 200) == "git status --short", hb.excerpt(benign, 200))
    saved = hb._REDACTOR
    hb._REDACTOR = None
    real = hb._patterns
    hb._patterns = lambda: (_ for _ in ()).throw(ImportError("gone"))
    try:
        ex2 = hb.excerpt(c, 200)
    finally:
        hb._patterns, hb._REDACTOR = real, saved
    check("X3 fail-closed: no redactor -> text withheld, never raw",
          FAKE_TOKEN not in ex2 and ex2.startswith("<excerpt withheld"), ex2)

    # ------------------------------------------- adapters vs the LIVE hooks
    sp = adapters.secret_print
    check("A1 secret_print: bare `printenv` -> env-dump", sp("Bash", {"command": "printenv"}) == "env-dump")
    check("A2 secret_print: one named variable passes", sp("Bash", {"command": "printenv HOME"}) is None)
    check("A3 secret_print: content grep for a key in a config file -> cred-grep",
          sp("Bash", {"command": "grep -n password app.yaml"}) == "cred-grep")
    check("A4 secret_print: -l (names only) passes",
          sp("Bash", {"command": "grep -l password app.yaml"}) is None)
    check("A5 secret_print: Grep tool content mode -> cred-grep",
          sp("Grep", {"pattern": "api_key", "path": "conf/app.json", "output_mode": "content"}) == "cred-grep")
    check("A6 secret_print: Grep tool files_with_matches passes",
          sp("Grep", {"pattern": "api_key", "path": "conf/app.json",
                      "output_mode": "files_with_matches"}) is None)
    # A pair, or A7 is vacuous: the same dump must fire WITHOUT the marker.
    check("A7a secret_print: a dump followed by another line still fires",
          sp("Bash", {"command": "printenv\necho ok"}) == "env-dump")
    check("A7b secret_print: ...and the OVERRIDE marker on that line passes it",
          sp("Bash", {"command": "printenv\necho '[user-approved-secret-read]'"}) is None)

    pe = adapters.ps_errorpref
    check("A8 ps_errorpref: EAP=Stop + bare git fires (hook suite T1)",
          pe("PowerShell", {"command": "$ErrorActionPreference = 'Stop'\ngit status --porcelain"}) == "fire")
    check("A9 ps_errorpref: git without EAP=Stop does not fire",
          pe("PowerShell", {"command": "git status --porcelain"}) is None)

    pp = adapters.ps_pipeline_close
    v = pp("PowerShell", {"command": "python fuzz.py --seed 7 | Select-Object -First 30"})
    check("A10 ps_pipeline_close: interpreter piped into -First fires (work tier)", v == "work", v)
    check("A11 ps_pipeline_close: capture-then-slice does not fire",
          pp("PowerShell", {"command": "$out = & python x.py; $out | Select-Object -First 30"}) is None)

    # ------------------------------------------------------------- CLI e2e
    root = os.path.join(tmp, "cli")
    write_corpus(root, [rec("Bash", {"command": "printenv"}),
                        rec("Bash", {"command": "export T=" + FAKE_TOKEN + "; printenv"},
                            ts="2026-10-01T11:00:00Z", tid="toolu_2"),
                        rec("Bash", {"command": "ls"}, ts="2026-10-01T12:00:00Z")])
    dump = os.path.join(tmp, "fires.json")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = hook_backtest.main(["adapters:secret_print", "--root", root, "--json", dump])
    text = out.getvalue()
    check("E1 CLI counts 2 fires of 3 calls", rc == 0 and "FIRES  : 2 / 3" in text, text[-300:])
    check("E2 CLI output without --excerpt carries no command text",
          FAKE_TOKEN not in text and "printenv" not in text.split("== fires")[1])
    rows = json.load(io.open(dump, encoding="utf-8"))
    check("E3 JSON dump: locators only, no token, no excerpt key",
          len(rows) == 2 and all("excerpt" not in r for r in rows)
          and FAKE_TOKEN not in json.dumps(rows), rows[:1])
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        hook_backtest.main(["adapters:secret_print", "--root", root, "--excerpt", "80"])
    check("E4 CLI --excerpt is redacted", FAKE_TOKEN not in out.getvalue()
          and "<redacted:github-token>" in out.getvalue())
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = hook_backtest.main(["adapters:secret_print", "--root", os.path.join(tmp, "nothing-here")])
    check("E5 CLI: no calls matched -> exit 2, not '0 fires'", rc == 2, rc)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

bad = [r for r in RESULTS if not r[0]]
for ok, name, detail in RESULTS:
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "   -> %r" % (detail,)))
print("\n%d/%d passed" % (len(RESULTS) - len(bad), len(RESULTS)))
sys.exit(1 if bad else 0)
