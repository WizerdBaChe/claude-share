# CLAUDE_SHARE｜跨 agent 規則與機制分享

> **中文摘要｜Chinese summary**：這是一個從個人 Claude 設定環境整理出的公開
> share repo。每個子資料夾是一個有範圍、有來源與有驗收界線的 share；它們不是
> 自動同步的完整環境，也不會把 Claude host-specific 設定直接偽裝成 Codex／
> ChatGPT skill。
>
> **English summary**: This repository contains reviewed, scoped shares extracted from a
> personal Claude configuration environment. Each directory has its own provenance,
> adoption notes, and acceptance boundary. The repository is not an auto-synced clone
> and does not turn Claude-specific host settings into a fake Codex/ChatGPT skill.

## 快速導覽｜Quick guide

| 你要做什麼 | 中文入口 | English entry |
|---|---|---|
| 第一次閱讀 | 先看 Lane A，再讀目標 share 的 README | Follow Lane A, then read the target share README |
| 回來更新 | 先讀 Lane B、CHANGELOG 與 manifest，再信任任何現況 | Follow Lane B, CHANGELOG, and the manifest before relying on state |
| 要安裝 | 先讀 ADOPTERS.md，再讀目標 README 與 acceptance checklist | Read ADOPTERS.md, the target README, and its acceptance checklist |
| 要跨平台搬移 | 讀 `interop-layer/`；不要直接複製 `CLAUDE.md`、hooks 或 settings | Use `interop-layer/`; do not copy CLAUDE.md, hooks, or settings verbatim |
| 要收錄新資料 | 讀 `tools/COLLECTION-RULES.md`，完成後跑 share gate | Read COLLECTION-RULES.md and run the share gate before publishing |

Public-facing extracts from a personal `~/.claude` configuration environment,
shared piecemeal. Each subfolder is one self-contained share; content is
reviewed for local machine identifiers before being copied here, and since
2026-08-14 that review is a script, not a habit — see `tools/`.

Licensed under [MIT](LICENSE).

---

## 🆕 架構圖能力集合｜Architecture-diagram capability set

**→ [`architecture-diagramming/capability-set.html`](architecture-diagramming/capability-set.html)** — five views, self-checking, regenerable.
Clone and open it in a browser; the page measures its own geometry on load and
prints the verdict in its header.

Most architecture diagrams are unfalsifiable. They look complete because
whoever drew them filled in the parts the data did not have, and nothing in the
pipeline could tell the difference. This set makes that expensive on three
independent fronts, and then it does the thing that is easy to promise and
awkward to actually do: **it turns the instrument on itself.**

The page above is the scan of this very mechanism, produced by the mechanism.
Not a mock-up of one.

| What it claims | How you check it without trusting us |
|---|---|
| **Nothing on the diagram is invented.** Every node and every edge carries an `ev` evidence anchor naming the file it was read out of. | The schema *rejects the build* without one — delete an `ev` and `node capability-set.build.mjs` throws instead of drawing. The anchors are visible in the model. |
| **The geometry is measured, not eyeballed.** Label overlap, anchors on borders, viewBox clipping, grid snap, edges through nodes, crossings vs a declared budget, an 11px font floor, dangling `url(#id)` references. | Open the page: the header says `幾何自檢：PASS（5 視圖）` and the report below lists 1,493 measured label pairs. It ran in your browser, on your machine, on the bytes you have. |
| **The instrument is calibrated in both directions.** A checker that has never gone red is not evidence. | Rename one marker id out of the `<defs>` block and reload: exactly 25 `dangling-reference` diagnostics — the exact count of references to it. Rebuild and it returns to 0. We ran that; you can re-run it in a minute. |
| **The artifact is frozen by a receipt.** | `build()` prints a sha256. Re-run it with no edits and the bytes are identical, so a diff means something changed. Pinned to LF in [`.gitattributes`](.gitattributes) — without that pin a CRLF checkout silently invalidates every receipt with all tests green. |
| **The gaps are a deliverable, not a disclaimer.** | The page's last table is its own gap report: five entries, including one marked `inherent` (a human appearance judgement cannot be machine-checked) and one marked `by design` (no timing view, because none of the five questions was a timing question). |

What it is made of — four layers, one loop, two entry points:

- **理論 (theory)** — which diagram answers which question, and what each one
  structurally *cannot* prove. One home, referenced by everyone else, never copied.
