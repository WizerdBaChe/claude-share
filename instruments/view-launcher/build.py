#!/usr/bin/env python3
r"""view-launcher — one front door to every project's view pages: sidebar of projects + dashboard.

  python tools/view-launcher/build.py             # writes ~/.claude/All-View-Pages-Launcher.html + .md,
                                                  # and the desktop shortcut if it is missing
  python tools/view-launcher/build.py --gist      # the compact text the SessionStart hook injects
  python tools/view-launcher/build.py --selftest  # two-sided controls, last line `ALL PASS n/n`

WHY (user rulings 2026-09-21, retrieval-linkage audit finding F-4). Core overview pages live
inside the tools that make them, and SSLD grows a new case or round every few days; the user's
diagnosis of the unopened GUIs was "no entry layer, so I forgot", and of the growth, "I will
lose track". This is that layer: a LAUNCHER in the game-launcher sense. Pages are its profiles
and are never moved, copied or edited by it.

THREE SOURCES, and which of them needs a human:
  1. PINNED   `views.json` — core pages by FUNCTION name (agent proposes, user approves). The
              only hand-kept source; needed for pages no index reaches (gitignored `out/`).
  2. AUTO     `tools/cross-index/out/stores/*.derived.json` — every human-facing deliverable
              (html/pptx/docx/xlsx) under a registered store, re-emitted DAILY by xi. A new
              round folder or page appears here with nobody registering anything.
  3. PROJECTS `references/PROJECTS.md` — names, status and roots. An item belongs to the
              registered project with the LONGEST matching root; an item under no registered
              project is filed under its top folder and marked unregistered — shown, never dropped.
A "round" is the first folder below the project root (SSLD's T09_…); rounds sort newest first.

LEVEL / CONSUMER. `views.json` = instrument register. `All-View-Pages-Launcher.html` = audience
entry. `All-View-Pages-Launcher.md` = the same for the Obsidian window. Both generated at the
~/.claude root, gitignored, rebuilt by the daily carrier right AFTER xi's emit so they read the
fresh index. The machine reader takes `views.json` / `--gist`, never the HTML.

NAME AND REACH (user ruling 2026-09-25). The outputs were `VIEWS.html` / `VIEWS.md`: a generic
name shared with `views.json` beside them and with several `out/views` folders under `<WORK_ROOT>`,
and the file sat in the hidden-by-habit ~/.claude folder while the desktop shortcut the README
promised did not exist. The ruling: a long, self-explanatory English name, the file stays where
it is, and the build itself ensures a desktop shortcut `All-View-Pages-Launcher.lnk` (created
when missing or pointing elsewhere, never duplicated; a failure is printed as WARN and never
fails the build). Other folders that want a door to it (facet-layer's `<WORK_ROOT>`\00_總覽) create
their own shortcut; this tool writes only the desktop one.

WHAT IT MAY RULE ON. "This path exists now and was modified then." Ages are computed in the
browser at VIEW time. A pinned page whose file is missing stays, greyed, with its refresh
command; an AUTO item whose file is missing is dropped and COUNTED on the page (the index is a
day old at worst — a listed-but-dead link is the worse failure there).

SIDEBAR (user ruling 2026-09-21, after a side-panel survey of Linear / Primer / Atlassian / Fluent /
Carbon / Apple HIG / M3): projects are GROUPED under the dashboard's own `groups` (one taxonomy for
both panes), in a STABLE order written in views.json `sidebar` (recency is the green dot + count of
files updated in 7 days, never the sort key), at most one nesting level (a `families` entry), and
archived statuses + unregistered projects collapse at the bottom. `place()` decides the bucket; the
fold state is remembered per viewer in localStorage (a convenience only; the hash stays the state).
Cards keep the path visible; the regenerate command sits behind a disclosure (open when the file is
missing).

NAVIGATION (rules/web-navigation-state.md): every destination is an `<a href="#…">` with
`aria-current`; the current project and the filter text live in the URL hash, so reload, Back
and a bookmark land on the same view.

RUNTIME FAILURE MODES, and what the user sees: scripts blocked or crashed -> a red banner, and
the pinned pages remain as plain links in a <noscript>/fallback list; clipboard blocked on
file:// -> the button says so and the text stays selectable; the derived index missing -> the
page says the automatic part is empty and names the command, pinned pages still work. A page
that needs a server cannot be started from a static file; its card shows the command to copy.

EXTENSION: new pinned page = one entry in views.json; new file TYPE or folder = xi's registry
`deliverables` globs (this tool follows); new output form = one more `render_*` over `collect()`.
review-when: xi's derived artifact changes shape (`root`, `cards[].path|name|heads|ext`);
PROJECTS.md's column layout changes (project | status | path first); the embedded item count
passes ~3000 (page weight — then split per project).
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
VIEWS = HERE / "views.json"
STORES = HOME / "tools" / "cross-index" / "out" / "stores"
PROJECTS_MD = HOME / "references" / "PROJECTS.md"
OUT_HTML = HOME / "All-View-Pages-Launcher.html"
OUT_MD = HOME / "All-View-Pages-Launcher.md"
SHORTCUT_NAME = "All-View-Pages-Launcher.lnk"
GIST_MAX = 12
RECENT_N = 12
_WIN_PATH = re.compile(r"[A-Za-z]:[\\/][^`|（(＋+\s]+")


class ViewsError(Exception):
    pass


def _norm(p: str) -> str:
    return p.replace("\\", "/").rstrip("/").casefold()


def load(path: Path = VIEWS) -> dict:
    """The pinned register, validated."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ViewsError(f"cannot read {path}: {e}")
    groups = data.get("groups") or []
    views = data.get("views") or []
    gids = [g.get("id") for g in groups]
    seen = set()
    for v in views:
        for key in ("id", "group", "title", "answers", "path"):
            if not v.get(key):
                raise ViewsError(f"{path.name}: entry {v.get('id', '?')!r} is missing `{key}`")
        if v["id"] in seen:
            raise ViewsError(f"{path.name}: duplicate id {v['id']!r}")
        if v["group"] not in gids:
            raise ViewsError(f"{path.name}: entry {v['id']!r} names unknown group {v['group']!r}")
        seen.add(v["id"])
        p = Path(v["path"])
        v["_exists"] = p.is_file()
        v["_mtime"] = int(p.stat().st_mtime) if v["_exists"] else 0
        v["_uri"] = p.as_uri() if p.is_absolute() else ""
    sidebar = data.get("sidebar") or {}
    for gid in (sidebar.get("project_groups") or {}):
        if gid not in gids:
            raise ViewsError(f"{path.name}: sidebar.project_groups names unknown group {gid!r}")
    for f in sidebar.get("families") or []:
        if not f.get("id") or not f.get("title") or not f.get("members"):
            raise ViewsError(f"{path.name}: sidebar family {f.get('id', '?')!r} needs id, title and members")
        if f.get("group") not in gids:
            raise ViewsError(f"{path.name}: sidebar family {f['id']!r} names unknown group {f.get('group')!r}")
    for key, gid in (sidebar.get("fallback") or {}).items():
        if gid not in gids:
            raise ViewsError(f"{path.name}: sidebar.fallback.{key} names unknown group {gid!r}")
    return {"groups": groups, "views": views, "sidebar": sidebar}


