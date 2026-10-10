"""Proof-of-life for hooks/offline_approval_notice.py (two-sided controls)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(os.path.dirname(HERE), "offline_approval_notice.py")
sys.path.insert(0, os.path.dirname(HERE))
import offline_approval_notice as m  # noqa: E402

FIRE = [
    "收工流程都只先寫在一張待辦卡，因為我等下會離線，無法點選修改許可",  # the 2026-10-09 incident
    "我等下不在，你先做",
    "接下來沒辦法核可，照建議做完",
    "I'll be offline for a few hours, keep going",
    "I can't approve anything for a while",
]
SILENT = [
    "CO 卡走建議，該handoff中的兩個載體格式我也驗過",
    "幫我把離散傅立葉轉換的範例寫出來",           # 離散 ≠ 離線
    "我不會離線，有需要就問我",
    "[unattended-run] 離線跑完這批",                # the tagged route has its own kickoff
    "approve the PR after the tests pass",
]


def run(prompt, telemetry):
    env = dict(os.environ, CLAUDE_TELEMETRY_DIR=telemetry)
    r = subprocess.run([sys.executable, HOOK], input=json.dumps({"prompt": prompt, "session_id": "t"}),
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=20)
    return r.returncode, r.stdout.strip()


class Controls(unittest.TestCase):
    def test_positive_controls_fire(self):
        with tempfile.TemporaryDirectory() as t:
            for p in FIRE:
                code, out = run(p, t)
                self.assertEqual(code, 0)
                self.assertTrue(out, f"did not fire: {p}")
                ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
                self.assertTrue(ctx.startswith("offline_approval_notice, a local UserPromptSubmit hook"))
                self.assertIn("Edit(~/.claude/rules/**)", ctx)   # live ask list, not a copy
                self.assertIn("nothing needs doing", ctx)        # R2n
                self.assertIn("telemetry/offline-approval-notice.jsonl", ctx)  # R3n
            rows = open(os.path.join(t, "offline-approval-notice.jsonl"), encoding="utf-8").read().splitlines()
            self.assertEqual(len(rows), len(FIRE))           # row written before emitting

    def test_negative_controls_silent(self):
        with tempfile.TemporaryDirectory() as t:
            for p in SILENT:
                code, out = run(p, t)
                self.assertEqual(code, 0)
                self.assertEqual(out, "", f"misfired on: {p}")

    def test_task_notification_turn_is_excluded(self):
        # FP 2026-10-10: a subagent report saying "offline" arrives as a prompt turn.
        # Pair: the same wording typed by the user fires; wrapped in a notification it does not.
        body = "Offline note: neither page used Google Fonts."
        self.assertEqual(m.match(body), "Offline")
        self.assertIsNone(m.match("<task-notification>\n<result>" + body + "</result>\n</task-notification>"))

    def test_garbage_input_fails_open(self):
        r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=20)
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_undetermined_prompt_types_are_excluded(self):
        # a payload that parses but whose prompt is not a string is undetermined:
        # excluded (silent), never folded into a fire verdict
        for bad in (None, 42, ["離線"], {"text": "離線"}):
            self.assertIsNone(m.match(bad), f"undetermined input folded into a verdict: {bad!r}")
        with tempfile.TemporaryDirectory() as t:
            env = dict(os.environ, CLAUDE_TELEMETRY_DIR=t)
            r = subprocess.run([sys.executable, HOOK], input=json.dumps({"prompt": ["離線"]}),
                               capture_output=True, text=True, encoding="utf-8", env=env, timeout=20)
            self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_no_prohibited_shapes(self):
        ctx = m.compose("離線", ["Edit(x)"])
        for bad in ("Policy:", "see ", "Detail:", "tell the user", "REPORT"):
            self.assertNotIn(bad, ctx)


if __name__ == "__main__":
    unittest.main(verbosity=1)
