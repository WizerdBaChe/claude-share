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
   machine-check after. Measured 2026-08-16 (2×2 arms, same task, same
   model): a schema-first contract suppressed the INVESTIGATION itself — 1
   tool call vs 8/18, no companion files read, zero empirical probes — not
   merely the output's shape; free-first cost ~1.6× tokens / ~2× wall-clock,
   which is the price of the investigation, not overhead. Orthogonal to the
   class: each acceptance layer stacked on one output still rules only on
   what IT can determine (global gate rule; `lessons.md` L-019). State the goal, not the proof ritual — "prove your
   own work passes" invites an expensive self-verification loop. The worker
   self-checks FORMAT compliance only; ACCEPTANCE verification belongs to
   the dispatcher with fresh context (`10-command-loop.md` Step 6).
3. **Report format** — the shape of the conclusion + where artifacts land.
4. **Redlines** — the explicit do-not-touch list (rule-tier files, production,
   anything the project protects).
5. **Self-sufficient materials** — copy specs/references the sandbox may not be
   able to reach into a path the worker CAN read. A worker that can't read what
   it needs tends to fabricate a plausible answer rather than report the gap.

✅ "Goal: unify date formats (downstream parser needs ISO-8601 — that's why).
Acceptance: `python check_dates.py out/` prints OK. Output: JSON per schema in
schema.json. Redlines: don't touch archive/. Read first: spec.md (copied to
your scratch dir)."
❌ "Clean up the dates in these files, you know what I mean" — no acceptance,
no format, no redlines; whatever comes back is unreviewable.

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

**T1 Search/inventory** (read-only): task / motivation / scope (explicit globs)
/ match criteria + one worked example / output path + format (count →
categorized list, each `file:line` + ≤80-char excerpt) / redline: write only
the report file / reply: count + top 3 findings.

**T2 Implementation**: task + spec-file path (spec as file, not pasted) / read
first: self-sufficient materials / to-do (one verifiable action per line) /
design constraints stated as fixed / acceptance commands / redlines / reply:
≤5-line summary + acceptance output + known limitations.

**T3 Refactor/batch edit**: old→new pattern + scope / motivation /
**do-not-touch list (more important than the change list)** / per-file verify
command / batch cap of N files with a count per batch / ambiguous cases →
"needs a human" list, never guessed / output: change list + skipped list +
verify output.

**T4 Research** (read-only + one report): question / background + what decision
it feeds / starting sources (worker may add a few, each with URL + one-line
justification) / live search required, no training-data recall; every claim
cited / output structure: conclusion first → comparison table → verdicts
(adopt / don't / needs-human, each with evidence; mark uncertainty, never
fabricate) / reply: one-line method + top 3 conclusions.

**T5 Review/red-team** (read-only, never the author): target / context (runs
unattended? touches user data?) / cross-reference paths / focus areas ranked
by risk / verdict: PASS/FAIL first line + WARNING list (HIGH/MED/LOW, each
with `file:line` + failure scenario) / adversarial stance: raise at least 3
specific challenges.

Template rules of thumb: long spec → file first, then dispatch; acceptance is
written for the worker but the dispatcher still spot-checks (never a
substitute); on re-dispatch, put the previous failure output in "read first".

## §7 The report contract (what a worker hands back)

- Conclusions + `file:line` refs only; large artifacts to disk, path returned.
- Delivery summary: what was done (≤5 lines) + what was verified (commands +
  key output lines) + honesty clause (what couldn't be reached, what was
  skipped, and why).
- Any numeric or factual claim carries a source; no source → label
  "unverified". Never fabricate.

## §8 Token discipline (main-session hygiene)

- Batch micro-tasks: each dispatch has fixed overhead — **measured 2026-08-14 at
  ~49K tokens of preamble for one `general-purpose` worker with zero tool uses**
  (`rule-registry.md` → subagent instruction surface). Don't send sub-minute
  tasks one at a time; one worker, several items, each verified individually.
  The currency §1 actually buys is MAIN-CONTEXT preservation, not total tokens:
  below roughly that size, reading it yourself is cheaper both ways.
- Small reference material: pass a path anyway (keeps the prompt short and the
  material updatable).
- Large tool output: check size first; read tail/summary before deciding to
  read more. Sanity-check output before treating it as content (does it look
  like an error string? suspiciously short or empty?).

## Agent 名冊路由 (Agent Roster Routing) — task shape → agentType → 強度

派工第三維度：本節管「派給哪個 agent、什麼強度」（skill 歸
`skill-trigger-dict.md`、層級歸一~四節）。模型上限與 tier 映射見
`ops/environment.md`。該表只管 subagent，不是 main-loop model 的預設。

**effort 不是 per-call**（查證 2026-08-12，見 `environment.md`）：自訂 agent 的
強度寫死在該檔 frontmatter 的 `effort:`，派工當下改不了。下表「強度」欄記錄的是
各定義**已經釘住**的值，不是給 dispatcher 填的參數；要改就改定義檔。
`model` 仍可 per-call 覆寫。

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

能力邊界是**強制的**，不是提示：唯讀角色的 `tools` 白名單不含 `Edit`/`Write`，
且 `permissionMode: dontAsk` 會自動拒絕 allowlist 以外的動作。派工時不要要求
唯讀 agent 順手修好——它做不到，只會浪費一輪。反之，實作型角色**刻意不設**
`permissionMode`，因為 `dontAsk` 會連 `Edit` 一起拒絕（allowlist 沒有它）。

skill 觸發：每個定義都保留 `Skill` 工具，body 只指示「查執行期 roster」而不寫死
skill 名稱，所以新增 skill 自動生效、不需回頭改定義。**移除 `Skill` 會靜默關閉
整個 skill 機制**（`lessons.md` L-014）。

消歧（易混淆組）：
- `code-reviewer` agent vs `/code-review` skill vs `code-review-deep-checklist`：
  skill 是**方法論**（快速抓蟲/深度健檢），agent 是**執行載體**。主 session 收件
  紅隊時派 `code-reviewer` agent；使用者主動要求 review 時走 skill 路由
  （`skill-trigger-dict.md` 審查家族）。內建 `/code-review` 與 `/verify`
  **不能用 `skills:` 預載**（官方明載，理由是預載只取自模型可調用的集合）。
  但實測 2026-08-12：subagent 的 roster **仍然列出**它們，所以「subagent 能不能
  實際叫起來」未經驗證 —— 派工時不要依賴它，改派 `code-review-deep-checklist`
  或在交辦訊息裡直接給方法。
- `software-architect` vs `Plan`：單純要一份實作計畫 → `Plan`；要 ADR/選型
  trade-off → `software-architect`；要任務拆分與派工建議 → 那是 dispatcher
  本人的工作（`10-command-loop.md`），不外派。
  （`management-tech-lead` 已於 2026-08-12 封存：三個分支全部路由離開它，
  留著只是名冊噪音。）
- 其餘 agent 按 description 對號入座；本表只列高頻與易混淆者。
