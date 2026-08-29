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
3. **Report format** — the shape of the conclusion + where artifacts land.
4. **Redlines** — the explicit do-not-touch list (rule-tier files, production,
   anything the project protects).
5. **Self-sufficient materials** — copy specs/references the sandbox may not be
   able to reach into a path the worker CAN read. A worker that can't read what
   it needs tends to fabricate a plausible answer rather than report the gap.

Worked ✅/❌ pair for this contract: `ops/references/dispatch-templates.md`.

## §3 Gotchas when dispatching to an external CLI agent (verify in your env)

1. Background jobs: redirect stdin from `/dev/null`, or some CLIs hang waiting.
2. Launch from a genuine scratch dir, not an OS-protected folder — some
   sandboxes silently fail to read protected paths and fabricate instead.
3. Always wrap with an outer timeout — some agents hang silently.
4. Non-git working dirs may need an explicit "trust this directory" flag.

## §4 Model / effort assignment (two axes: model × effort)

Strength has two axes: model tier AND effort/thinking level. The current
environment's tier→model-id mapping, cost cap, and
enforcement mechanism live in `ops/environment.md`; this table stays in role
terms. **Cap rule**: everything above "mid tier + high effort" requires
explicit per-instance user approval (mechanically enforced where the
environment supports it — see `environment.md`).

| Task shape / severity | Model tier | Effort |
|---|---|---|
| Summarize / reformat / dictionary-style lookups | cheap | low |
| Translation / extraction / small to-spec scripts — anything with a hard machine-checkable gate | cheap + explicit output-format contract (a hard gate substitutes for tier quality on internal work; outward-facing "always top-tier" project rules still win) | low |
| Search / inventory / read-many-files | cheap–mid, search-oriented subagent | medium |
| Write a script/module | mid; always review the result | medium |
| Red-team / review | a different model family/tool than the author if one exists; else fresh-context mid tier. **Reviewer ≠ author, always** | high |
| Research / multi-source verification | mid, research-oriented subagent | high |
| Taste, ambiguous judgment, policy wording | main session — not delegable, see `30-judgment.md` R6 | — |

Where the dispatch mechanism supports a machine-enforced output schema (see
`environment.md`), use it instead of prompt-side format instructions — format
drift is the most common cheap-tier failure, and a schema eliminates it.
(Applies to class-A/B outputs per §2's answer-shape routing; a class-C task
takes no up-front schema on either mechanism.)

## §4a Which PATH: subagent or external tier (ask before §4's table)

Two dispatch paths exist. §4 above sizes work WITHIN the subagent path; this
picks the path. Facts, entry point and gates: `environment.md` "External
dispatch tier".

**Send it externally when ALL of these hold** — one NO sends it to a subagent:

- the target project is in `tools/extdispatch/allowlist.txt`;
- the work is not ABOUT `.claude`-class internals (see §4b);
- the deliverable is machine-checkable — a schema, an anchored finding list, a
  file that either compiles or does not. External output is accepted by
  verification, never by reading it and finding it plausible;
- latency is not the binding constraint (an external run is minutes, and free);
- **red-team / review: prefer external by default.** It is a genuinely
  different model family, which the subagent path cannot offer at all.

**Keep it in a subagent when** the work needs main-repo context, touches
anything unlisted or private, needs a tool the external worker lacks, or is
judgment/taste (which is not delegable at all — `30-judgment.md` R6).

Profile → task shape, prompt shape (format first line, evidence anchor, explicit
file scope, licensed empty answer), acceptance and failure signatures:
`ops/references/external-dispatch.md`. Chains and live health:
`extdispatch.py status` — that output beats any table.

## §4b Redlines and disclosure for external dispatch

- **Never externally**: `~/.claude` and its subtree, plus the operator's own
  share and publication trees — refused mechanically (exit 3).
- **Never as a TASK**: a project's own `.claude`-class internals. Not
  mechanical — a worker's `grep` cannot be gated by path, so the dispatcher
  owns this one. Authored in-house, verified by skills/subagents.