def place(projects: list[dict], sidebar: dict, home: Path = HOME) -> None:
    """Give each sidebar project a bucket (a group id, 'archive' or 'unregistered'), a stable rank,
    and its family. Archive status wins over everything; a family member follows its family's group,
    so an unregistered family member is NOT dropped into 'unregistered'."""
    rank: dict[str, tuple[str, int]] = {}
    for gid, names in (sidebar.get("project_groups") or {}).items():
        for i, n in enumerate(names):
            rank.setdefault(n, (gid, i))
    fam = {m: (f, lbl) for f in sidebar.get("families") or [] for m, lbl in f["members"].items()}
    arch = [s.casefold() for s in sidebar.get("archive_status") or []]
    fb = sidebar.get("fallback") or {}
    hn = _norm(str(home))
    for p in projects:
        st = p["status"].casefold()
        f, lbl = fam.get(p["name"], (None, ""))
        p["family"], p["label"], p["rank"] = (f["id"] if f else ""), lbl, 999
        if p["name"] in rank:
            p["rank"] = rank[p["name"]][1]
        if any(st.startswith(a) for a in arch):
            p["bucket"] = "archive"
            p["family"] = ""
        elif f:
            p["bucket"] = f["group"]
            p["rank"] = min(p["rank"], min((rank[m][1] for m in f["members"] if m in rank), default=999))
        elif p["name"] in rank:
            p["bucket"] = rank[p["name"]][0]
        elif not p["registered"]:
            p["bucket"] = "unregistered"
        else:
            under = _norm(p.get("root") or "").startswith(hn + "/") or _norm(p.get("root") or "") == hn
            p["bucket"] = fb.get("under_home" if under else "other", "unregistered")


def read_projects(md: Path) -> list[dict]:
    """Registered projects: name, short status, root paths. Unreadable file -> []."""
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].casefold() in ("project", "") or set(cells[0]) <= set("-: "):
            continue
        roots = [m.group(0).rstrip(".,;)") for m in _WIN_PATH.finditer(cells[2])]
        status = re.split(r"[(（—]| - ", cells[1].replace("*", ""), maxsplit=1)[0].strip()[:40]
        out.append({"name": cells[0].strip("`* "), "status": status, "roots": roots})
    return out