- **生產 (production)** — the source-data gate, structural text model first,
  carrier choice, and a three-rung verification ladder.
- **稽核 (audit)** — reconstruct the views from the *code*, not from the docs,
  run the same instrument, and file the result as next round's baseline.
- **執行 (execution)** — `archdiag/`: the library that makes the above run.
  Its own motivating defect is worth the price of admission: two copies of a
  self-check framework drifted apart **within one day**, and both reports still
  printed PASS. A checker that can fork is worse than no checker, because it is
  still being believed.

Read the mechanism: [`architecture-diagramming/README.md`](architecture-diagramming/README.md) ·
verify it yourself: [`ACCEPTANCE.md`](architecture-diagramming/ACCEPTANCE.md) (blind-runnable, fourteen items).

---

## 從這裡開始：選一條閱讀路徑｜Start here — pick your lane

**Never read this repo before?** → Lane A.
**Read it before and coming back?** → Lane B. Do not skip it. "I looked at this
already, it probably hasn't changed" is a documented failure mode in this
repo's own history, not a hypothetical.
**Going to copy files onto a machine?** → Lane C, and read
[`ADOPTERS.md`](ADOPTERS.md) first.

### Lane A — 第一次閱讀｜First read

| Order | Read | Why |
|---|---|---|
| 1 | [`environment-guide/PHILOSOPHY.md`](environment-guide/PHILOSOPHY.md) | Ten beliefs everything else hangs off. Skip it and the rules look arbitrary. |
| 2 | [`global-claude-md/CLAUDE.md`](global-claude-md/CLAUDE.md) | The always-loaded preferences file. Self-contained; every rule states its trigger. |
| 3 | [`claude-ops/ops/OPS.md`](claude-ops/ops/OPS.md) | Entry point and routing table for the rules layer. Read the table, not the whole layer. |
| 4 | [`AGENTS.md`](AGENTS.md) | One line per tracked file, when you want the map rather than the argument. |

`Global_skill_update.md` is the narrative of how this environment got its shape.
It is the most informative file here and also 67 KB and **frozen at 2026-08-11**.
Read it when you want history, not when you want current state.

### Lane B — 回訪與更新｜Returning reader

The repo looks stable and is not. Three of the changes that mattered most were
small diffs that inverted a meaning:

- a target went **SYNC OFF** while its row stayed in the registry;
- the method layer was **retired entirely** (2026-08-11) — content that used to
  ship now does not, and the reason is that it never worked;
- a 2026-08-11 finding was "corrected" the same day and the correction was
  **wrong and is now retracted**. Reading either version alone misleads you.

So:

```git bash
git log --oneline <the-sha-you-last-read>..HEAD
```

Then check `CHANGELOG.md` for the dated entry, and re-read these four before
relying on anything you remember:

| File | What silently inverts in it |
|---|---|
| [`interop-layer/MIGRATION-MAP.md`](interop-layer/MIGRATION-MAP.md) | File-target, package, and import registry; portability classes; inbound-dependency and self-contained-skill rules |
| [`tools/share-manifest.toml`](tools/share-manifest.toml) | Which dependencies are declared not-shipped, and what fallback you actually get. **2026-08-14: three hook entries here were wrong for a month** — classified "machine-bound" without re-checking. They ship now. **2026-08-16: the `outputs/` entry was wrong the same way** — called a scratch directory, actually the retrospective layer — and a `[[collected]]` entry claimed two leak gates were identical when they were not. Both corrected in place; neither history deleted. |
| [`claude-ops/ops/rule-registry.md`](claude-ops/ops/rule-registry.md) | The current value of every cap and standing ruling, plus its value history |
| [`claude-ops/ops/environment.md`](claude-ops/ops/environment.md) | Machine facts, per-block dated. Every one of them expires. |

If you are re-reading in order to answer a question, answer it from the file,
not from memory of the file. `claude-ops/ops/OPS.md` states the same rule for
the model: any mechanism name is an example, verify before relying on it.

### Lane C — 準備採用或安裝｜Adopter

1. [`ADOPTERS.md`](ADOPTERS.md) — where to put this repo (and where not to),
   what it names but does not ship, and which symptoms are your platform rather
   than a defect here.
2. The `README.md` of the specific share you are copying — each carries its own
   install steps and de-identification notes.
