# Domain Routing Manifest

> Single source of truth for **which domain files exist** and **when to load each**.
> Gate A Step 0 (SKILL.md) consults this file before loading any Layer-B content.
> Keep it terse — this file is read on every domain-triage turn. One row per file.

## How Gate A uses this manifest

1. **Identify domain** — match the user's field against the `base` rows' triggers.
2. **Load the base profile** — always load the matched domain's base profile alongside
   the tier framework. Its Node 6 (pitfalls) + Node 8 (decision triggers) become standing
   if-then rules for the whole turn.
3. **Scan sub-profiles of that domain** — for every `sub-profile` row whose parent is the
   matched domain, check its load trigger against the user's wording. On a match, **load it
   and activate its own Node 6/8 triggers** (they fire like the base profile's).
4. **Pull references on demand only** — `reference` / `boundary` rows are loaded only when
   the specific topic is explicitly engaged; they carry no standing triggers. A `boundary`
   row's job is to route the user *out* to a sibling domain when they cross the edge.

Type semantics are defined in `domain-expansion-guide.md` §2 (the two-gate decision tree).

## Manifest

**This share ships the manifest FORMAT with no rows.** The source environment's
filled manifest listed its author's own research fields; those domain profiles are
subject-matter knowledge and were excluded from this share (see `README.md` in this
folder). Author your own rows — one per file you actually create.

| Type | File | Parent | Load trigger (keywords) | Covers / role | Active triggers? |
|---|---|---|---|---|---|
| base | `<domain>.md` | — | 5–10 field-identifying keywords a user would actually type | The domain's 7-node base profile | yes (Node 6+8) |
| sub-profile | `<domain>/<phenomenon_or_method>.md` | `<domain>` | keywords naming that specific phenomenon, method, or material | Specialized branch whose pitfalls fire as standing rules | yes (Node 6+8) |
| reference | `<domain>/<terminology>.md` | `<domain>` | terms, symbols, abbreviations the field overloads | Look-up material, pulled only when the topic is explicitly engaged | no |
| boundary | `<domain>/<adjacent_field>.md` | `<domain>` | keywords belonging to the NEIGHBOURING field | Routes the user OUT to a sibling domain and corrects false equivalences | no |

Delete the four template rows above once you have real ones. Row-type semantics —
and when a topic deserves a `sub-profile` versus a line inside the base profile —
are decided by the two-gate tree in `domain-expansion-guide.md` §2.

**Only list files that ACTUALLY EXIST.** Gate A will try to load whatever it finds
here; a row pointing at a missing file is a load failure, not a no-op.

## Maintenance

- SKILL.md must NOT hardcode domain file paths — it points here. When you add a domain
  file, add its row here in the same change; that is the only place the load list lives.
- `base` files stay lean (the 7-node profile = the domain's shared core). Specialized
  branches go in `sub-profile` rows, not the base file — see the decision tree.
