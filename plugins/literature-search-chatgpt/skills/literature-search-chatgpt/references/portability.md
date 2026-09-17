# Portability — ChatGPT/Codex host binding

Read this file FIRST when this package runs. The methodology in `SKILL.md` — P1→P5
semantics, source routing, credibility rubric, access-level tags, result contract and
zero-fabrication — is host-neutral. This package binds those semantics to ChatGPT/Codex
capabilities and records an honest degradation when a capability is unavailable. A
future Claude adapter will be maintained separately so its routing and tool names do
not become implicit requirements here.

## Capability slots

| Slot | Needed for | ChatGPT/Codex binding | Acceptable substitutes | If absent (degradation) |
|---|---|---|---|---|
| `web_search` | P2 discovery/mixed paths | the host web search tool | an approved scholarly API or another user-authorized search service | discovery unavailable → source-provided and local-corpus modes only; say so up front |
| `page_fetch` | P3 verification, P4 extraction, scholarly APIs | the host page open/fetch tool | direct HTTP GET or a browser surface that can read the page | cap items at `[abstract]` from search results; record the coverage loss in `gaps` |
| `extract_render` | JS-heavy pages, PDFs and pages the fetch tool cannot read | host browser/PDF reading or an attached source file | an approved document extraction service | keep honest `[partial]`/`[abstract]` tags; never reconstruct missing text |
| `local_tool` | an optional connector holding primary documents | a user-run local process or connector exposed to the host | any CLI/loopback service that keeps its credential outside the skill | drop that source class and record the cost |
| `local_corpus` | corpus-first routing | user-provided files, a reference-manager connector or a local PDF folder | any readable curated corpus | skip the corpus rung; empty ≠ “literature not found” |
| `pdf_read` | `[full]` extraction from PDFs | native PDF reading or an attached PDF | OCR/document extraction with a visible source | extract from readable HTML/abstract versions; tag honestly |
| `file_write` | explicit file deliverables | host workspace/file writing | downloadable artifact or inline delivery | inline delivery remains the default |
| `run_store` | persisting the evidence run | `loop/runs.py` with its per-user default or `LSE_RUN_HOME` | any writable folder; a host with no file store keeps the ledger in the reply | say `run not filed: home unavailable` in `search_trail` and `gaps` |
| `subagent_dispatch` | optional evaluation work only | none required by a normal run | a host subagent when explicitly available | ignore |

## Decision procedure (run once per session, before P1)

1. **Inventory** the tools actually available in this runtime and map them to the slots.
2. **Minimum viable profile**: at least one of (`web_search` + `page_fetch`), a usable
   `local_corpus`, or user-supplied sources. If none hold, explain why the request cannot
   be completed without inventing evidence.
3. **Choose bindings per slot**, preferring built-in tools, then user-authorized APIs,
   then best-effort services with their limits recorded.
4. **Record the profile** in the deliverable: Mode 1 uses `gaps`/`confidence`; Mode 2
   uses `search_trail` and `gaps`.
5. **Invariants never degrade**: zero fabricated citations, access tags reflect what was
   actually read, every extracted item has a locator, uncertainty is marked, gaps are
   reported rather than filled, and every load-bearing claim names its support span.

## Host-specific constructs

- The frontmatter description is metadata for explicit ChatGPT/Codex skill invocation;
  no external trigger dictionary is required.
- A cross-skill handoff is valid only when the named skill exists in the current host.
  Otherwise absorb the need into the result contract and state the gap.
- Tool labels in the reference files are capability names. Map them to the current
  host's web search, page fetch, browser, PDF and file tools; never assume a particular
  vendor-specific MCP name.
- `LSE_HOST_POLICY` may point `connectors/access_policy.py` at a policy JSON. If it is
  absent, the policy reader fails closed for browser surfaces and allows only its public
  scholarly API list.

## Adaptation record

This directory is the ChatGPT/Codex package adapter. Its host-facing edits are kept in
the package README and `SHARE-NOTES.md`; the source share skill remains separately
maintained under `skill-toolkit/skills/literature-search-extract`. When another host is
packaged, create a sibling plugin with its own manifest and adapter files rather than
mixing host bindings into this directory.