3. [`interop-layer/acceptance-evals.md`](interop-layer/acceptance-evals.md) — a
   port with no eval run is not a finished port.

## Shares｜分享內容

| Folder | Contents |
|---|---|
| `global-claude-md/` | The top-level global `CLAUDE.md` entry point itself — conditional working preferences for Git workflow, environment/shell syntax, interaction style, engineering judgement, frontend layering (FSD), skill routing, project-operations tiering, file hygiene, and reply language. |
| `claude-ops/` | Anonymized snapshot of the operational rules layer: authority, command loop, dispatch, judgment, maintenance, bootstrap, evolution. |
| `skill-toolkit/` | Portable AI-agent skills and a bilingual trigger dictionary, reviewed for personal identifiers and local paths. |
| `interop-layer/` | Cross-agent migration layer: compiles the portable rules subset into file-based targets and records separate ChatGPT import/package rules. Method depth is delegated, not shipped; dependent skills are out of scope. |
| `environment-guide/` | Human-facing philosophy, operator manual, and commit-message conventions, including a full migration checklist. **New 2026-10-02:** `KNOWLEDGE-PACKS.md` (what a knowledge pack is, the criteria one must meet to be registered, depended on or shared, and a dated status table — it stands in for the three packs that stay withheld) and `LABEL-REGISTRY.md` as a template (the rules for enumerable labels, with the family table reduced to its header). |
| `hooks/` | **New 2026-08-14, thirty-five mounted hooks since 2026-10-10** (two notices added that day — an absent-user approval notice and a worktree stash notice; thirty-three on 2026-10-02; twenty-one on 2026-09-12; this round added eight new hooks and reversed the exclusion of five whose only private dependency was a tool that now ships under `instruments/`). The mechanical enforcement layer the rules had been citing without shipping: destructive-command deny-list, subagent model cap, browser-pane measurement and scope guards, session health nudge, four shadow probes (delivery gate, context runway, fieldwork threshold — retired 2026-09-12 and shipped unmounted — and rule-load logger), the compact-recovery set (pre-compact bookmark, post-compact pointer card, transcript read-window guard, and **new 2026-09-07** a PostCompact loss recorder over a shared snapshot library), and four shell/git guards — the Bash tool's silent transport defects, two Windows-PowerShell traps that both fail in the direction the author does not expect, and a wrong-branch commit guard written after the prose ritual ran and did not gate. Plus the mounting template. All fail-open, and three of the four shell/git ones ANNOTATE rather than deny, because their backtests said the gate cannot determine intent. **New 2026-09-12:** the literature-access guard with its policy table, a guard on writes into any tree that carries its own collection rules (this one included), a worktree scope guard, and a dispatch-and-commit notice. |
| `compact-recovery/` | **New 2026-08-16, extended 2026-09-07.** Post-compact recall as an operating mode: a PreCompact/SessionStart bookmark-and-pointer-card bridge over the four hooks above, plus the digest generator (`preserve.py`) their grep-first ladder leans on — what a `/compact` summary drops stays recoverable at on-demand token cost. Ships with a nine-item real-fire acceptance checklist, and with one gap stated in its own README rather than left to be discovered: the recorder ships, its audit tool does not, so the loss log it writes has no reader here. |
| `red-team/` | **New 2026-08-17.** Adversarial review made machine-checkable: a prompt shape that makes fabrication expensive, a mechanical anchor/scope gate that separates a citation slip from an invented quote, and an adversarial layer that sends each finding to a refuter which may not be its author. Layers 2–4 need no model at all. Ships with a blind-runnable acceptance checklist. |
| `architecture-diagramming/` | **New 2026-08-27, executable half added 2026-08-29.** The architecture-diagram capability set — theory (view selection + integrity instrument, two `product-design-thinking` references), production (`diagram-authoring`), audit (`code-review-deep-checklist` Mode B view layer) — packaged as one mechanism: integration map, install set, and a fourteen-item external acceptance checklist. The skills live in `skill-toolkit/skills/`; this folder is the loop, its verification, and now `archdiag/` — the library that turns a view model into a self-checking HTML deliverable with a sha256 freeze receipt. |
| `instruments/` | **New 2026-09-12, widened 2026-10-02 to forty-three directories, forty-seven since 2026-10-10** (a shared hook-backtest harness, a mod review gate, the external-discussion search, a design-token key gate). Started as the two verification tools shipped rules name as their own enforcement: `page-fill-gate` (does a human-read HTML page use the width it is given — calibrated by a known-bad and a known-good fixture on every run) and `check_cap_binding.py` (does each cap constant in a hook still equal the value the rule text states). The owner's 2026-10-02 ruling added the source's method tools (the process ledger, lesson intake, feedback pool, three PPTX gates, quote evidence, the shell-transport instruments, tree-noise, tracking-refs and the rest), every hook's hand-run test suite, the lint and proof-of-life instruments, and two monitoring tools (`system-hmi`, `view-launcher`) as templates. Sub-paths match the source, so `instruments/<x>/` copies to `~/.claude/tools/<x>/`; what stays out of `tools/` is the operator's personal stores and carriers, each with a reason in the manifest. |
| `agents/` | **New 2026-08-14, ten since 2026-10-10** (`cheap-worker`, a cheap-tier mechanical worker that carries no user instruction layer; nine since 2026-09-07). The subagent definitions `claude-ops/ops/20-dispatch.md` routes to, each with a `tools:` capability allowlist and a defined output contract. The newest, `work-card-executor`, runs one build-ready work card to its machine-checkable acceptance and stops at any fork the card does not settle. |
| `mods/` | **New 2026-10-10.** Two Claude Code mods (in-process TypeScript plugins, 2.1.287+): the subagent model cap as a mod, and an observe-only feedback observer. Both run their tests under `claude plugin test`. |
| `model-bench/` | **New 2026-10-08, rounds 3–5 since 2026-10-10.** A tier-routing benchmark for the dispatch table: twelve tasks with machine gates, run per model × effort; reports, run records and a general-audience explainer post. Share copy of a tool whose canonical home is the source workstation. |
| `thinking-notes/` | Twelve numbered design-thinking notes. Argument, not policy — nothing there binds a reader. |
| `tools/` | The publishing gate — leak, placeholder, reference-disposition, structure, collection-provenance and dead-declaration checks, plus an opt-in source comparison — and `COLLECTION-RULES.md`, the procedure for deciding what may be collected in the first place. Its two procedures are worth reading even if you never collect: **A** for a file that is not here yet, **B** for one that is, because running A over B's files is what a 2026-08-16 refresh did to six deliberate decisions. |

