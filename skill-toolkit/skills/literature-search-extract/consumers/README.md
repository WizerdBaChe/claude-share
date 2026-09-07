# consumers/ — the consumer registry of the evidence feedback loop

`registry.json` is the ONE place that says who participates in the loop and how
(design of record: `~/.claude/references/lse-feedback-loop-design.md` §3.8; schema:
`../loop/schemas/consumer.schema.json`). A participant — a skill that calls this
skill, a skill this skill hands off to, a store the loop joins against, or a tool
that only writes back — is a ROW. Adding one changes no code path (INV-7):
`reflux.py` validates events by schema, `runs.py affected` scans events by `actor`,
and `runs.py bridge` renders every row into `../references/bridge.md`.

## How to add a consumer (the whole procedure)

1. Add a row (copy the closest existing one). `status: planned` until the first real
   call; `direction` says how it participates; `situations[]` are the lines a reader
   needs to call it correctly — they ARE the bridge text.
2. `python ../loop/runs.py bridge` — regenerates `../references/bridge.md` with a
   `generated-from` sha. Never hand-edit the bridge.
3. `python ../loop/runs.py check --registry` — 0 FAIL (schema, status transitions,
   bridge freshness).
4. Nothing else. If a step 4 seems necessary, the loop has grown a per-consumer code
   path and that is the defect to fix, not to document.

## Fields worth knowing

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
