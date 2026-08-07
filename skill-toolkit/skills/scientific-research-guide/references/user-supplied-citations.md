# User-Supplied Citation Inventory

> Status: TEMPLATE — the source environment's filled inventory was subject-matter
> knowledge (its author's own research tracks) and is not part of this share. The
> storage rules, table shapes, and delegation contract below are the transferable
> part; fill them with your own sources.
> Scope: URLs a user supplies alongside a domain packet.
> Evidence rule: A URL stored in the inbox is provenance, not evidence. Promote it into a domain profile only after identity, access level, locator, relevance, and claim scope are checked.

## Storage and triage rules

1. Preserve the user-provided URL verbatim in the source inbox. Do not silently replace a repository copy, thesis mirror, publisher page, or preprint with another URL.
2. Resolve a canonical identifier when available: DOI first, then PMID, arXiv ID, patent number, ISBN, or repository identifier.
3. Record access honestly: [full] means the full text was read; [partial] means only selected sections, a preview, or supplementary material was read; [abstract] means abstract or metadata only; [secondary] means the item was learned through another source; [untriaged] means identity or relevance is not yet checked.
4. Keep alternate versions under one citation identity when the identity is verified, but retain every user-provided access URL in the inbox.
5. Promote only the smallest useful set into a domain profile's Literature Anchors. A promoted entry must include why it matters and must not be used beyond the conditions actually read.
6. Treat Wikipedia, lectures, seminars, vendor pages, blogs, videos, search aggregators, patents, and theses as discovery or engineering-context sources unless the claim explicitly requires that source type. They are not substitutes for a peer-reviewed primary paper.
7. Keep unresolved or context-dependent terms in the inbox as [untriaged]; do not expand an acronym or infer a mechanism from the URL alone.
8. When a later search updates an entry, append a note with the date, access level, identifier, locator, and disposition. Do not erase the original provenance.

## Identity-checked promotion candidates

Only entries checked against the supplied URL, DOI/title metadata, or an accessible
journal page belong here. The access tag limits what may be asserted from the entry.

| Track | Canonical identity | User URL or access family | Access | Intended use | Disposition |
|---|---|---|---|---|---|
| `<domain>` | `<DOI / arXiv / PMID / patent no.>` | `<the URL the user actually supplied>` | `[full]` / `[partial]` / `[abstract]` / `[secondary]` / `[untriaged]` | `<the one claim this is allowed to support>` | `<promoted to X.md Node 7 / held / superseded, + date>` |

## Canonical duplicate groups

Group alternate URLs under ONE identity only where the identifier supports it — a
publisher page, a repository mirror, a preprint, and a thesis chapter are the same
citation only if verified so.

| Identity | Alternate user URLs |
|---|---|
| `<canonical DOI>` | `<url A>; <url B>; <url C>` |

## User-provided source inbox: `<track name>`

One section per track. All entries are preserved as source-provided provenance;
unless promoted above, treat them as `[untriaged]`. Never rewrite a user's URL into
a "better" one — record the alternate separately.

- `<verbatim user-supplied URL>`

## Maintenance

- Keep this file as the source-provenance layer. Do not use it as a substitute for the domain profiles' 3–5 Literature Anchors.
- When promoting an entry, add its identifier, access tag, locator, relevance, and limitations to the promotion table.
- When a URL is dead, retain the URL and append a status note; do not delete user provenance.
- When a paper has a publisher page, repository mirror, preprint, and thesis version, verify that the versions share the same identity before grouping them.

### Delegation rule: updating this file through literature-search-extract

This file's own tables must not be hand-updated by an untraceable ad hoc search. Any
substantive change to it — promoting an `[untriaged]` entry, raising an access tag
(e.g. `[abstract]` → `[full]`), resolving a dead link, or adding a new identity-checked
row — is Tier 1 literature work and follows the same rule as any other Tier 1 task
(SKILL.md Gate B): delegate the actual search/read to the `literature-search-extract`
skill (Mode 2), do not do it inline from memory or a single unlogged fetch.

- **Request contract**: `purpose` = identity/access-tier verification or gap-fill for this
  inbox; `question` = the specific claim or track this entry should support (e.g. "does
  this URL resolve to a peer-reviewed source that supports claim C in <domain>.md?"); `source_types` = per this file's §Storage-and-triage-rules
  item 6 (peer-reviewed primary/review preferred, engineering/vendor/preprint flagged as
  such); `scope` = the single track being updated;
  `output_format` = canonical identifier + access tag + one-line relevance + limitations,
  matching this file's promotion-table columns; `depth` = targeted (one entry or one
  small batch), not a broad sweep.
- **Result contract**: consume `findings`/`sources`/`gaps`/`confidence`/`search_trail` and
  write them straight into the promotion table or the identity-checked row; do not
  paraphrase away the access tag or the stated limitations.
- **Traceability**: when an update was produced by a literature-search-extract run, note
  the date inline in the row's Disposition cell (or in the Canonical-duplicate-groups
  note for identity merges) so a future maintainer can see which entries were
  contract-verified versus carried over from an earlier integration pass. Record the contract used, not just the result.
- **Batch integration passes** (adding a whole new domain's citation set at once) should still run through the same contract per
  track, and should leave a dated audit-trail report in `reports/`, not only a diff to
  this file.
- This delegation rule does not apply to purely mechanical edits (fixing a typo, marking
  a URL dead without re-resolving it, reformatting a table) — those may be done directly.
