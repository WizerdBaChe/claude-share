"""Gate one Agent-tool bench run from its subagent transcript.

usage: python judge_agent.py <agent_id> <workdir> <task> <rep> <duration_ms> <out.jsonl>

Environment: MB_SESSION_DIR = the dispatching session's transcript folder,
i.e. ~/.claude/projects/<project-slug>/<session-id>. Reads
$MB_SESSION_DIR/subagents/agent-<id>.jsonl, sums the per-message
usage of every assistant turn, takes the final assistant text as the result, writes it to
<workdir>/_result.txt and invokes `bench.py judge`.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SESSION_DIR = Path(os.environ["MB_SESSION_DIR"]).expanduser()
BENCH = Path(__file__).with_name("bench.py")

agent_id, workdir, task, rep, duration_ms, out = sys.argv[1:7]
tr = SESSION_DIR / "subagents" / f"agent-{agent_id}.jsonl"
inp = outp = cread = cwrite = think = 0
turns = 0
model = None
final_text = ""
for line in tr.read_text(encoding="utf-8").splitlines():
    try:
        j = json.loads(line)
    except json.JSONDecodeError:
        continue
    m = j.get("message") or {}
    if m.get("role") != "assistant":
        continue
    u = m.get("usage") or {}
    if u:
        turns += 1
        inp += int(u.get("input_tokens") or 0)
        outp += int(u.get("output_tokens") or 0)
        cread += int(u.get("cache_read_input_tokens") or 0)
        cwrite += int(u.get("cache_creation_input_tokens") or 0)
        think += int((u.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
    model = m.get("model") or model
    texts = [b.get("text", "") for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "text"]
    if texts:
        final_text = "\n".join(texts)
Path(workdir, "_result.txt").write_text(final_text, encoding="utf-8")
usage = {"input_tokens": inp, "output_tokens": outp, "cache_read_tokens": cread,
         "cache_creation_tokens": cwrite, "thinking_tokens": think, "num_turns": turns,
         "duration_ms": int(duration_ms)}
print(f"{task} r{rep} model={model} turns={turns} in={inp} out={outp} cread={cread} cwrite={cwrite} think={think}")
subprocess.run([sys.executable, "-X", "utf8", str(BENCH), "judge", "--task", task, "--workdir", workdir,
                "--result-file", str(Path(workdir, "_result.txt")), "--model", model or "claude-haiku-5-5",
                "--effort", "inherit", "--variant", "full", "--path", "agent", "--rep", rep,
                "--usage-json", json.dumps(usage), "--out", out], check=True)
