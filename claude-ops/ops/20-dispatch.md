# Dispatch Rules — handing work to subagents without getting burned

Written to be followed mechanically — no taste required. Numeric thresholds are
defaults, adjustable per project but never silently. Tier names ("cheap / mid /
top") are roles, not model ids — map them to the current environment's actual
models at session start; never assume ids from memory.

## §0 Establish the environment first (once per environment, never from memory)

Check and record: available model tiers, the subagent/dispatch mechanism,
whether an independent second CLI agent exists (a genuinely different vantage
point for red-teaming), and whether scripted calls to your own CLI behave
normally (supervisor setups sometimes shadow the command).

**Where to record**: `ops/environment.md` — one file per environment holding
the tier→model mapping, cost-cap policy, and available dispatch mechanisms.
Read it before the first dispatch of a session; update it when facts change
(it lists its own refresh triggers). If it's missing or stale, re-establish
the facts first — never dispatch on remembered model ids.

**A NEW `agents/*.md` definition is not dispatchable when it is written.** The
roster the Agent tool validates against is a snapshot the harness refreshes on
its own schedule — no documented trigger, no setting, and the type check runs
before any hook, so nothing of ours sees the failure. After authoring a
definition, spend one read-only PROBE dispatch before relying on it; while it
returns `Agent type '<name>' not found`, run the work on an existing definition
plus a `model:` override and journal that as an interim policy, so unwinding it
is a status flip rather than a rewrite. The later "New agent types are now
available" notice is the all-clear. (`lessons.md` L-046.)

## §1 Core rule: the dispatcher does no fieldwork

The dispatcher's job: read tickets, dispatch, receive conclusions, verify,
backfill, talk to the requester. Every raw file the dispatcher reads itself
permanently occupies main-context space.

**Delegate when any of these holds** (defaults): touches >3 files or >200
lines; repo-wide scan / broad grep / read-many-files-to-answer; web research
beyond a quick ≤3-source lookup; writing a new script/module; batch edits
(isolate in a worktree if large).

**Do it yourself when**: single-file edit under ~50 lines; urgent
stop-the-bleeding fix; taking over after a worker failed the same subtask
twice; the final write of any rule-tier file (workers draft, main session
writes — see `40-maintenance.md` §1).

✅ "Find every caller of X across the repo" → search subagent returns 12
`file:line` refs; main context grows by 12 lines.
❌ Dispatcher greps the repo itself and pages through 3,000 lines of matches —
the rest of the session now pays rent on that noise.

**§1a Degraded environments (no subagent mechanism)**: the separation of
duties is the invariant; the mechanism is negotiable. Run scanning as a
separate phase whose raw output is reduced to conclusions + refs BEFORE the
decision phase reads it; simulate reviewer separation with a fresh pass under
a different role framing ("review as tomorrow's inheritor, no memory of
writing it"). State the deviation explicitly, and wherever it lands in a FILE
(delivery note, ticket, phase log) tag it `DEVIATION:` — an unmarked deviation
is invisible to every sweep, which is how "no mechanism available" quietly
becomes "no mechanism used" (`lessons.md` L-011 P2; sweep check 12).

## §2 The dispatch contract (all five parts, or it doesn't go out)

1. **Goal AND motivation** — a worker that knows why can make correct calls on
   details you didn't spell out.
2. **Machine-checkable acceptance + output-format contract** (exact structure,
   schema, verbatim-preserve fields). Format drift is a more common failure
   than wrong content. **How strict the schema may be routes by answer-shape
   class** (adopted 2026-08-16; evidence:
   `reports/2026-08-16-machine-first-verification-scoping.md` §五/§7.5/§八):
   **(A) enumerable outputs** (listings, extractions, to-spec files — shape
   known) → full schema up front, machine checks before AND after; **(B) a
   verdict plus open-ended reasons** (refute/confirm, pass/fail) → pin ONLY
   the verdict field, reasons stay free-form, and a format failure must never
   decide the verdict; **(C) open-ended judgment** (what's wrong / what's
   missing — the shape IS the answer's value) → NO schema up front: acquire
   free-form first, then convert each claim into a verifiable unit and
   machine-check after. Measured 2026-08-16 (2×2 arms, same task/model): a
   schema-first contract suppressed the INVESTIGATION itself (1 tool call vs
   8/18), not merely the output's shape; free-first cost ~1.6× tokens —
   the price of the investigation, not overhead. Orthogonal to the class:
   each acceptance layer stacked on one output still rules only on what IT
   can determine (global gate rule; `lessons.md` L-019). State the goal, not
   the proof ritual — "prove your own work passes" invites an expensive
   self-verification loop. The worker self-checks FORMAT compliance only;
   ACCEPTANCE verification belongs to the dispatcher with fresh context
   (`10-command-loop.md` Step 6).
3. **Report format** (§7's fields included) — the shape of the conclusion +
   where artifacts land.
   Where artifacts land includes INCREMENTAL on-disk evidence: one numbered
   log per attempt, outputs written as they are produced, probes with their
   own logs — a worker can die mid-task on a transport/auth error (measured
   2026-09-15: HTTP 403 mid-card, transient; `ops/lessons.md` L-099) and the
   successor's brief then names the last log and says "resume", never "redo".
   A worker whose only output is its final report has no resumable state.
4. **Redlines** — the explicit do-not-touch list (rule-tier files, production,
   anything the project protects).
5. **Self-sufficient materials** — copy specs/references the sandbox may not be
   able to reach into a path the worker CAN read. A worker that can't read what
   it needs tends to fabricate a plausible answer rather than report the gap.

**A brief that dispatches a worker into a governed record — a manifest, ledger
or audit file that is itself published, reviewed or gated — carries that
record's own record-writing rule.** Conditional, so not a sixth contract part:
it fires only when the worker WRITES into something shared. The worker holds
one shard and never runs the merge-time gate, so a rule enforced there is
unreachable from where it stands, and nothing in the fragment's own acceptance
fails without it — everything it would have caught surfaces after the merge, in
the merged file, at the dispatcher's cost. Shape, the ✅/❌ pair and the
measured case: `ops/references/dispatch-templates.md` (fragment-writing
briefs).

**When N workers get slices of ONE class of work, part 2 is a DECISION
PROCEDURE, not a task list — and it is exhaustive down to the "this is not
mine" branch.** Conditional, like the clause above: it fires only on a fan-out
where the slices share a kind. The reason is not tidiness. Four workers meeting
the same ambiguous shape each invent a different resolution, and the dispatcher
cannot align them afterwards — the outputs are no longer comparable, and the
one thing a fan-out was supposed to buy (uniform treatment of a class) is
exactly what is lost. A task list says WHAT to produce; a decision procedure
says HOW TO DECIDE, so only the decisions differ per slice, never the method —
and the "report, don't fix" branch is what makes it exhaustive, paired with §7
so a worker knows what a report LOOKS like. Measured instance (S1/S2/S3
branches, 17 suites, 2026-09-09): `ops/references/dispatch-templates.md`
"Fan-out decision procedure".

## §3 Gotchas when dispatching to an external CLI agent (verify in your env)

1. Background jobs: redirect stdin from `/dev/null`, or some CLIs hang waiting.
2. Launch from a genuine scratch dir, not an OS-protected folder — some
   sandboxes silently fail to read protected paths and fabricate instead.
3. Always wrap with an outer timeout — some agents hang silently. The same
   holds for any in-session background run or probe: cap it at ~10× a measured
   baseline of the same job (floor 5 min); no new log line past the cap is a
   hang, not a slow run — kill the worker AND its server child, log the kill in
   the ledger, and keep the hung run's log under its own name, never reuse the
   path for the retry (`ops/lessons.md` L-098: 45 min found by a process
   listing, log then overwritten).
4. Non-git working dirs may need an explicit "trust this directory" flag.

## §4 Model / effort assignment (two axes: model × effort)

The current environment's tier→model-id mapping, cost cap, and
enforcement mechanism live in `ops/environment.md`; this table stays in role
terms. **Cap rule**: everything above "mid tier + high effort" requires
explicit per-instance user approval (mechanically enforced where the
environment supports it — see `environment.md`). **A guard that did not answer
is not an approval**: a command hook that times out is a PASS to the engine
(default `onFailure: "continue"`; since 2.1.295 a hook may set
`onFailure: "block"` to turn timeout/crash/exit≠0,2 into a block — not yet
set on any local guard, see a dated CC-version reconciliation report under the source's `reports/` tree, which this repo does not ship), so
a dispatch that went out with no `model` (or an over-cap one) runs on the
parent's model — stop it (TaskStop) and re-dispatch with `model` set; record
the escape as a `feedback` row (`hook:model_cap_guard`). Never "left"
(2026-10-02, a local session: two of eight parallel dispatches escaped this way).

| Task shape / severity | Model tier | Effort |
|---|---|---|
| Summarize / reformat / dictionary-style lookups | cheap | medium |
| Translation / extraction / to-spec outputs — anything with a hard machine-checkable gate | cheap + explicit output-format contract (a hard gate substitutes for tier quality on internal work; outward-facing "always top-tier" project rules still win) | medium |
| Multi-constraint format contract | cheap — not mid (mid adds punctuation and length by habit) | medium |
| Search / inventory / read-many-files | cheap, dispatcher POST-SORTS the output mechanically (cheap keeps the set exact and orders by natural line number); mid only when order is contractual and no post-processor exists | medium |
| Write a script/module; agentic repair against an immutable test gate | cheap when the verification regime is explicit (hidden tests, hashed tests + suite run by the gate); mid otherwise; always review | high |
| Red-team / review | a different model family/tool than the author if one exists; else fresh-context mid — cheap is clean when the acceptance layer is ANCHORED (`red-team/` layers 2–4). **Reviewer ≠ author, always** | high |
| Research / multi-source verification | mid; cheap when the sources are LOCAL and every citation is machine-checked verbatim | high |
| Aggregation over a large context block INLINE | mid; never inline it into a cheap dispatch — the prefix pushes the prompt over the cheap tier's long-prompt pricing step; file + Read, or one session | medium |
| Summarising UNTRUSTED content (injection present) | cheap; the gate checks the file system AND the output for the planted token | medium |
| Taste, ambiguous judgment, policy wording | main session — not delegable, see `30-judgment.md` R6 | — |

The table SUMMARISES the latest `tools/model-bench` round (cheapest arm that
passes every repetition, per row) and changes when that register does, never
by hand. Cheap effort floor is medium (user ruling 2026-10-08): no `low`;
`high` only for code rows with an explicit verification regime; `xhigh` buys
thinking time, not passes. **A cheap dispatch carries no user instruction
layer** — CLAUDE.md, rules and session injections are noise to mechanical
work: route it to `cheap-worker` (roster below) or `Explore`; `general-purpose`
loads the whole layer (`references/harness-measurements.md` "Dispatch
prefix") and is for tasks that need it.

Where the dispatch mechanism supports a machine-enforced output schema (see
`environment.md`), use it instead of prompt-side format instructions — format
drift is the most common cheap-tier failure, and a schema eliminates it.
(Applies to class-A/B outputs per §2's answer-shape routing; a class-C task
takes no up-front schema on either mechanism.)

## §4a Which PATH: subagent or external tier (ask before §4's table)

Two dispatch paths exist. §4 above sizes work WITHIN the subagent path; this
picks the path. Facts, entry point and gates: `environment.md` "External
dispatch tier".

> **Share note.** `tools/extdispatch/` (the dispatcher, `allowlist.txt`, and
> every gate below) is source-only (excluded-by-decision except its
> `red-team/` acceptance scripts, `tools/share-manifest.toml`). This whole
> external path is design here, not something this copy can run; every task
> goes to a subagent instead.

**Send it externally when ALL of these hold** — one NO sends it to a subagent:

- the target project is in `tools/extdispatch/allowlist.txt`;
- the work is not ABOUT `.claude`-class internals (see §4b);
- the deliverable is machine-checkable — a schema, an anchored finding list, a
  file that either compiles or does not. External output is accepted by
  verification, never by reading it and finding it plausible;
- latency is not the binding constraint (an external run is minutes, and free);
- the deliverable comes BACK as text — findings, lookups, verdicts, a proposed
  patch — and the main loop integrates it. Work that writes into a project's
  working tree stays in-house (user ruling 2026-09-23: tier environments differ
  — shell, paths, installed tools — and edits made from a different environment
  confuse the tree). The `code` / `agentic` / `mechanical` profiles run only
  when the user asks for them by name;
- **red-team / review: prefer external by default.** It is a genuinely
  different model family, which the subagent path cannot offer at all.

**Keep it in a subagent when** the work needs main-repo context, touches
anything unlisted or private, needs a tool the external worker lacks, or is
judgment/taste (which is not delegable at all — `30-judgment.md` R6).

Profile → task shape, prompt shape (format first line, evidence anchor, explicit
file scope, licensed empty answer), acceptance and failure signatures:
`ops/references/external-dispatch.md`. Chains and live health:
`extdispatch.py status` — that output beats any table.

**A prompt names the ROUTING TABLE, never a tool surface.** Naming a browser, a
fetch command or a specific client hands the worker a path whose legality the
dispatcher has not checked — and if that path is barred, the violation is the
dispatcher's, already committed at dispatch time, with the worker merely
executing it. Keep the licensed empty answer reachable: a worker that stops at
a barred route and reports the gap has succeeded (`ops/lessons.md` L-075;
literature case and the 5-step ladder: `rules/literature-access.md`).

**The one fetch command a literature wave DOES name is `fetchsrc.py`** — it is the
routing table in executable form: it consults the host policy before every request,
keeps the per-host and per-run caps in its manifest, and prints `HAND-TO-USER:`
itself, so the licensed empty answer stays reachable. Name it as the only route for
text that will be cited, put its `--run` folder under the brief's output folder, and
write no brief rule that reads as excluding it — it writes text only (PDFs are parsed
in memory) and its scratch moves with `LSE_FETCH_SCRATCH`. The measured 2026-10-03
exclusion (L-075 mirror shape), why the caps live in `fetchsrc.py` and not the host
guard, and the promotion trigger: `rules/literature-access.md` "The instrument side".

## §4b Redlines and disclosure for external dispatch

- **Never externally**: `~/.claude` and its subtree, plus the operator's own
  share and publication trees — refused mechanically (exit 3).
- **The redlines bind EVERY external tier, Codex included.** The Codex CLI is
  reached directly, not through extdispatch: entry point `codex exec`, prompt on
  stdin, house flags (the full line and why each flag is there: `environment.md`
  "Codex CLI tier"). `hooks/codex_dispatch_guard.py`
  denies a codex call whose `-C`/cwd/`--add-dir` or prompt/attachment file lies
  under a redline, reading the same `REDLINE_PREFIXES` extdispatch enforces.
  No allowlist and no grant on this tier (user ruling 2026-09-23) — so the
  unlisted-project STOP below does not fire for Codex, and the disclosure line
  above is its only per-call control besides the redline.
- **Never as a TASK**: a project's own `.claude`-class internals. Not
  mechanical — a worker's `grep` cannot be gated by path, so the dispatcher
  owns this one. Authored in-house, verified by skills/subagents.
- **Disclose at dispatch time** (user ruling): which project is going out, to a
  free external tier, and why it is safe to send. Free-tier use needs
  disclosure, not approval.
- **Shard the card** by real sub-need and stage, so one dispatch never carries
  a whole picture of a codebase.
- **Unlisted or private project → STOP and ask**, every time (extdispatch
  tiers).

## §5 Escalation and de-escalation

- Cheap-tier fails once → CLASSIFY before escalating. (a) Format / order /
  contract drift (the set or the facts are right, the shape is not): add the
  contract line or a mechanical post-processor and re-dispatch the SAME tier
  (measured 2026-10-08: every cheap miss on search was order, every one on
  format was punctuation). (b) Wrong facts, miscounts, arithmetic drift over a
  large context: one tier up — same-tier retries reproduce the failure.
- Same subtask fails twice → diagnose the reasons first (`30-judgment.md` R1):
  the SAME reason twice = an environment problem → fix the environment, don't
  escalate; two DIFFERENT reasons = the task exceeds the tier → top tier or
  take over in the main session, carrying the COMPLETE failure trail (both
  rounds' prompts + errors) — never discard it.
- Once the top tier cracks a pattern → write it as explicit steps, push batch
  execution back down to the cheap tier.
- **Two retries max per problem** (default): the third attempt must change
  method, model family, or stop and ask.
- External quota exhausted → schedule a retry at the reset window or switch
  agents; don't idle.

✅ Escalate with both failed prompts attached → the stronger model sees how
its predecessors died.
❌ Re-send the identical prompt to the identical tier a third time "in case it
works now".

## §6 Dispatch templates (fill brackets; contract parts are non-negotiable)

Five shapes — **T1 search/inventory** (read-only), **T2 implementation**
(spec as a file, acceptance commands), **T3 refactor/batch edit** (the
do-not-touch list outranks the change list; ambiguous cases → "needs a human",
never guessed), **T4 research** (read-only + one report; live search, every
claim cited), **T5 review/red-team** (read-only, never the author; PASS/FAIL
first line + ranked WARNING list + ≥3 specific challenges). Field lists, the
worked §2 ✅/❌ example, rules of thumb: `ops/references/dispatch-templates.md`.

## §7 The report contract (what a worker hands back)

- Conclusions + `file:line` refs only; large artifacts to disk, path returned.
- Delivery summary: what was done (≤5 lines) + what was verified (commands +
  key output lines) + honesty clause (what couldn't be reached, what was
  skipped, and why) + **weakest point** (the ONE delivered item most likely
  to be wrong, with its location) + **brief gaps** (where the brief forced a
  guess, and the reading taken). Free text, never schema (§2 class C); "none"
  needs a reason; anchored verdict reports are exempt. Why: registry
  `DISPATCH_REPORT_WEAKEST_POINT`.
- Any numeric or factual claim carries a source; no source → label
  "unverified". Never fabricate.

## §7a Supervising a dispatched ticket (do the registration AT dispatch time)

A dispatched session cannot be identified after the fact (only the OPENING
user turn binds; measured 2026-08-21), so registration happens AT dispatch:
`hooks/session_board_register.py` writes the board entry on `spawn_task`.
**You still owe three things** — a distinctive opening sentence (it becomes
`match`), the `deliverables` field (`[]` = decided none, `null` = nobody
decided), and the real cwd when the ticket starts in a worktree. `UNBOUND`
right after dispatch means the hook did not run: find the cause, never re-add
by hand. Field detail, the board/`list_sessions` authority split and the
shared-tree rule lines: `ops/references/ticket-supervision.md`.

> **Share note.** Neither half of that mechanism ships here: the registering
> hook (`hooks/session_board_register.py`) and the ticket board it writes into
> (`tools/session-board/`) are both declared in `tools/share-manifest.toml`
> under `[[not_shipped]]`. In this share the registration steps (detailed in
> `ops/references/ticket-supervision.md`) are done BY HAND — which is what the
> source did before 2026-08-21, and what those steps already describe. Only
> the question of who writes the row changes; every field, and the reason each
> one exists, is unchanged.

**Never read completion from silence.** Quiet cannot be told from stuck,
waiting-on-permission or thinking; judge by the deliverable (`lessons.md`
L-025). `QUIET + deliverable ABSENT` is a session to go and look at.

**A tree with a peer in it shares HEAD, `.git/index` AND the working tree:**
no `checkout -b` while a peer is live; a ref move without `checkout` leaves
the index stale (next commit records DELETIONS); after any commit `git show
--stat HEAD` for what you did NOT write; verify a peer's publish by content.
Incidents, routing by coupling class, recovery: `ops/references/shared-tree-git.md`.

## §8 Token discipline (main-session hygiene)

- Batch micro-tasks: each dispatch pays a fixed prefix (harness + tool schemas,
  plus the whole user instruction layer for a `general-purpose` worker —
  sizes in `references/harness-measurements.md` "Dispatch prefix"). Don't send
  sub-minute tasks one at a time; one worker, several items, each verified
  individually. The currency §1 buys is MAIN-CONTEXT preservation, not total
  tokens: below roughly the prefix size, reading it yourself is cheaper both
  ways. Never inline a large context block into a cheap dispatch (§4 table).
- Small reference material: pass a path anyway (keeps the prompt short and the
  material updatable).
- Large tool output: check size first; read tail/summary before deciding to
  read more. Sanity-check output before treating it as content (does it look
  like an error string? suspiciously short or empty?).

## Agent 名冊路由 (Agent Roster Routing) — task shape → agentType → 強度

派工第三維度：本節管「派給哪個 agent、什麼強度」（skill 歸
`skill-trigger-dict.md`、層級歸一~四節）。模型上限與 tier 映射見
`ops/environment.md`。該表只管 subagent，不是 main-loop model 的預設。

**effort 自 2.1.292 起可 per-call**（Agent 工具的 `effort` 參數；`environment.md`
Dispatch mechanisms）：下表「強度」欄是各定義檔 frontmatter **已經釘住**的值；
per-call `effort` 依工具說明只在使用者或指令明確要求時才填，且上限仍是 `high`
（`xhigh`／`max` 屬超出上限）。`model` 仍可 per-call 覆寫。
per-call effort 實測見 tools/model-bench/results/round4-report.md §2 與 round5-report.md
§2（haiku t04 的失誤是排序，high 不會修好）；表格數字待使用者裁決後再回寫。

| 任務形狀 (task shape) | agentType | model × effort（定義檔已釘） | 能力邊界 |
|---|---|---|---|
| 搜尋/盤點/read-many-files | `Explore`（內建，唯讀） | 繼承 × 繼承 | 唯讀；**不載入 CLAUDE.md** |
| 機械性、有硬驗收閘（轉檔/翻譯/照規格腳本/盤點/錨定審查/鎖測試修復） | `cheap-worker`（2026-10-08） | haiku × **medium**（`omitClaudeMd: true`，無 MCP） | 可寫 + Bash/PowerShell；**不載 CLAUDE.md／rules**；要規則層才用 `general-purpose`（haiku × 繼承） |
| 後端/API 實作 | `backend-architect` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| 前端實作 | `frontend-developer` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| 寫測試、QA 驗證 | `testing-qa-engineer` / `api-tester` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| Bug 根因定位與修復 | `testing-bug-fixer` | sonnet × **high** | 可寫 + Bash/PowerShell |
| 照卡施工（build-ready 施工卡、契約已定、要高強度執行者） | `work-card-executor`（2026-09-04 新增，SSLD T41 首用） | sonnet × **high**（判斷型卡經使用者核可後 `model: opus` 覆寫＋`[user-approved-top-tier]`） | 可寫 + Bash/PowerShell；只動卡片 Objects；分岔即停 |
| 紅隊/審查（reviewer ≠ author） | `code-reviewer`（fresh context） | sonnet × **high** | **唯讀**（Read/Glob/Grep/Skill + dontAsk） |
| 安全審查 | `security-engineer` | sonnet × **high** | **唯讀** + WebSearch/WebFetch |
| 架構規劃（派工版） | `Plan`（內建）或 `software-architect` | sonnet × **high** | architect 可寫文件，不可執行 shell |
| 研究/多源查證 | `general-purpose` + T4 契約 | sonnet × 繼承 | 全繼承 |
| 品味/政策措辭/模糊判斷 | **不派工** — 主 session 自做（`30-judgment.md` R6） | — | — |

能力邊界是**強制的**，不是提示（`environment.md` Dispatch mechanisms）：唯讀角色
的 `tools` 白名單不含 `Edit`/`Write`，派工時不要要求它順手修好——做不到，只會浪費
一輪；實作型角色**刻意不設** `permissionMode`（`dontAsk` 會連 `Edit` 一起拒絕）。
每個定義都保留 `Skill` 工具——**移除它會靜默關閉整個 skill 機制**（`lessons.md`
L-014）。

兩個**目前未使用**的載入面（2026-09-06 對 2.1.257 調和補記）：`skills:` 前置
載入（每次派工付全額 token，要用先量成本）、sibling roster（啟動當下的快照）。
條件、限制與該不該用：`references/harness-measurements.md` §Dispatch semantics。

消歧（易混淆組）：
- `code-reviewer` agent vs `/code-review` skill vs `code-review-deep-checklist`：
  skill 是**方法論**（快速抓蟲/深度健檢），agent 是**執行載體**。主 session 收件
  紅隊時派 `code-reviewer` agent；使用者主動要求 review 時走 skill 路由
  （`skill-trigger-dict.md` 審查家族）。內建 `/code-review` 與 `/verify`
  **不能用 `skills:` 預載**，subagent 能否自行叫起未經驗證（2026-08-12）——
  派工時不要依賴它，改派 `code-review-deep-checklist` 或在交辦訊息裡直接給方法。
- `software-architect` vs `Plan`：單純要一份實作計畫 → `Plan`；要 ADR/選型
  trade-off → `software-architect`；要任務拆分與派工建議 → 那是 dispatcher
  本人的工作（`10-command-loop.md`），不外派。（`management-tech-lead` 已於
  2026-08-12 封存。）
- 其餘 agent 按 description 對號入座；本表只列高頻與易混淆者。
