# Tool-boundary probes — run by hand, and here is why

These five probes cannot be scripted. The defects they test live in **Claude
Code's tool transport**, which only exists when the model issues a tool call.
A Python script invoking `subprocess.run(["bash", "-c", cmd])` reaches bash
without crossing that boundary and will report everything as healthy — a
convincing false negative.

So this file is a runbook, not a test suite. Each probe is one tool call with
its result recorded from **2026-08-19, Claude Code 2.1.233**. Run them, diff
against the recorded output, and if anything differs the conclusions in
`ops/lessons.md` L-024 and CLAUDE.md's Environment bullets 1–2 are in question.

Whole set takes about a minute. `invariants.py` and `sweep.py` cover everything
that *can* be automated; this covers what cannot.

---

## P1 — Backslash collapse (the load-bearing one)

**Bash tool:**

```
cat > "$TMP/r1a.txt" <<'EOF'
01|\|
02|\\|
03|\\\|
04|\\\\|
05|\\\\\|
06|\\\\\\|
07|\n|
15|C:\Users\alice|
16|C:\\Users\\alice|
EOF
python - <<'PYEOF'
d=open('<path>/r1a.txt','rb').read()
for L in d.split(bytes([10])):
    if L: print(L[:2].decode(), 'len=%d' % len(L[3:-1]), L[3:-1].hex())
PYEOF
```

Recorded (hex, so the display layer cannot lie):

| tag | bytes | meaning |
|---|---|---|
| 01 | `5c` | 1 -> 1 |
| 02 | `5c` | **2 -> 1** |
| 03 | `5c5c` | **3 -> 2** |
| 04 | `5c5c` | **4 -> 2** |
| 05 | `5c5c5c` | **5 -> 3** |
| 06 | `5c5c5c` | **6 -> 3** |
| 07 | `5c6e` | `\n` untouched |
| 15 | 14 bytes | single backslashes untouched |
| 16 | 14 bytes | **`\\` halved** |

Rule: a run of n becomes `ceil(n/2)`; a backslash before a non-backslash is untouched.

**Controls that must stay clean** — same content through the **PowerShell tool**
(`[IO.File]::WriteAllText`) and through the **Write tool**: both recorded
`1, 2, 3, 4` unchanged. If a control now collapses too, the routing rule
(CLAUDE.md Environment bullet 1) loses its basis and must be re-argued.

**Read-back is faithful** — `cat` and `od -c` of a file containing real `\\`
show `\\`. The corruption is input-only, which is why reading the written bytes
back is a valid check and trusting the exit code is not.

---

## P2 — Which Windows-path spellings survive (Bash tool)

```
ls 'C:\Users\alice\.claude\ops'       # recorded: OK
ls "C:\Users\alice\.claude\ops"       # recorded: OK
ls C:\Users\alice\.claude\ops         # recorded: FAIL rc=2, program received C:Usersaliceops
ls "C:\Users\alice\.claude\ops\"      # recorded: exit 2, bash: eval: line 1: unexpected EOF
ls /c/Users/alice/.claude/ops         # recorded: OK
```

The fourth is the trap: a trailing backslash escapes the closing quote, so the
command never runs. Note the `eval:` prefix — a different code path from the
size-ceiling failures, which say `-c:`.

---

## P3 — Size ceiling

Not a hand probe: `sweep.py` measures it from the corpus, which is stronger than
one synthetic command.

```
python sweep.py --since <10 days ago>
```

Recorded 2026-08-19: largest SUCCESSFUL Bash command **7,688 B**; every call at
or above **7,700 B** failed (7 of 7), all with `unexpected EOF` pointing at an
arbitrary line of a heredoc body. PowerShell succeeded at 8,053 B.

**Open**: the attribution to `cmd.exe`'s 8,191-character limit is INFERENCE. The
bracket is measured; the cause is not. One padded probe would settle it — a
Bash command of ~8,150 B whose padding sits in a `#` comment (parse-safe under
truncation) ending in `echo END`. If END prints, the ceiling is above 8,150 and
the cmd.exe attribution stands.

---

## P4 — Line endings, per write path

Write the same three lines through each path, then count CR and LF bytes.

| path | recorded | note |
|---|---|---|
| **Edit tool** | preserves the file's existing ending | the ONLY one that does |
| Write tool | pure LF | overwriting a CRLF file converts the whole file |
| Bash heredoc `>` | pure LF | |
| Bash `cat >>` onto CRLF | **mixed** | this is how the two mixed files were made |
| PS `[IO.File]::WriteAllText` | pure LF | |
| PS `Set-Content` | LF body + one CRLF at end | |
| PS `Out-File` / `>` | LF body + CRLF end + **UTF-8 BOM** | |

`invariants.py` checks the *consequence* (zero mixed files in the repo)
automatically; this table is what explains it.

Also recorded: CJK, emoji, combining marks, zero-width space and full-width
characters all survive byte-exactly through the Bash tool. **The only thing that
gets eaten is backslashes.**

---

## P5 — PowerShell `$?` after a native exe writes stderr

```powershell
$py = "python.exe"; $c = "import sys; sys.stderr.write('warn'); sys.exit(0)"
$o = & $py -c $c 2>&1;                  $a = $?    # recorded: False
$o = & $py -c $c;                       $b = $?    # recorded: True
$o = & $py -c $c 2>$null;               $d = $?    # recorded: False
$o = cmd /c "... 2>&1";                 $f = $?    # recorded: True
```

**ANY** stderr redirection of a native exe that writes to stderr sets `$?` false
on exit 0 — `2>$null` is not a workaround. `cmd /c` is exempt.

Two things this probe is NOT evidence for, both established 2026-08-19:

- It does **not** make the tool report failure. The tool follows the exit code.
  A `2>&1` command that fails is failing for its own reasons.
- It **does** become a terminating error under `$ErrorActionPreference='Stop'`,
  which aborts the rest of the chain on a harmless warning. Combined with the
  fact that `EAP='Stop'` also misses a native non-zero exit, it is wrong in both
  directions for native executables — check `$LASTEXITCODE` instead.