def read_auto(stores: Path) -> tuple[list[dict], int]:
    """-> (items from xi's derived cards whose file exists, count dropped as missing)."""
    items, dropped = [], 0
    for art_path in sorted(stores.glob("*.derived.json")):
        try:
            art = json.loads(art_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        root = str(art.get("root", "")).replace("\\", "/").rstrip("/")
        for c in art.get("cards", []):
            full = f"{root}/{c.get('path', '')}"
            p = Path(full)
            try:
                st = p.stat()
            except OSError:
                dropped += 1
                continue
            heads = " ".join(str(c.get("heads", "")).split())
            items.append({"path": full, "store_root": root, "file": p.name, "ext": str(c.get("ext", p.suffix.lstrip("."))),
                          "title": heads[:80], "mtime": int(st.st_mtime), "uri": p.as_uri()})
    return items, dropped


def assign(items: list[dict], projects: list[dict]) -> None:
    """Longest registered root wins; otherwise the top folder under the store root, unregistered."""
    roots = sorted(((_norm(r), pr["name"], r.replace("\\", "/").rstrip("/")) for pr in projects for r in pr["roots"]),
                   key=lambda t: -len(t[0]))
    for it in items:
        n = _norm(it["path"])
        for nr, name, raw in roots:
            if n == nr or n.startswith(nr + "/"):
                it["project"], it["registered"], base = name, True, raw
                break
        else:
            rel = it["path"][len(it["store_root"]) + 1:]
            top = rel.split("/", 1)[0] if "/" in rel else ""
            it["project"] = top or Path(it["store_root"]).name
            it["registered"] = False
            base = f"{it['store_root']}/{top}" if top else it["store_root"]
        rel = it["path"][len(base) + 1:]
        it["round"] = rel.split("/", 1)[0] if "/" in rel else ""
        it["project_root"] = base


def collect(views: Path = VIEWS, stores: Path = STORES, projects_md: Path = PROJECTS_MD) -> dict:
    pinned = load(views)
    projects = read_projects(projects_md)
    items, dropped = read_auto(stores)
    assign(items, projects)
    pinned_paths = {_norm(v["path"]) for v in pinned["views"]}
    items = [it for it in items if _norm(it["path"]) not in pinned_paths]      # a pinned page is shown once
    status = {p["name"]: p["status"] for p in projects}
    roots = {p["name"]: p["roots"] for p in projects}
    plist: dict[str, dict] = {}
    for it in items:
        pr = plist.setdefault(it["project"], {"name": it["project"], "registered": it["registered"],
                                              "status": status.get(it["project"], ""), "root": it["project_root"],
                                              "count": 0, "latest": 0})
        pr["count"] += 1
        pr["latest"] = max(pr["latest"], it["mtime"])
    for v in pinned["views"]:                       # a project that only has pinned pages still gets a sidebar row
        name = v.get("project")
        if name and name not in plist:
            plist[name] = {"name": name, "registered": name in status, "status": status.get(name, ""),
                           "root": next(iter(roots.get(name, [])), "").replace("\\", "/"), "count": 0, "latest": v["_mtime"]}
    ordered = sorted(plist.values(), key=lambda p: -p["latest"])
    place(ordered, pinned["sidebar"])
    families = [{"id": f["id"], "title": f["title"]} for f in pinned["sidebar"].get("families") or []]
    return {"groups": pinned["groups"], "views": pinned["views"], "items": items, "dropped": dropped, "families": families,
            "projects": ordered, "auto_available": stores.is_dir() and bool(items)}


# ---------------------------------------------------------------- HTML

CSS = """
:root{--bg:#faf7f1;--side:#f1ece0;--card:#fffdf8;--ink:#23201b;--mute:#6f675b;--line:#ddd5c6;--accent:#8a3b12;
--ok:#2f6b3a;--gone:#9a2a2a;--chip:#efe8da;--sidew:clamp(15rem,19vw,21rem)}
*{box-sizing:border-box}
html{font-size:17px}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.55;
font-family:"Noto Serif TC","Source Han Serif TC","PMingLiU",Georgia,serif}
#app{display:grid;grid-template-columns:var(--sidew) minmax(0,1fr);min-height:100vh}
nav{background:var(--side);border-right:1px solid var(--line);padding:22px 0 30px;position:sticky;top:0;
height:100vh;overflow-y:auto}
nav h1{font-size:1.35rem;margin:0 20px 2px;letter-spacing:.06em}
nav .sub{margin:0 20px 16px;color:var(--mute);font-size:.76rem}
nav .navsec{border-top:1px solid var(--line);margin-top:12px;padding-top:4px}
nav h2{font-size:.76rem;letter-spacing:.06em;color:var(--mute);margin:10px 20px 4px;font-weight:700}
nav a,nav summary{display:flex;gap:8px;align-items:center;padding:5px 20px;color:var(--ink);text-decoration:none;
font-size:.9rem;border-left:3px solid transparent;min-width:0}
nav a:hover,nav a:focus-visible,nav summary:hover{background:var(--chip)}
nav a[aria-current=page]{border-left-color:var(--accent);background:var(--card);font-weight:600}
nav .nm{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
nav .n{color:var(--ok);font:600 .72rem Consolas,monospace;white-space:nowrap}
nav .dot{width:7px;height:7px;border-radius:50%;background:var(--ok);flex:none}
nav .nodot{width:7px;flex:none}
nav a.unreg .nm{font-style:italic}
nav details>summary{cursor:pointer;list-style:none}
nav details>summary::-webkit-details-marker{display:none}
nav details>summary .tw{width:10px;flex:none;color:var(--mute);font-size:.7rem}
nav details>summary .tw::before{content:"▸"}nav details[open]>summary .tw::before{content:"▾"}
nav details.fam a{padding-left:44px}
nav details.fold>summary{color:var(--mute);font-size:.84rem}
nav details.fold a{opacity:.85}
main{padding:24px clamp(16px,2.6vw,44px) 50px;min-width:0}
.top{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:end;justify-content:space-between;
border-bottom:1px solid var(--line);padding-bottom:14px}
.top h2{font-size:1.7rem;margin:0;letter-spacing:.03em;overflow-wrap:anywhere}
.top p{margin:4px 0 0;color:var(--mute);font-size:.85rem;overflow-wrap:anywhere}
#q{font:inherit;font-size:.92rem;padding:8px 12px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--ink);width:min(100%,24rem)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr));gap:14px;margin:20px 0 6px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px}
.tile b{display:block;font-size:1.9rem;line-height:1.15}
.tile span{color:var(--mute);font-size:.8rem}
.tile.bad b{color:var(--gone)}
h3.sec{font-size:1rem;margin:28px 0 12px;color:var(--accent);letter-spacing:.08em;font-weight:600;overflow-wrap:anywhere}
h3.sec small{color:var(--mute);font-weight:400;letter-spacing:0;margin-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,20rem),1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px 13px;
display:flex;flex-direction:column;gap:7px;min-width:0}
.card h4{margin:0;font-size:1.15rem;line-height:1.35}
.card h4 a{color:var(--ink);text-decoration:none;border-bottom:2px solid var(--accent)}
.card h4 a:hover,.card h4 a:focus-visible{color:var(--accent)}
.answers{margin:0;color:var(--mute);font-size:.92rem}
.meta{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:.78rem;color:var(--mute)}
.chip{background:var(--chip);border-radius:99px;padding:1px 9px;font:500 .72rem Consolas,monospace}
.age{color:var(--ok)}
.row{display:flex;gap:8px;align-items:flex-start;min-width:0}
code{font-family:Consolas,"Cascadia Mono",monospace;font-size:.72rem;color:var(--mute);overflow-wrap:anywhere;
flex:1;min-width:0;user-select:all}
button{font:inherit;font-size:.72rem;border:1px solid var(--line);background:var(--bg);color:var(--ink);
border-radius:5px;padding:1px 8px;cursor:pointer;white-space:nowrap}
button:hover{border-color:var(--accent)}
.lbl{font-size:.7rem;color:var(--mute);white-space:nowrap;padding-top:1px}
details.more summary{cursor:pointer;font-size:.72rem;color:var(--mute);width:max-content}
details.more summary:hover{color:var(--accent)}
details.more .row{margin-top:5px}
.card.gone{border-style:dashed;opacity:.85}.card.gone h4{color:var(--gone)}
.gone-note{color:var(--gone);font-size:.85rem;margin:0}
ul.items{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--line);border-radius:10px}
ul.items li{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:4px 14px;align-items:baseline;
padding:9px 16px;border-top:1px solid var(--line)}
ul.items li:first-child{border-top:0}
ul.items a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--accent);overflow-wrap:anywhere}
ul.items a:hover,ul.items a:focus-visible{color:var(--accent)}
ul.items .f{grid-column:1/-1;font:400 .7rem Consolas,monospace;color:var(--mute);overflow-wrap:anywhere}
ul.items .when{font-size:.78rem;color:var(--ok);white-space:nowrap}
.note{color:var(--mute);font-size:.88rem;margin:18px 0}
#err{display:none;background:#9a2a2a;color:#fff;padding:10px 20px;font-size:.9rem}
#fallback{padding:24px}
footer{margin-top:40px;color:var(--mute);font-size:.78rem;overflow-wrap:anywhere}
@media (max-width:760px){#app{grid-template-columns:1fr}nav{position:static;height:auto;max-height:45vh}}
"""

JS = r"""
window.onerror=function(m){var e=document.getElementById('err');e.style.display='block';
e.textContent='啟動器的腳本出錯了（下方仍列出釘選頁面的連結）：'+m;
document.getElementById('fallback').hidden=false;console.error({source:'view-launcher',error:String(m)});};
(function(){
var D=JSON.parse(document.getElementById('data').textContent),DAY=86400,now=Date.now()/1000;
function el(t,c,x){var n=document.createElement(t);if(c)n.className=c;if(x!=null)n.textContent=x;return n;}
function age(s){var d=(now-s)/DAY;if(d<1/24)return'剛剛';if(d<1)return Math.round(d*24)+' 小時前';if(d<60)return Math.round(d)+' 天前';return Math.round(d/30)+' 個月前';}
function stamp(s){var t=new Date(s*1000),p=function(x){return(x<10?'0':'')+x;};return t.getFullYear()+'-'+p(t.getMonth()+1)+'-'+p(t.getDate())+' '+p(t.getHours())+':'+p(t.getMinutes());}
function state(){var h=new URLSearchParams(location.hash.slice(1));return{p:h.get('p')||'',q:h.get('q')||''};}
function href(p,q){var h=new URLSearchParams();if(p)h.set('p',p);if(q)h.set('q',q);var s=h.toString();return'#'+s;}
function copyBtn(text){var b=el('button',null,'複製');b.type='button';b.addEventListener('click',function(){
var done=function(ok){b.textContent=ok?'已複製':'複製失敗，請手動選取';setTimeout(function(){b.textContent='複製';},1600);};
if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).then(function(){done(true);},function(){done(false);});else done(false);});return b;}
function row(label,text){var r=el('div','row');r.appendChild(el('span','lbl',label));r.appendChild(el('code',null,text));r.appendChild(copyBtn(text));return r;}
function card(v){var c=el('article','card'+(v.exists?'':' gone')),h=el('h4');
if(v.exists){var a=el('a',null,v.title);a.href=v.uri;h.appendChild(a);}else h.textContent=v.title;c.appendChild(h);
c.appendChild(el('p','answers',v.answers));var m=el('div','meta');if(v.project)m.appendChild(el('span','chip',v.project));
if(v.exists)m.appendChild(el('span','age',age(v.mtime)+'更新（'+stamp(v.mtime)+'）'));c.appendChild(m);
if(!v.exists)c.appendChild(el('p','gone-note','找不到這個檔案——可能還沒產生，或被搬走了。'+(v.refresh?'用下面的指令重新產生；':'')+'搬走的話請改 views.json 裡的路徑。'));
c.appendChild(row('位置',v.path.replace(/\//g,'\\')));
if(v.refresh){var d=el('details','more');if(!v.exists)d.open=true;d.appendChild(el('summary',null,'重新產生指令'));d.appendChild(row('指令',v.refresh));c.appendChild(d);}
return c;}
function itemLi(it,showProject){var li=el('li'),a=el('a',null,it.title||it.file);a.href=it.uri;li.appendChild(a);
li.appendChild(el('span','chip',it.ext));li.appendChild(el('span','when',age(it.mtime)));
li.appendChild(el('span','f',(showProject?it.project+' ／ ':'')+(it.round?it.round+' ／ ':'')+it.file));return li;}
function list(items,showProject){var u=el('ul','items');items.forEach(function(it){u.appendChild(itemLi(it,showProject));});return u;}
function sec(t,small){var h=el('h3','sec',t);if(small)h.appendChild(el('small',null,small));return h;}
function match(o,k){return!k||JSON.stringify(o).toLowerCase().indexOf(k)>=0;}
var OPEN={};try{OPEN=JSON.parse(localStorage.getItem('view-launcher-open')||'{}')||{};}catch(e){OPEN={};}
function saveOpen(){try{localStorage.setItem('view-launcher-open',JSON.stringify(OPEN));}catch(e){}}
function total(p){return p.count+D.views.filter(function(v){return v.project===p.name;}).length;}
function recent(p){return D.items.filter(function(it){return it.project===p.name&&now-it.mtime<7*DAY;}).length
+D.views.filter(function(v){return v.project===p.name&&v.exists&&now-v.mtime<7*DAY;}).length;}
function mark(a,r){if(r){var d=el('span','dot');d.title='七天內有更新';a.appendChild(d);}else a.appendChild(el('span','nodot'));}
function projLink(p,s,label){var a=el('a',p.registered?'':'unreg'),r=recent(p);a.href=href(p.name,s.q);
a.title=p.name+(p.registered?'':'（未登記）')+' — 共 '+total(p)+' 個，七天內更新 '+r+' 個';mark(a,r);
a.appendChild(el('span','nm',label||p.name));if(r)a.appendChild(el('span','n',String(r)));
if(s.p===p.name)a.setAttribute('aria-current','page');return a;}
function fold(key,cls,title,r,defOpen,force){var d=el('details',cls),sm=el('summary');sm.appendChild(el('span','tw'));
sm.appendChild(el('span','nm',title));if(r)sm.appendChild(el('span','n',String(r)));d.appendChild(sm);
d.open=force||(OPEN.hasOwnProperty(key)?OPEN[key]:defOpen);
d.addEventListener('toggle',function(){OPEN[key]=d.open;saveOpen();});return d;}
function units(ps){var fams={},out=[];ps.forEach(function(p){if(p.family){if(!fams[p.family]){fams[p.family]={fam:p.family,rank:p.rank,name:'',members:[]};out.push(fams[p.family]);}
var F=fams[p.family];F.members.push(p);F.rank=Math.min(F.rank,p.rank);}else out.push({p:p,rank:p.rank,name:p.name.toLowerCase()});});
out.sort(function(a,b){return a.rank-b.rank||(a.name<b.name?-1:a.name>b.name?1:0);});return out;}
function nav(s){var n=document.getElementById('nav');n.textContent='';n.appendChild(el('h1',null,'檢視入口'));
n.appendChild(el('p','sub',D.views.length+' 個釘選 · '+D.items.length+' 個自動收錄'));
var a=el('a',null,'首頁總覽');a.href=href('',s.q);if(!s.p)a.setAttribute('aria-current','page');n.appendChild(a);
function sumR(ps){return ps.reduce(function(t,p){return t+recent(p);},0);}
D.groups.forEach(function(g){var ps=D.projects.filter(function(p){return p.bucket===g.id;});if(!ps.length)return;
var sec=el('div','navsec');sec.appendChild(el('h2',null,g.title||g.id));
units(ps).forEach(function(u){if(u.p){sec.appendChild(projLink(u.p,s));return;}
var F=D.families.filter(function(f){return f.id===u.fam;})[0]||{title:u.fam};
u.members.sort(function(a,b){return a.rank-b.rank;});
var cur=u.members.some(function(p){return p.name===s.p;}),d=fold('fam:'+u.fam,'fam',F.title,sumR(u.members),true,cur);
u.members.forEach(function(p){d.appendChild(projLink(p,s,p.label||p.name));});sec.appendChild(d);});n.appendChild(sec);});
[['archive','封存與維護'],['unregistered','未登記']].forEach(function(b){var ps=D.projects.filter(function(p){return p.bucket===b[0];});if(!ps.length)return;
ps.sort(function(x,y){return x.name.toLowerCase()<y.name.toLowerCase()?-1:1;});
var sec=el('div','navsec'),cur=ps.some(function(p){return p.name===s.p;}),d=fold('bucket:'+b[0],'fold',b[1]+'（'+ps.length+'）',0,false,cur);
ps.forEach(function(p){d.appendChild(projLink(p,s));});sec.appendChild(d);n.appendChild(sec);});}
function top(title,sub,s){var t=el('div','top'),l=el('div');l.appendChild(el('h2',null,title));l.appendChild(el('p',null,sub));t.appendChild(l);
var q=el('input');q.id='q';q.type='search';q.value=s.q;q.placeholder=s.p?'在這個專案裡篩選':'搜尋全部頁面與檔案';q.setAttribute('aria-label','篩選');
q.addEventListener('input',function(){history.replaceState(null,'',href(s.p,q.value.trim())||'#');render(true);});t.appendChild(q);return t;}
function tile(n,label,bad){var t=el('div','tile'+(bad?' bad':''));t.appendChild(el('b',null,String(n)));t.appendChild(el('span',null,label));return t;}
function home(m,s,k){m.appendChild(top('首頁總覽','所有核心檢視頁與各專案的產出頁；頁面都留在原處，這裡只負責帶路。',s));
if(k){var hv=D.views.filter(function(v){return match(v,k);}),hi=D.items.filter(function(it){return match(it,k);});
m.appendChild(sec('搜尋結果',hv.length+hi.length+' 筆'));if(hv.length){var g=el('div','grid');hv.forEach(function(v){g.appendChild(card(v));});m.appendChild(g);}
if(hi.length)m.appendChild(list(hi.slice(0,200),true));if(!hv.length&&!hi.length)m.appendChild(el('p','note','沒有符合的項目。'));return;}
var gone=D.views.filter(function(v){return!v.exists;}).length,wk=D.items.filter(function(it){return now-it.mtime<7*DAY;}).length;
var ts=el('div','tiles');ts.appendChild(tile(D.projects.length,'個專案'));ts.appendChild(tile(D.views.length,'個釘選的核心頁'));
ts.appendChild(tile(D.items.length,'個自動收錄的產出檔'));ts.appendChild(tile(wk,'個在七天內更新'));
if(gone)ts.appendChild(tile(gone,'個釘選頁找不到檔案',true));m.appendChild(ts);
D.groups.forEach(function(g){var vs=D.views.filter(function(v){return v.group===g.id;});if(!vs.length)return;
m.appendChild(sec(g.title||g.id));var gr=el('div','grid');vs.forEach(function(v){gr.appendChild(card(v));});m.appendChild(gr);});
m.appendChild(sec('最近更新',' 跨所有專案，最新 '+D.recent_n+' 筆'));
if(D.items.length)m.appendChild(list(D.items.slice().sort(function(a,b){return b.mtime-a.mtime;}).slice(0,D.recent_n),true));
else m.appendChild(el('p','note','自動收錄的部分目前是空的：找不到產出檔索引。重新產生索引的指令：python -X utf8 '+D.emit_cmd));}
function project(m,s,k,p){m.appendChild(top(p.name,(p.registered?(p.status||'已登記'):'未登記在專案登記表，依資料夾歸類')+(p.root?' · '+p.root.replace(/\//g,'\\'):''),s));
var vs=D.views.filter(function(v){return v.project===p.name&&match(v,k);});
if(vs.length){m.appendChild(sec('釘選的核心頁'));var g=el('div','grid');vs.forEach(function(v){g.appendChild(card(v));});m.appendChild(g);}
var its=D.items.filter(function(it){return it.project===p.name&&match(it,k);}),rounds={},order=[];
its.forEach(function(it){if(!rounds[it.round]){rounds[it.round]={items:[],latest:0};order.push(it.round);}rounds[it.round].items.push(it);rounds[it.round].latest=Math.max(rounds[it.round].latest,it.mtime);});
order.sort(function(a,b){return rounds[b].latest-rounds[a].latest;});
order.forEach(function(r){var R=rounds[r];R.items.sort(function(a,b){return b.mtime-a.mtime;});
m.appendChild(sec(r||'（專案根目錄）',R.items.length+' 個 · 最近 '+age(R.latest)));m.appendChild(list(R.items,false));});
if(!vs.length&&!its.length)m.appendChild(el('p','note',k?'這個專案裡沒有符合的項目。':'這個專案目前沒有收錄任何頁面。'));}
function render(keepFocus){var s=state(),k=s.q.toLowerCase(),m=document.getElementById('main');m.textContent='';nav(s);
var p=D.projects.filter(function(x){return x.name===s.p;})[0];
if(s.p&&!p){m.appendChild(top('找不到這個專案','網址裡的專案「'+s.p+'」不在目前的清單裡，可能已改名。',s));}
else if(p)project(m,s,k,p);else home(m,s,k);
var f=el('footer',null,'清單產生於 '+D.built+'；「多久前」是打開這一頁時才算的。'+(D.dropped?'索引裡有 '+D.dropped+' 個檔案已不在原處，未列出。':'')+'釘選頁面改 '+D.views_file+'；其餘每日自動更新。');m.appendChild(f);
if(keepFocus){var q=document.getElementById('q');q.focus();q.setSelectionRange(q.value.length,q.value.length);}
document.title=(p?p.name+' — ':'')+'檢視入口';}
window.addEventListener('hashchange',function(){render(false);});render(false);
})();
"""


def _payload(data: dict, built: float) -> dict:
    return {
        "built": time.strftime("%Y-%m-%d %H:%M", time.localtime(built)), "recent_n": RECENT_N,
        "dropped": data["dropped"], "views_file": str(VIEWS),
        "emit_cmd": str(HOME / "tools" / "cross-index" / "xi.py") + " emit",
        "groups": data["groups"], "projects": data["projects"], "families": data["families"],
        "views": [{"id": v["id"], "group": v["group"], "title": v["title"], "answers": v["answers"],
                   "project": v.get("project", ""), "path": v["path"], "refresh": v.get("refresh", ""),
                   "exists": v["_exists"], "mtime": v["_mtime"], "uri": v["_uri"]} for v in data["views"]],
        "items": [{k: it[k] for k in ("title", "file", "ext", "mtime", "uri", "project", "round")} for it in data["items"]],
    }


def render_html(data: dict, built: float) -> str:
    e = html.escape
    blob = json.dumps(_payload(data, built), ensure_ascii=False).replace("</", "<\\/")
    fallback = "".join(f'<li><a href="{e(v["_uri"], quote=True)}">{e(v["title"])}</a> — {e(v["answers"])}</li>'
                       for v in data["views"] if v["_exists"])
    return ('<!doctype html>\n<html lang="zh-Hant" data-page-class="dashboard">\n<head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>檢視入口</title>'
            f'<style>{CSS}</style></head>\n<body><div id="err" role="alert"></div>'
            '<div id="app"><nav id="nav" aria-label="專案"></nav><main id="main"></main></div>\n'
            f'<div id="fallback" hidden><p>釘選的核心頁（純連結）：</p><ul>{fallback}</ul></div>'
            f'<noscript><div style="padding:24px"><p>這一頁需要 JavaScript 才能顯示側邊欄與儀表；釘選的核心頁：</p><ul>{fallback}</ul></div></noscript>\n'
            f'<script type="application/json" id="data">{blob}</script>\n<script>{JS}</script></body></html>\n')


def render_md(data: dict, built: float) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(built))
    lines = ["# 檢視入口", "",
             f"所有核心檢視頁與各專案產出頁的總入口（產生於 {stamp}；此檔由 `tools/view-launcher/build.py` 每日產生，請勿手改）。"
             f"側邊欄＋儀表的圖形版：[{OUT_HTML.name}]({OUT_HTML.as_uri()})", ""]
    for g in data["groups"]:
        vs = [v for v in data["views"] if v["group"] == g["id"]]
        if not vs:
            continue
        lines += [f"## {g.get('title', g['id'])}", ""]
        for v in vs:
            head = f"[{v['title']}]({v['_uri']})" if v["_exists"] else f"{v['title']}（⚠ 找不到檔案）"
            lines.append(f"- **{head}** — {v['answers']}")
            if v.get("refresh"):
                lines.append(f"  - 重新產生：`{v['refresh']}`")
        lines.append("")
    lines += ["## 各專案（最近有動的在上）", ""]
    for p in data["projects"]:
        its = sorted((it for it in data["items"] if it["project"] == p["name"]), key=lambda it: -it["mtime"])
        tag = "" if p["registered"] else "（未登記）"
        latest = time.strftime("%Y-%m-%d", time.localtime(p["latest"])) if p["latest"] else "-"
        lines.append(f"- **{p['name']}**{tag} — {p['count']} 個產出檔，最近 {latest}")
        for it in its[:3]:
            lines.append(f"  - [{it['title'] or it['file']}]({it['uri']})" + (f" · {it['round']}" if it["round"] else ""))
    lines.append("")
    return "\n".join(lines)


