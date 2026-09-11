# Record Templates — full templates extracted from `60-bootstrap.md` (trim pass 2026-08-06)

Normative status: these are the invariant-class schemas registered in
`ops/rules-usage-dict.md` §7 — no relaxation level omits their fields.
When-to-use rules and boundaries stay in `60-bootstrap.md` §F/§G; read THIS
file at write time, verbatim.

## §1 Work card (施工卡) — owner: `60-bootstrap.md` §F

```markdown
### <PREFIX>-NN — <one-line end state>
- Severity/Confidence: <blocker|should-fix|consider|nit> / <level + how verified>
- Objects: <files touched, incl. new files and doc/ADR amendments>
- Why: <root cause or violated rule, one line>
- Change: <the fix, concrete enough for a FRESH context to execute unaided>
- Blast radius: <behaviors affected + what must NOT change>
- Rollback: <how to revert; constraints that survive the revert>
- Acceptance: <machine-checkable check(s) first, then manual-compare items>
- Commit: <conventional message per global CLAUDE.md git rule>
```

Field ownership (reference, never redefine — one rule, one file):
- Language: global CLAUDE.md **File output** rule. A work card is the
  build-spec class — English card body (Objects/Change/Blast radius/
  Rollback/machine-checkable Acceptance); Traditional Chinese only for
  the surfaces the user rules on (manual-compare acceptance items,
  decision rationale). Do not let "it's a `.md` under `docs/`" default
  it to Chinese.
- Severity scale: `code-review-deep-checklist` output contract.
- Commit format: global CLAUDE.md git rule. (`~/.claude/COMMIT-TEMPLATES.md`
  is this config repo's own semantics — never apply it to target projects.)
- Objects/Rollback/Acceptance render the sole-source build-ready bar
  (`product-design-thinking` → `skills/product-design-thinking/references/document-ladder.md` §4, the
  normative minimum for sole-basis docs); Severity/Confidence, Blast radius,
  and Commit are card additions — a bar-compliant item missing only
  card-level fields is NOT a skeleton.

## §2 Decision & Process Journal — owner: `60-bootstrap.md` §G

```markdown
# <project> — Decision & Process Journal

## Now (updated <YYYY-MM-DD>)
frontier: <one line — where the project actually is>
premises: <irreducible premises, each tagged (user)/(model) + P-env/P-intent/P-validity>
open: <D/P ids still unresolved>

## D-NNN <YYYY-MM-DD> <one-line decision>
status: decided | superseded-by D-XXX | reopened
context: <what forced this decision, one line>
options: <A / B — one line each, and WHY the losers lost>
choice+why: <the reasoning that tipped it — the thinking, not just the verdict>
revisit-if: <condition that would reopen this>
links: <T-NNN / L-NNN / ADR / commit / phase>

## P-NNN <YYYY-MM-DD> <one-line problem>
status: open | worked-around | solved | promoted→L-NNN
trail: <what was tried, dead ends included — the process record>
resolution: <what worked, or the current workaround + its cost>
links: <...>
```

## §3 Handoff（交接單）— owner: this section (registered 2026-09-02)

When: a heavy round is split across sessions by the user's own rhythm —
evaluate/design in one session, build in a FRESH one — or a remote/peer
session hands work back to the local machine. The handoff is the sole
entry the next session reads first; a phase-log checkpoint records where the
project is, the handoff says what to DO in the next hour. Precedents: one
written remote → local, another evaluate → build, both real instances in the
source environment's own private records (its asset library and its
`references/` tree — neither ships here). Language: English spec body
(commands, cards, DoD); Traditional Chinese for the sections the user rules on.

```markdown
---  (xi card: what / tags [handoff, <project>] / aliases incl. 交接單 / date / status)
# HANDOFF — <round name>
**一句話**: <state + what is blocked on the user, one sentence>
## 0. Pick up in 30 seconds
<shell block: cd, git log/status expectations, freshness commands, the one probe that proves the environment is as described>
Reading order: <file → file → file; the newest evidence first, standing rulings after, this file last>
Environment facts (verified <date>): <versions, paths, relaxation level, model cap>
## 1. State of the world this round inherits   <table: item | state>
## 2. Rulings to obtain FIRST（使用者裁決；建議值已附）   <table: id | 問題 | 建議 | 阻擋> — prefixed ids
## 3. Boundary contract seed   <the 5 sections, ≤18 lines; tier recommendation>
## 4. Prior art already consulted (do not redo; extend)
## 5. Work cards   <§1 format, English body; SKELETON labelled where the bar is not met>
## 6. Definition of done for the round   <numbered; includes the registration set and the close-out ritual>
## 7. What this session could not do / deliberately left
## 8. Risks the builder must carry
```

Minimum fields (registry row in `rules-usage-dict.md` §7): 一句話 / pick-up
commands / reading order / rulings-first table / DoD / could-not-do. A handoff
without the rulings table exports the decision cost to the next session; one
without could-not-do reads as complete and gets built on.

## §4 Self-declaration（自我宣告塊）— owner: this section (registered 2026-09-10)

Extracted 2026-09-10 from a real per-project implementation (SSLD's own
record-registry script, inside that project's own tree — not shipped here),
where every human-facing product of the project opens with a machine-assembled
block and nobody hand-types one. It is the ARTIFACT-level companion of the claim-level
refutability statement (`30-judgment.md` R2): refutability says how the
conclusion could be wrong, this says what the artifact is made of and how far it
got. Both, never one restated as the other — R2's four fields are referenced
here, not copied.

**Trigger** (deliberately narrow — this must not grow a block on every task): a
DURABLE artifact a human will act on without re-deriving it — a report, a deck,
an audience page, a design document, a case dossier, an evaluation. NOT for a
chat answer, NOT for machine-read records that already carry their own meta
(phase logs, verify JSON, ledgers), NOT for a code change. One artifact, one
block, at the top.

```
## 這份文件是什麼做出來的
- 成熟度: <ruler A: value (origin)> · <ruler B: value (origin)>   ← two rulers side
  by side, each naming who assigned it; an unassigned ruler is "未定", never a guess
- 保真度: <instrument → level> for every instrument whose output is quoted here
- 算過的: <what was actually computed or measured>
- 只畫過的: <what exists only as a drawing, sketch, mock or illustration>
- 沒做的: <what a reader could reasonably assume was done and was not>
- 最弱的一環: <ONE sentence, plain language, naming the weakest credibility factor —
  not the longest list of caveats, the single thing most likely to be wrong>
- 來源: <path + sha256 prefix of every fact source the numbers came from>
- 界線: → the refutability statement (holds-when / overturned-by / evidence tier /
  not-covered); do not restate it here
```

Two rules the block itself must satisfy:

- **A PASS count is not a credibility signal.** "64 controls PASS" says the
  instrument ran, not that the claim is true; SSLD enforces this as INV-17 by
  scanning the assembled block and refusing when a bare `<n> PASS` appears. The
  same sentence belongs in the reader's text (`skills/audience-fit`, gate
  `afgate.py voice`).
- **算過／只畫過／沒做 is the load-bearing line.** It is the field the evidence
  tier does not carry: a figure can be rendered, audited and still show a
  quantity nobody computed (`rules/figure-self-read.md`; global CLAUDE.md —
  green tests prove the data path, not the picture). A block whose three lines
  are all "算過的" is either a fully computed artifact or an unread template.