The ChatGPT/Codex literature package moved on 2026-09-18 to its own public
repository: [`WizerdBaChe/literature-search-chatgpt`](https://github.com/WizerdBaChe/literature-search-chatgpt).
This repository remains the Claude-oriented share collection; a future Claude
adapter can be published with its own host-labelled package boundary.

## 查找入口｜Where things are

| If you want | Read |
|---|---|
| A one-line map of every tracked file | `AGENTS.md` |
| To adopt any of this on a machine | `ADOPTERS.md` |
| How the source environment evolved, rule by rule (frozen 2026-08-11) | `Global_skill_update.md` |
| Why a rule holds its current value, going forward | `claude-ops/ops/rule-registry.md` |
| When each share was copied and what changed | `CHANGELOG.md` |
| The rules layer itself | `claude-ops/ops/` (start at `OPS.md`) |
| Installable skills | `skill-toolkit/skills/` (inventory in `skill-toolkit/README.md`) |
| Standalone ChatGPT/Codex plugin | [`literature-search-chatgpt`](https://github.com/WizerdBaChe/literature-search-chatgpt) |
| A tool a shipped rule names as its enforcement | `instruments/` (start at `instruments/README.md`) |
| Why any of this is shaped this way | `environment-guide/PHILOSOPHY.md` |
| What this repo names but does not ship | `tools/share-manifest.toml` |
| Where a collected file came from, and every edit made on the way | `tools/share-manifest.toml` `[[collected]]` |
| The rules for collecting anything else out of the source environment | `tools/COLLECTION-RULES.md` |

## 共通約定｜Conventions

- One git repo at this root; each share is a subfolder, so future additions land
  as new folders/commits without touching prior shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
- No release tags, version numbers or content digests, on purpose. Pin a commit
  SHA on your side; see ADOPTERS.md for the reasoning.
- Before any push that touches shipped content: `python tools/share_gate.py`
  must exit 0. If you are COLLECTING rather than reading, add
  `--source <your ~/.claude>` — that enables the one check which can see a
  declared edit that a refresh quietly reverted.
