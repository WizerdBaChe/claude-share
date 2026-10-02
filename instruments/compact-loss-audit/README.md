# compact-loss-audit

Judges recorded compactions for **handoff completeness** and **misleading-ness**, not token counts.
Recorder = `hooks/compact_loss_record.py` (PostCompact, every compaction, persists before any judgement).
Judge = `audit.py` (run at a natural pause; the PostCompact hook nudges every 5th auto compaction).

```powershell
python tools/compact-loss-audit/audit.py          # unaudited auto compactions
python tools/compact-loss-audit/audit.py --all    # include manual + re-audit
```

Output: `reports/<YYYY-MM-DD>-HHMM-compact-loss-audit.md` — one summary table + one packet per compaction
(summary text, handoff snapshot, pre/post turns, post-compact tool calls) with a 讀者裁定 block to fill.

Determinable checks (printed with evidence): C1 path coverage, C2 snapshot presence / deny-once,
M1 intake-gate touch before the first post-compact write, M2 user-correction phrases.
Everything else is forwarded to the reader — the tool never vetoes.

Severity: WARN, advisory. Calibrate before trusting: one known-bad and one known-good compaction
must score differently. Design: `references/compaction-pipeline-design.md` §4.4.