def render_gist(data: dict) -> str:
    """Compact machine-facing list: function name -> path. One line per pinned view, capped."""
    rows = [f"- {v['title']} [{v.get('project', '-')}] {v['path']}" + ("" if v["_exists"] else "  (file missing)")
            for v in data["views"][:GIST_MAX]]
    more = len(data["views"]) - GIST_MAX
    if more > 0:
        rows.append(f"- (+{more} more in tools/view-launcher/views.json)")
    return "\n".join(rows)


def build(views: Path = VIEWS, out_html: Path = OUT_HTML, out_md: Path = OUT_MD,
          stores: Path = STORES, projects_md: Path = PROJECTS_MD) -> int:
    data = collect(views, stores, projects_md)
    now = time.time()
    out_html.write_text(render_html(data, now), encoding="utf-8", newline="\n")
    out_md.write_text(render_md(data, now), encoding="utf-8", newline="\n")
    gone = [v["id"] for v in data["views"] if not v["_exists"]]
    unreg = [p["name"] for p in data["projects"] if not p["registered"]]
    print(f"view-launcher: {len(data['views'])} pinned ({len(gone)} missing{' ' + str(gone) if gone else ''}), "
          f"{len(data['items'])} auto items in {len(data['projects'])} projects ({len(unreg)} unregistered), "
          f"{data['dropped']} index rows dropped as missing -> {out_html}")
    if not data["auto_available"]:
        print(f"view-launcher: WARN — no derived index under {stores}; only pinned pages are shown "
              f"(repair: python -X utf8 {HOME / 'tools' / 'cross-index' / 'xi.py'} emit)")
    return 0


