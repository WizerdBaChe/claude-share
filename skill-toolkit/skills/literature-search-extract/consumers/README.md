# consumers/ — evidence loop consumer registry｜證據回饋迴路 consumer 登錄表

> **中文摘要｜Chinese summary**：`registry.json` 是 evidence feedback loop 的
> 單一決策來源，記錄哪些 skill、store 或 write-back tool 參與迴路，以及它們如何
> 參與。新增 consumer 只新增一列，不新增 per-consumer code path；schema、
> affected scan 與 bridge renderer 會讀同一列。
>
> **English summary**: `registry.json` is the single registry for participants in the
> evidence feedback loop. A consumer is a row, not a custom code path; schema
> validation, affected-run scans, and bridge generation all consume that row.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 來源 | design record §3.8 與 `consumer.schema.json` 是 governing references | Design record §3.8 and `consumer.schema.json` are the governing references |
| 參與者 | 呼叫本 skill 的 skill、被 handoff 的 skill、迴路 join 的 store、只寫回事件的 tool | A calling skill, handoff target, joined store, or write-back-only tool |
| 入口 | 編輯 `registry.json`，再跑 bridge 與 registry check | Edit `registry.json`, then run the bridge and registry checks |
| 不做 | 不為單一 consumer 增加程式分支，也不手改 generated bridge | Do not add per-consumer branches or hand-edit the generated bridge |

`registry.json` is the ONE place that says who participates in the loop and how
(design of record: `~/.claude/references/lse-feedback-loop-design.md` §3.8; schema:
`../loop/schemas/consumer.schema.json`). A participant — a skill that calls this
skill, a skill this skill hands off to, a store the loop joins against, or a tool
that only writes back — is a ROW. Adding one changes no code path (INV-7):
`reflux.py` validates events by schema, `runs.py affected` scans events by `actor`,
and `runs.py bridge` renders every row into `../references/bridge.md`.

## 新增 consumer｜Add a consumer (the whole procedure)

1. Add a row (copy the closest existing one). `status: planned` until the first real
   call; `direction` says how it participates; `situations[]` are the lines a reader
   needs to call it correctly — they ARE the bridge text.
2. `python ../loop/runs.py bridge` — regenerates `../references/bridge.md` with a
   `generated-from` sha. Never hand-edit the bridge.
3. `python ../loop/runs.py check --registry` — 0 FAIL (schema, status transitions,
   bridge freshness).
4. Nothing else. If a step 4 seems necessary, the loop has grown a per-consumer code
   path and that is the defect to fix, not to document.

## 欄位速查｜Fields worth knowing

- `status` lifecycle: `planned → live → retired`; `retired → live` needs a new
  `registered` date and a `history[]` note; `planned → retired` is allowed. Any other
  transition fails `check --registry` (R3). `direction: store|indirect` rows are `live`
  by definition.
- `calls.presets`: pre-filled request contracts — how D2's "is this the standard
  term?" is served without an eighth output format (`term_check`).
- `store.identity_field`: where the identity key is DERIVED from at read time
  (`idkey.find_all` / `idkey.normalize`); no consumer store is migrated.
- `store.run_pointer`: where the consumer records `run:<run_id>` so a later
  `runs.py affected <key>` can name the artifact.
- `writes_back`: which event kinds this participant may append through
  `../loop/reflux.py` (`consumed` / `correction` / `retraction` / `handoff` / `rerun`).

Rows are edited by a person with the user's approval — the registry is a human
decision record, like `../connectors/registry.json`.