- **Disclose at dispatch time** (user ruling): which project is going out, to a
  free external tier, and why it is safe to send. Free-tier use needs
  disclosure, not approval.
- **Shard the card** by real sub-need and stage, so one dispatch never carries
  a whole picture of a codebase.
- **Unlisted or private project → STOP and ask**, every time.

## §5 Escalation and de-escalation

- Cheap-tier fails once → re-dispatch one tier up. Same-tier retries usually
  reproduce the same failure.
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
first line + ranked WARNING list + ≥3 specific challenges). Field lists and
the worked §2 example: `ops/references/dispatch-templates.md`. Rules of thumb:
long spec → file first, then dispatch; acceptance is written for the worker but
the dispatcher still spot-checks; on re-dispatch, put the previous failure
output in "read first".

## §7 The report contract (what a worker hands back)

- Conclusions + `file:line` refs only; large artifacts to disk, path returned.
- Delivery summary: what was done (≤5 lines) + what was verified (commands +
  key output lines) + honesty clause (what couldn't be reached, what was
  skipped, and why).
- Any numeric or factual claim carries a source; no source → label
  "unverified". Never fabricate.

## §7a Supervising a dispatched ticket (do the registration AT dispatch time)

A dispatched session cannot be identified after the fact — two id namespaces
nothing on disk joins, and transcripts contaminated by cross-session messages
so only the OPENING user turn binds cleanly (measured 2026-08-21; evidence in
`tools/session-board/README.md`).

> **Share note.** Neither half of that mechanism ships here: the registering
> hook (`hooks/session_board_register.py`) and the ticket board it writes into
> (`tools/session-board/`) are both declared in `tools/share-manifest.toml`
> under `[[not_shipped]]`. In this share the three steps below are done BY
> HAND — which is what the source did before 2026-08-21, and what the steps
> already describe. Only the question of who writes the row changes; every
> field, and the reason each one exists, is unchanged.

**Registration is mechanised — you owe exactly one field.** Steps 2 and 3 below
used to be prose here, and prose is what this repo measured failing (L-011 hit
3, L-023 hit 2). `hooks/session_board_register.py` writes the entry on
PostToolUse of `spawn_task`, taking `task_id` from the response and `title`,
`cwd` and `match` from the call — the only real dispatch surface (32
spawn_task vs 0 Workflow; `Agent` calls are subagents the board does not scan;
`tools/session-board/sweep-dispatch-surface.py` re-derives it).

1. **Open the prompt with a sentence that appears nowhere else**, and never quote
   another ticket's opening sentence in a message. The hook copies that first
   line verbatim into `match`; it is still yours to make distinctive. (It cuts
   the phrase before any character JSON escapes, and writes `match: null` rather
   than a weak one — the board then says UNBOUND, which is correct.)
2. **Fill in `deliverables` — the one field a machine cannot infer.** The hook
   writes `null`, which the board prints as `NOT DECLARED` in magenta with the
   edit to make. Replace it with the paths the ticket must produce, or with `[]`
   if it deliberately has none (e.g. "commit these paths") and put the
   verification command in `note`. `[]` and `null` are different states on
   purpose: `[]` says you decided, `null` says nobody has. Inventing a path to
   watch is still worse than watching nothing.
3. **Check the cwd if the ticket is started in a worktree.** The hook records
   the cwd passed to `spawn_task`, or the dispatching session's if none was
   passed; a worktree session's real cwd differs and the board will report
   UNBOUND until you correct it.

Nothing else is owed. If the board says `UNBOUND` for a ticket you just
dispatched, the hook did not run — check `telemetry/session-board-register.jsonl`
and `ops/references/integrity-sweep.md` check 22, do not re-add the entry by
hand and leave the cause in place.

Then supervise with `tools/session-board/session-board.ps1 -TicketFile ...`, run
twice a few minutes apart. Division of authority, because neither side can
answer the other's half:

| question | authority |
|---|---|
| is it still running? title? `local_` id? | `ccd_session_mgmt list_sessions` |
| which transcript is which ticket? quiet for how long? what did it produce? | the board |