def _ps(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def _ps_quote(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def desktop_dir() -> Path | None:
    r = _ps("[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetFolderPath('Desktop')")
    out = r.stdout.strip()
    return Path(out) if r.returncode == 0 and out else None


def ensure_shortcut(target: Path, folder: Path | None, name: str = SHORTCUT_NAME) -> str:
    """Create/repair `<folder>/<name>` -> target. Returns 'ok' | 'created' | 'repaired' | 'WARN …'.

    Idempotent: an existing shortcut already pointing at `target` is left untouched (mtime kept).
    Best-effort: never raises; the caller prints the result and the build verdict is unaffected."""
    if folder is None or not folder.is_dir():
        return f"WARN no desktop folder ({folder})"
    lnk = folder / name
    try:
        script = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; $w=New-Object -ComObject WScript.Shell; "
                  f"$p={_ps_quote(lnk)}; $t={_ps_quote(target)}; "
                  "if (Test-Path -LiteralPath $p) { if ($w.CreateShortcut($p).TargetPath -eq $t) { 'ok'; exit 0 }; $m='repaired' } else { $m='created' }; "
                  "$s=$w.CreateShortcut($p); $s.TargetPath=$t; $s.Description='All view pages and dashboards on this machine'; $s.Save(); "
                  "if ($w.CreateShortcut($p).TargetPath -eq $t) { $m } else { 'WARN readback mismatch' }")
        r = _ps(script)
        out = (r.stdout.strip().splitlines() or [""])[-1]
        return out if r.returncode == 0 and out else f"WARN powershell exit {r.returncode}: {r.stderr.strip()[:200]}"
    except Exception as e:  # noqa: BLE001 — a shortcut must never fail the build
        return f"WARN {type(e).__name__}: {e}"


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    import tempfile
    results = []

    def check(cid, ok, note=""):
        results.append(bool(ok))
        print(f"{'PASS' if ok else 'FAIL'}  {cid}  {note}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fs = lambda p: str(p).replace("\\", "/")
        store = td / "WORK"
        files = ["SSLD_A/T01_first/deck.pptx", "SSLD_A/T02_second/頁 面.html", "SSLD_A/readme.html",
                 "SSLD_A/sub/tool/deep.html", "Loose/x.html", "top.html"]
        for f in files:
            (store / f).parent.mkdir(parents=True, exist_ok=True)
            (store / f).write_text("x", encoding="utf-8")
        stores = td / "stores"
        stores.mkdir()

        def emit(paths):
            (stores / "s.derived.json").write_text(json.dumps({"store": "s", "root": fs(store), "cards": [
                {"path": p, "name": "n", "heads": "標題 </script><b>x</b>" if p.endswith("面.html") else "", "ext": p.rsplit(".", 1)[1]}
                for p in paths]}, ensure_ascii=False), encoding="utf-8")
        emit([*files, "SSLD_A/T01_first/vanished.html"])
        pm = td / "PROJECTS.md"
        pm.write_text("| project | status | path | last-checkpoint | next | predecessor |\n|---|---|---|---|---|---|\n"
                      f"| proj-A | **active** — long text (x) | `{str(store / 'SSLD_A')}` (git main) | - | - | - |\n"
                      f"| proj-tool | build | {str(store / 'SSLD_A' / 'sub' / 'tool')} + elsewhere | - | - | - |\n", encoding="utf-8")
        page = td / "pinned.html"
        page.write_text("x", encoding="utf-8")
        base = {"groups": [{"id": "g", "title": "群組"}], "views": [
            {"id": "a", "group": "g", "title": "存在的頁 <b>x</b>", "answers": "問題 & 答案", "path": fs(page), "project": "proj-A",
             "refresh": 'python "C:\\a b\\c.py" --x'},
            {"id": "b", "group": "g", "title": "不見的頁", "answers": "q", "path": fs(td / "gone.html"), "project": "only-pinned"},
            {"id": "c", "group": "g", "title": "也被索引收到的頁", "answers": "q", "path": fs(store / "top.html")}]}
        vj, oh, om = td / "v.json", td / "o.html", td / "o.md"

        def run(d):
            vj.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            try:
                return build(vj, oh, om, stores, pm), None
            except ViewsError as e:
                return 2, str(e)

        code, _ = run(base)
        h, m = oh.read_text(encoding="utf-8"), om.read_text(encoding="utf-8")
        D = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', h, re.S).group(1).replace("<\\/", "</"))
        by = {it["file"]: it for it in D["items"]}
        check("V1 builds both outputs, page declares its class", code == 0 and 'data-page-class="dashboard"' in h and m)
        check("V2 longest registered root wins (proj-tool inside proj-A)", by["deep.html"]["project"] == "proj-tool" and by["deck.pptx"]["project"] == "proj-A")
        check("V3 round = first folder under the project root; root files have none",
              by["deck.pptx"]["round"] == "T01_first" and by["readme.html"]["round"] == "" and by["deep.html"]["round"] == "")
        check("V4 item under no registered project is kept, filed by top folder, marked unregistered",
              by["x.html"]["project"] == "Loose" and any(p["name"] == "Loose" and not p["registered"] for p in D["projects"]))
        check("V5 index row whose file is gone is dropped AND counted", "vanished.html" not in by and D["dropped"] == 1)
        check("V6 a pinned page is not listed twice", "top.html" not in by and any(v["id"] == "c" for v in D["views"]))
        check("V7 missing pinned page is kept with exists=false; project with only pinned pages gets a sidebar row",
              any(v["id"] == "b" and not v["exists"] for v in D["views"]) and any(p["name"] == "only-pinned" for p in D["projects"]))
        check("V8 file URI percent-encoded (space + CJK)", "%20" in by["頁 面.html"]["uri"] and by["頁 面.html"]["uri"].startswith("file:///"))
        check("V9 hostile text cannot close the data script or reach markup",
              h.count("</script>") == 2 and "<b>x</b>" not in h.split('id="data"')[0] and by["頁 面.html"]["title"].startswith("標題 </script>"))
        check("V10 status is cut short; registered project carries it", any(p["name"] == "proj-A" and p["status"] == "active" for p in D["projects"]))
        check("V11 no-script fallback lists existing pinned pages as plain links only",
              f'href="{page.as_uri()}"' in h and "gone.html" not in h.split("<noscript>")[1].split("</noscript>")[0])
        (store / "SSLD_A" / "T03_new").mkdir()
        (store / "SSLD_A" / "T03_new" / "fresh.html").write_text("x", encoding="utf-8")
        emit([*files, "SSLD_A/T03_new/fresh.html"])
        run(base)
        D2 = json.loads(re.search(r'id="data">(.*?)</script>', oh.read_text(encoding="utf-8"), re.S).group(1).replace("<\\/", "</"))
        check("V12 a NEW round in the index appears with nobody registering it",
              any(it["round"] == "T03_new" and it["project"] == "proj-A" for it in D2["items"]))
        check("V13 markdown lists pinned + projects, flags the missing one", "不見的頁（⚠ 找不到檔案）" in m and "**proj-A**" in m and "（未登記）" in m)
        gist = render_gist(load(vj))
        check("V14 gist names function + path, marks missing", "存在的頁" in gist and "(file missing)" in gist)
        code, err = run({**base, "views": [*base["views"], dict(base["views"][0])]})
        check("V15 duplicate id -> refused with the id named", code == 2 and "duplicate id 'a'" in (err or ""))
        code, err = run({**base, "views": [{k: v for k, v in base["views"][0].items() if k != "answers"}]})
        check("V16 entry without `answers` -> refused, key named", code == 2 and "`answers`" in (err or ""))
        vj.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        code = build(vj, oh, om, td / "no-such-stores", td / "no-projects.md")
        D3 = json.loads(re.search(r'id="data">(.*?)</script>', oh.read_text(encoding="utf-8"), re.S).group(1).replace("<\\/", "</"))
        check("V17 no index, no registry -> still builds, pinned pages intact, zero auto items", code == 0 and len(D3["views"]) == 3 and D3["items"] == [])
        side = {"project_groups": {"g": ["proj-tool", "proj-A"]}, "archive_status": ["frozen"],
                "families": [{"id": "fam", "title": "家族", "group": "g2", "members": {"proj-A": "主線", "Loose": "散件"}}],
                "fallback": {"under_home": "g", "other": "g2"}}
        sb = {**base, "groups": [*base["groups"], {"id": "g2", "title": "第二組"}], "sidebar": side}
        code, _ = run(sb)
        P = {p["name"]: p for p in json.loads(re.search(r'id="data">(.*?)</script>', oh.read_text(encoding="utf-8"), re.S)
                                              .group(1).replace("<\\/", "</"))["projects"]}
        check("V18 listed project -> its group, rank = list position (stable, not recency)",
              code == 0 and P["proj-tool"]["bucket"] == "g" and P["proj-tool"]["rank"] == 0)
        check("V19 family member follows the FAMILY's group, unregistered member not dropped into 'unregistered'",
              P["Loose"]["bucket"] == "g2" and P["Loose"]["family"] == "fam" and P["Loose"]["label"] == "散件"
              and P["proj-A"]["bucket"] == "g2" and P["proj-A"]["family"] == "fam")
        check("V20 unregistered project outside any family -> 'unregistered'", P["only-pinned"]["bucket"] == "unregistered")
        code, _ = run({**sb, "sidebar": {**side, "archive_status": ["build"]}})
        P2 = {p["name"]: p for p in json.loads(re.search(r'id="data">(.*?)</script>', oh.read_text(encoding="utf-8"), re.S)
                                               .group(1).replace("<\\/", "</"))["projects"]}
        check("V21 archive status wins over the listed group", P2["proj-tool"]["bucket"] == "archive" and P2["proj-A"]["bucket"] == "g2")
        pl = [{"name": "r", "registered": True, "status": "active", "root": fs(store / "SSLD_A")},
              {"name": "o", "registered": True, "status": "active", "root": fs(td / "elsewhere")}]
        place(pl, {"fallback": {"under_home": "g", "other": "g2"}}, home=store)
        check("V22 unlisted registered project falls back by root (under home vs other)",
              pl[0]["bucket"] == "g" and pl[1]["bucket"] == "g2" and pl[0]["rank"] == 999)
        code, err = run({**sb, "sidebar": {**side, "project_groups": {"nope": ["x"]}}})
        check("V23 sidebar group id not in `groups` -> refused, id named", code == 2 and "'nope'" in (err or ""))
        code, err = run({**sb, "sidebar": {**side, "families": [{"id": "f", "title": "t", "group": "zz", "members": {"a": "b"}}]}})
        check("V24 family naming an unknown group -> refused", code == 2 and "'zz'" in (err or ""))
        desk = td / "desk top"
        desk.mkdir()
        tgt = td / "o.html"
        r1 = ensure_shortcut(tgt, desk)
        lnk = desk / SHORTCUT_NAME
        back = _ps(f"(New-Object -ComObject WScript.Shell).CreateShortcut({_ps_quote(lnk)}).TargetPath").stdout.strip()
        check("V25 shortcut created, TargetPath reads back as the launcher", r1 == "created" and back == str(tgt), f"{r1} -> {back}")
        m0 = lnk.stat().st_mtime_ns
        r2 = ensure_shortcut(tgt, desk)
        check("V26 second run leaves a correct shortcut untouched", r2 == "ok" and lnk.stat().st_mtime_ns == m0, r2)
        r3 = ensure_shortcut(td / "other.html", desk)
        check("V27 shortcut pointing elsewhere is repaired, not duplicated", r3 == "repaired" and len(list(desk.glob("*.lnk"))) == 1, r3)
        check("V28 missing folder -> WARN, no exception", ensure_shortcut(tgt, td / "nope").startswith("WARN"))
    print(f"\n{'ALL PASS' if all(results) else 'FAILED'} {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if "--selftest" in sys.argv:
            sys.exit(selftest())
        if "--gist" in sys.argv:
            print(render_gist(load()))
            sys.exit(0)
        code = build()
        res = ensure_shortcut(OUT_HTML, desktop_dir())
        print(f"view-launcher: desktop shortcut {SHORTCUT_NAME}: {res}")
        sys.exit(code)
    except ViewsError as e:
        print(f"view-launcher: FAIL — {e}  (repair: {VIEWS})")
        sys.exit(2)
