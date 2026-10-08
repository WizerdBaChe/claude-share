"""T03 — zh-TW → en UI strings, placeholders and tags preserved. Dispatch row: 'Translation / extraction' (cheap)."""
import json
import re
from _common import parse_json, verdict, CJK

ID = "t03_translate_to_spec"
CATEGORY = "translation-to-spec"
DISPATCH_ROW = "Translation / extraction / small to-spec scripts — hard machine-checkable gate"
EXPECTED_TIER = "cheap"
TOOLS = "none"
MAX_TURNS = 1
TIMEOUT_S = 240

SRC = {
    "save.ok": "已儲存 {count} 個檔案",
    "login.greet": "歡迎回來，<b>{name}</b>！",
    "err.quota": "超過配額：還剩 %s MB",
    "confirm.delete": "確定要刪除「{title}」嗎？此動作無法復原。",
    "sync.progress": "同步中… {done}/{total}",
    "share.link": "連結已複製到剪貼簿",
    "export.hint": "匯出會包含 <i>所有</i> 標籤",
    "retry.in": "{sec} 秒後重試",
    "empty.inbox": "收件匣是空的",
    "upgrade.cta": "升級到 <b>Pro</b> 以解除限制",
}
PLACEHOLDER = re.compile(r"\{[a-z_]+\}|%s|</?[bi]>")

PROMPT = f"""Translate the following UI strings from Traditional Chinese to natural English.
Output ONLY a JSON object with EXACTLY the same keys, values translated.
Rules: keep every placeholder (`{{name}}`, `%s`) and every HTML tag (`<b>`, `</b>`, `<i>`, `</i>`)
exactly as written and in the same count; do not add or drop keys; no prose, no code fences.

{json.dumps(SRC, ensure_ascii=False, indent=2)}
"""


def setup(workdir):
    pass


def check(result, workdir):
    try:
        got = parse_json(result)
    except ValueError:
        return verdict(False, "output is not JSON")
    if not isinstance(got, dict) or set(got) != set(SRC):
        return verdict(False, f"key set differs (missing {sorted(set(SRC) - set(got or {}))[:3]}, extra {sorted(set(got or {}) - set(SRC))[:3]})")
    bad = []
    for k, v in got.items():
        if not isinstance(v, str) or not v.strip():
            bad.append(f"{k}: empty"); continue
        if CJK.search(v):
            bad.append(f"{k}: CJK left"); continue
        if sorted(PLACEHOLDER.findall(v)) != sorted(PLACEHOLDER.findall(SRC[k])):
            bad.append(f"{k}: placeholders/tags differ"); continue
        if v == SRC[k]:
            bad.append(f"{k}: untranslated")
    if bad:
        return verdict(False, f"{len(bad)} string(s) fail: " + "; ".join(bad[:3]), score=1 - len(bad) / len(SRC))
    return verdict(True, f"{len(SRC)}/{len(SRC)} keys translated, placeholders and tags intact, no CJK")


_GOOD = {
    "save.ok": "Saved {count} files", "login.greet": "Welcome back, <b>{name}</b>!",
    "err.quota": "Quota exceeded: %s MB left", "confirm.delete": "Delete \"{title}\"? This cannot be undone.",
    "sync.progress": "Syncing… {done}/{total}", "share.link": "Link copied to clipboard",
    "export.hint": "Export will include <i>all</i> tags", "retry.in": "Retrying in {sec} seconds",
    "empty.inbox": "Your inbox is empty", "upgrade.cta": "Upgrade to <b>Pro</b> to remove limits",
}
_BAD1 = dict(_GOOD); _BAD1["save.ok"] = "Saved {n} files"            # placeholder renamed
_BAD2 = dict(_GOOD); _BAD2["login.greet"] = "Welcome back, {name}!"  # tags dropped
_BAD3 = dict(_GOOD); _BAD3["empty.inbox"] = "收件匣 is empty"          # CJK left
CONTROLS = [
    {"result": json.dumps(_GOOD, ensure_ascii=False), "expect": True},
    {"result": json.dumps(_BAD1), "expect": False},
    {"result": json.dumps(_BAD2), "expect": False},
    {"result": json.dumps(_BAD3, ensure_ascii=False), "expect": False},
]
