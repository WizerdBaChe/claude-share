"""Judge Agent-path round-5 runs (copy of round4-agent-judge.py, session path changed): result text + usage read from the subagent transcript.
usage: MB_SESSION_DIR=<transcript folder> python round5-agent-judge.py <r5agent dir> <results_*.json> <out runs.jsonl>"""
import json, os, subprocess, sys
from datetime import datetime

R4, RES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
# MB_SESSION_DIR = the dispatching session's transcript folder; subagent transcripts are in <it>/subagents/.
SUB = os.path.join(os.path.expanduser(os.environ["MB_SESSION_DIR"]), "subagents")
BENCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bench.py")
disp = {d["id"]: d for d in json.load(open(os.path.join(R4, "dispatch.json"), encoding="utf-8"))}
if RES.endswith(".json"):
    res = json.load(open(RES, encoding="utf-8"))
else:   # "### <id> <agentId>" header, raw text until the next header
    res, cur = {}, None
    for line in open(RES, encoding="utf-8").read().splitlines():
        if line.startswith("### "):
            rid, agent = line[4:].split()
            cur = res[rid] = {"agent": agent, "text": ""}
        elif cur is not None:
            cur["text"] += line + "\n"


def usage(agent):
    u = dict(input_tokens=0, output_tokens=0, cache_read_tokens=0, cache_creation_tokens=0,
             thinking_tokens=0, num_turns=0)
    ts, model, gold, last = [], None, False, {}
    for line in open(os.path.join(SUB, f"agent-{agent}.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r.get("timestamp"):
            ts.append(datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")))
        if ".gold.json" in line and r.get("type") == "user":
            gold = True        # a tool RESULT carrying the gold file name
        m = r.get("message") or {}
        if r.get("type") == "assistant" and isinstance(m, dict) and m.get("usage"):
            last[m.get("id")] = m["usage"]   # streamed chunks repeat; the LAST one is complete
            model = m.get("model") or model
    for us in last.values():
        u["input_tokens"] += us.get("input_tokens", 0)
        u["output_tokens"] += us.get("output_tokens", 0)
        u["cache_read_tokens"] += us.get("cache_read_input_tokens", 0)
        u["cache_creation_tokens"] += us.get("cache_creation_input_tokens", 0)
        u["num_turns"] += 1
    u["duration_ms"] = int((max(ts) - min(ts)).total_seconds() * 1000) if ts else 0
    return u, model, gold


for rid, r in res.items():
    d = disp[rid]
    u, model, gold = usage(r["agent"])
    rf = os.path.join(R4, rid.replace("|", "_") + ".result.txt")
    open(rf, "w", encoding="utf-8").write(r["text"])
    before = sum(1 for _ in open(OUT, encoding="utf-8")) if os.path.exists(OUT) else 0
    cp = subprocess.run([sys.executable, "-X", "utf8", BENCH, "judge", "--task", d["task"],
                         "--workdir", d["workdir"], "--result-file", rf,
                         "--model", model or "claude-haiku-5-5", "--effort", d["effort"],
                         "--variant", "full", "--path", "agent", "--rep", str(d["rep"]),
                         "--usage-json", json.dumps(u), "--out", OUT],
                        capture_output=True, text=True, encoding="utf-8")
    print(rid, model, "gold_seen" if gold else "", cp.stdout.strip()[-160:], cp.stderr.strip()[-200:])
    # tag the appended row with the contamination flag
    rows = open(OUT, encoding="utf-8").read().splitlines()
    if len(rows) == before + 1:
        last = json.loads(rows[-1]); last["gold_seen"] = gold; rows[-1] = json.dumps(last, ensure_ascii=False)
        open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
