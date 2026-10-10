#!/usr/bin/env python3
"""Offline controls for psearch.py parsers. Each parser gets a POSITIVE control
(a well-formed answer must yield the expected item) and, where the platform
can answer with a block/challenge page, a NEGATIVE control (that page must
raise LegUnavailable, never parse as "zero results" -- the defect this tool
exists to prevent is a refused route read as absence of discussion).
Run: python -X utf8 tools/platform-search/controls.py  -> exit 0 iff all pass."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import psearch as ps  # noqa: E402

ATOM = b"""<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><author><name>/u/alice</name></author><category term="comfyui" label="r/comfyui"/>
<content type="html">&lt;p&gt;Use GGUF + Lightx2v&lt;/p&gt;</content>
<link href="https://www.reddit.com/r/comfyui/comments/abc/wan_8gb/"/><updated>2025-10-11T02:35:57+00:00</updated>
<title>Wan 2.2 on 8GB</title></entry>
<entry><author><name>/u/bob</name></author><content type="html">reply text</content>
<link href="https://www.reddit.com/r/comfyui/comments/abc/wan_8gb/c1/"/><updated>2025-10-12T00:00:00+00:00</updated>
<title>/u/bob on Wan 2.2 on 8GB</title></entry></feed>"""
BLOCK_PAGE = b"<html><body class=theme-beta>You've been blocked by network security. If you think you've been blocked by mistake...</body></html>"
CHALLENGE = b"<html><head><title>\xe8\xab\x8b\xe7\xa8\x8d\xe5\x80\x99...</title></head><body>cf-chl</body></html>"

results = []


def check(name, cond):
    results.append((name, bool(cond)))


def raises(fn, *args):
    try:
        fn(*args)
    except ps.LegUnavailable as e:
        return str(e)
    return None


# reddit search RSS
items = ps.parse_reddit_atom(ATOM)
check("reddit+ parses 2 entries", len(items) == 2)
check("reddit+ title/url/sub/date", items[0]["title"] == "Wan 2.2 on 8GB"
      and items[0]["where"].endswith("/wan_8gb/") and "r/comfyui" in items[0]["meta"] and "2025-10-11" in items[0]["meta"])
check("reddit+ html stripped from snippet", items[0]["snippet"] == "Use GGUF + Lightx2v")
err = raises(ps.parse_reddit_atom, BLOCK_PAGE)
check("reddit- block page raises, named", err is not None and "network security" in err)
err = raises(ps.parse_reddit_atom, CHALLENGE)
check("reddit- challenge page raises, named", err is not None and "challenge" in err)

# reddit thread
th = ps.parse_reddit_thread(ATOM)
check("thread+ post then comment with authors", [t["author"] for t in th] == ["/u/alice", "/u/bob"])
check("thread- block page raises", raises(ps.parse_reddit_thread, BLOCK_PAGE) is not None)

# JSON legs
hn = ps.parse_hn({"hits": [{"title": "Show HN: X", "objectID": "42", "points": 10, "num_comments": 3,
                            "created_at": "2026-01-02T00:00:00Z", "url": "https://x.dev"}]})
check("hn+ item url + meta", hn[0]["where"].endswith("id=42") and "10 pts" in hn[0]["meta"])
check("hn+ empty hits -> empty list (a real zero)", ps.parse_hn({"hits": []}) == [])

se = ps.parse_se({"items": [{"title": "Edge coupler &amp; taper", "link": "https://physics.stackexchange.com/q/1",
                             "score": 5, "answer_count": 2, "accepted_answer_id": 9, "tags": ["optics"],
                             "last_activity_date": 1700000000}]}, "physics")
check("se+ unescaped title, accepted flag", se[0]["title"] == "Edge coupler & taper" and "(accepted)" in se[0]["meta"])

dc = ps.parse_discourse({"topics": [{"id": 7, "slug": "lora-oom", "title": "LoRA OOM", "posts_count": 4,
                                     "created_at": "2026-03-01"}],
                         "posts": [{"topic_id": 7, "blurb": "try gradient checkpointing"}]}, "discuss.pytorch.org")
check("discourse+ url + blurb", dc[0]["where"] == "https://discuss.pytorch.org/t/lora-oom/7" and "gradient" in dc[0]["snippet"])

hf = ps.parse_hf([{"id": "org/model", "downloads": 100, "likes": 2, "pipeline_tag": "text-to-video",
                   "lastModified": "2026-05-01T00:00:00Z"}])
check("hf+ url", hf[0]["where"] == "https://huggingface.co/org/model")

cv = ps.parse_civitai({"items": [{"id": 58390, "name": "Detail Tweaker", "type": "LORA",
                                  "modelVersions": [{"baseModel": "SD 1.5"}], "stats": {"downloadCount": 5}}]})
check("civitai+ base model in meta", "SD 1.5" in cv[0]["meta"] and cv[0]["where"].endswith("/58390"))

# fetch_json on a non-JSON block page must raise (negative control for every JSON leg)
check("json- block hint names the page", "network security" in ps._blocked_hint(BLOCK_PAGE))

# leg wiring: every leg has a registry id, every default leg exists
check("wiring: legs mapped to registry", set(ps.ALL_LEGS) == set(ps.LEG_REGISTRY))
check("wiring: defaults are legs", set(ps.DEFAULT) <= set(ps.ALL_LEGS))
reg = ps.registry_status()
check("wiring: every mapped registry id exists", all(v in reg for v in ps.LEG_REGISTRY.values()))

# agy: JSON list parsed; prose-only answer is undetermined (raised), never zero;
# rows without a real URL or of the wrong type are excluded
ag = ps.parse_agy('Here you go:\n```json\n[{"title": "T", "url": "https://www.reddit.com/r/x/comments/1/", '
                  '"platform": "reddit", "date": "2025-08-07", "tip": "use GGUF"}, '
                  '{"title": "no url", "url": ""}, "stray string"]\n```')
check("agy+ one valid row kept, labelled unverified", len(ag) == 1 and "unverified" in ag[0]["meta"])
err = raises(ps.parse_agy, "I could not find anything relevant.")
check("agy- prose-only answer is undetermined, not zero", err is not None and "undetermined" in err)
check("wiring: --wide adds agy and keeps defaults", "agy" in ps.WIDE and set(ps.DEFAULT) <= set(ps.WIDE))

# relaxed query: only long queries are relaxed, keeping the caller's leading words
check("relax+ long query -> first 3 words", ps.relax_query("edge coupler fiber alignment tolerance") == "edge coupler fiber")
check("relax- short query untouched", ps.relax_query("wan 2.2 lora") is None)

# undetermined: a leg result of the wrong type is reported, never folded into items
b = ps.build_blocks({"hn": {"hits": []}, "reddit": ps.LegUnavailable("x"), "se": []}, ["hn", "reddit", "se"], {})
check("undetermined: non-list leg result excluded", b["hn"]["status"].startswith("undetermined") and b["hn"]["items"] == [])
check("undetermined: unavailable and real-zero stay distinct",
      b["reddit"]["status"].startswith("unavailable") and b["se"]["status"] == "available(0)")

fails = [n for n, ok in results if not ok]
for n, ok in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"{len(results) - len(fails)}/{len(results)} pass")
sys.exit(1 if fails else 0)
