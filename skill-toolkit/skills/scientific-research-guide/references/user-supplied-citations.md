# User-Supplied Citation Inventory

> Status: TEMPLATE — the source environment's filled inventory was subject-matter
> knowledge (its author's own research tracks) and is not part of this share. The
> storage rules, table shapes, and delegation contract below are the transferable
> part; fill them with your own sources.
> Scope: URLs a user supplies alongside a domain packet.
> Evidence rule: A URL stored in the inbox is provenance, not evidence. Promote it into a domain profile only after identity, access level, locator, relevance, and claim scope are checked.

## Storage and triage rules

1. Preserve the user-provided URL verbatim in the source inbox. Do not silently replace a repository copy, thesis mirror, publisher page, or preprint with another URL.
2. Resolve a canonical identifier when available: DOI first, then PMID, arXiv ID, patent number, ISBN, or repository identifier. For a versioned source (a standard's issue, an arXiv vN, a vendor datasheet's rev), the identifier includes the exact issue/version consulted — a bare designation cannot support a later "has it been revised?" check (guide §3.7).
3. Record access honestly: [full] means the full text was read; [partial] means only selected sections, a preview, or supplementary material was read; [abstract] means abstract or metadata only; [secondary] means the item was learned through another source; [untriaged] means identity or relevance is not yet checked. **An access tag is a dated observation, not a permanent property** — paywalls open, pages die, vendor pages get silently edited. Every tag assignment or change must have its date recoverable from the same row (the promotion table's Checked (date) column; for inbox-only entries, the batch's intake date).
4. Keep alternate versions under one citation identity when the identity is verified, but retain every user-provided access URL in the inbox.
5. Promote only the smallest useful set into a domain profile's Literature Anchors. A promoted entry must include why it matters and must not be used beyond the conditions actually read.
6. Treat Wikipedia, lectures, seminars, vendor pages, blogs, videos, search aggregators, patents, and theses as discovery or engineering-context sources unless the claim explicitly requires that source type. They are not substitutes for a peer-reviewed primary paper.
7. Keep unresolved or context-dependent terms in the inbox as [untriaged]; do not expand an acronym or infer a mechanism from the URL alone.
8. When a later search updates an entry, append a note with the date, access level, identifier, locator, and disposition. Do not erase the original provenance.
9. Every promotion-table row carries a **Checked (date)**: the date its identity/access/relevance was last actually checked against the source (not merely re-typed from an earlier version of this file). Where a row's disposition waits on a specific nameable future event — a paywalled or blocked page becoming accessible, a standard's next issue — note it inline as `review-when: <event>`; never a vague "re-check periodically" (same discipline as guide §3.7: a control that names no event rots silently while still being trusted).
10. New URLs enter the inbox under a **dated batch note** naming the supplying packet. Without a batch date, an [untriaged] entry's age — and therefore its link-rot risk — is unknowable.

## Identity-checked promotion candidates

Only entries checked against the supplied URL, DOI/title metadata, or an accessible
journal page belong here. The access tag limits what may be asserted from the entry.

| Track | Canonical identity | User URL or access family | Access | Checked (date) | Intended use | Disposition |
|---|---|---|---|---|---|---|
| `<domain>` | `<DOI / arXiv / PMID / patent no.>` | `<the URL the user actually supplied>` | `[full]` / `[partial]` / `[abstract]` / `[secondary]` / `[untriaged]` | `<YYYY-MM-DD>` | `<the one claim this is allowed to support>` | `<promoted to X.md Node 7 / held / superseded>` |

## Canonical duplicate groups

Group alternate URLs under ONE identity only where the identifier supports it — a
publisher page, a repository mirror, a preprint, and a thesis chapter are the same
citation only if verified so.

| Identity | Alternate user URLs |
|---|---|
| `<canonical DOI>` | `<url A>; <url B>; <url C>` |

## User-provided source inbox: `<track name>`

One section per track, opened with a dated batch note naming the supplying packet
(rule 10). All entries are preserved as source-provided provenance; unless promoted
above, treat them as `[untriaged]`. Never rewrite a user's URL into a "better" one —
record the alternate separately.

- `<verbatim user-supplied URL>`

## Maintenance

- Keep this file as the source-provenance layer. Do not use it as a substitute for the domain profiles' 3–5 Literature Anchors.
- When promoting an entry, add its identifier, access tag, Checked (date), locator, relevance, and limitations to the promotion table. When it is promoted onward into a profile's §7b, the Checked (date) here becomes the starting `Verified (date)` there only if the promotion pass actually re-read the source; otherwise the ledger row gets the promotion pass's own date and status.
- When a URL is dead, retain the URL and append a **dated** status note; do not delete user provenance. An undated "dead" note cannot distinguish a transient outage from years of link rot.
- When a paper has a publisher page, repository mirror, preprint, and thesis version, verify that the versions share the same identity before grouping them — and record *which version* the access tag describes (an arXiv v1 read is not evidence about the published version's final numbers; triage rule 2).

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
- **Traceability**: when an update was produced by a literature-search-extract run, set
  the row's **Checked (date)** to the run's date (identity merges: note the date in the
  Canonical-duplicate-groups note) so a future maintainer can see which entries were
  contract-verified versus carried over from an earlier integration pass. The Disposition
  cell keeps the qualitative outcome; the date lives in its own column (triage rule 9).
  Record the contract used, not just the result.
- **Batch integration passes** (adding a whole new domain's citation set at once) should still run through the same contract per
  track, and should leave a dated audit-trail report in `reports/`, not only a diff to
  this file.
- This delegation rule does not apply to purely mechanical edits (fixing a typo, marking
  a URL dead without re-resolving it, reformatting a table) — those may be done directly.