**Never read completion from silence.** A quiet transcript cannot be told apart
from stuck, waiting-on-permission, or thinking; raising the threshold only moves
the misjudgement later. Judge by the deliverable — `ops/lessons.md` L-025 (B4),
where a monitor that trusted silence harvested an empty deliverable. `QUIET +
deliverable ABSENT` is a session to go and look at, not a finished one.

**A tree with a peer in it shares HEAD, `.git/index` AND the working tree** —
the rule lines, each measured on a real incident (2026-08-17, 2026-08-21 ×2):
- Do not `git checkout -b` while a peer session is live — moving HEAD redirects
  their next commit onto your branch. Additive, zero-behaviour-change work goes
  straight onto the current branch; anything larger waits for the baton-pass.
- A ref move (`git update-ref`, `git branch -f`) WITHOUT a following `checkout`
  leaves the shared index stale, and the next commit in ANY session silently
  records every path it does not know about as a DELETION (52 files, no error,
  `merge-base --is-ancestor` still says yes — ANCESTRY AND CONTENT ARE
  DIFFERENT QUESTIONS).
- After ANY commit in a shared tree: **`git show --stat HEAD`, read for what you
  did NOT write** — deletions are the loud case; ABSORPTION of a peer's
  uncommitted edit into your commit (content correct, provenance gone, every
  check green) is the quiet one. If you must commit a path a peer has dirty,
  carry their provenance in the message and stage nothing else of theirs.
- To verify SOMEONE ELSE'S publish, ask the content question — `git cat-file -e
  <sha>:<path>` or a tracked-file count — not `--is-ancestor`.
Routing by coupling class, the full commit ritual, attribution (by what a commit
TOUCHES, never by which session looks busy) and the recovery recipes:
`ops/references/shared-tree-git.md` (the canonical home of `lessons.md` L-023).

## §8 Token discipline (main-session hygiene)

- Batch micro-tasks: each dispatch has fixed overhead — ~49K tokens of preamble
  per `general-purpose` worker (`rule-registry.md` → subagent instruction
  surface). Don't send sub-minute tasks one at a time; one worker, several
  items, each verified individually. The currency §1 buys is MAIN-CONTEXT
  preservation, not total tokens: below roughly that size, reading it yourself
  is cheaper both ways.
- Small reference material: pass a path anyway (keeps the prompt short and the
  material updatable).
- Large tool output: check size first; read tail/summary before deciding to
  read more. Sanity-check output before treating it as content (does it look
  like an error string? suspiciously short or empty?).

## Agent 名冊路由 (Agent Roster Routing) — task shape → agentType → 強度

派工第三維度：本節管「派給哪個 agent、什麼強度」（skill 歸
`skill-trigger-dict.md`、層級歸一~四節）。模型上限與 tier 映射見
`ops/environment.md`。該表只管 subagent，不是 main-loop model 的預設。

**effort 不是 per-call**（`environment.md` Dispatch mechanisms）：下表「強度」欄
是各定義檔 frontmatter **已經釘住**的值，不是 dispatcher 可填的參數；要改就改
定義檔。`model` 仍可 per-call 覆寫。

| 任務形狀 (task shape) | agentType | model × effort（定義檔已釘） | 能力邊界 |
|---|---|---|---|
| 搜尋/盤點/read-many-files | `Explore`（內建，唯讀） | 繼承 × 繼承 | 唯讀；**不載入 CLAUDE.md** |
| 機械性、有硬驗收閘（轉檔/翻譯/照規格腳本） | `general-purpose` | haiku × 繼承 | 全繼承 |
| 後端/API 實作 | `backend-architect` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| 前端實作 | `frontend-developer` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| 寫測試、QA 驗證 | `testing-qa-engineer` / `api-tester` | sonnet × 繼承(medium) | 可寫 + Bash/PowerShell |
| Bug 根因定位與修復 | `testing-bug-fixer` | sonnet × **high** | 可寫 + Bash/PowerShell |
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
