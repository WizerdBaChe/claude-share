# Portability — capability self-assessment for non-Claude runtimes

Read this file FIRST when this skill runs anywhere other than Claude Code: another
coding agent (codex, opencode, Gemini CLI…), a web LLM with browsing (ChatGPT, Gemini,
Claude.ai web), or any future host. The methodology in SKILL.md — P1→P5 semantics,
source routing, credibility rubric, access-level tags, result contract, zero-fabrication
— is environment-neutral. Only the TOOL BINDINGS are Claude-specific. Do not fork the
skill per platform; self-assess at runtime against the capability slots below, then run
the same pipeline with substituted bindings.

## Capability slots

| Slot | Needed for | Claude Code binding | Acceptable substitutes | If absent (degradation) |
|---|---|---|---|---|
| `web_search` | P2 discovery/mixed paths | WebSearch | Tavily / Brave (metered) / DDGS (best-effort) / SearXNG / built-in browsing of a web LLM | discovery path unavailable → only source-provided and local-corpus modes remain; say so up front |
| `page_fetch` | P3 verification, P4 extraction, scholarly APIs (Crossref/OpenAlex/arXiv return JSON/XML over plain GET) | WebFetch | any HTTP GET/fetch tool; browsing tool that renders pages | items cap at `[abstract]` from search snippets; credibility checks limited — record in `gaps` |
| `extract_render` | JS-heavy/anti-bot pages (optional) | — (WebFetch limit) | Tavily extract / Exa contents / self-hosted Firecrawl (see search-sources.md provider table) | keep honest `[partial]`/`[abstract]` tags; never reconstruct |
| `local_corpus` | corpus-first routing (optional) | prism MCP | Zotero/reference-manager MCP; a local PDF folder the host can read; files the user uploads in a web LLM | skip the corpus rung; empty ≠ "literature not found" |
| `pdf_read` | `[full]` extraction from PDFs (optional) | Read tool on PDF | file upload + native PDF reading (web LLMs); OCR pipeline | extract from HTML/abstract versions; tag honestly |
| `file_write` | file deliverables (optional) | Write | canvas / downloadable file features | inline delivery — already the default; file output needs explicit request anyway |
| `subagent_dispatch` | evals only — never required for a run | Agent tool | none needed | ignore |

## Decision procedure (run once per session, before P1)

1. **Inventory** the tools actually available in this runtime; map them to the slots.
2. **Minimum viable profile**: at least ONE of — (`web_search` + `page_fetch`), a usable
   `local_corpus`, or user-supplied sources (source-provided path). If none hold,
   decline the request with the reason instead of running; a run with zero source
   access can only fabricate.
3. **Choose bindings per slot**, preferring: built-in free tools → free-tier APIs →
   metered APIs (only with user awareness) → best-effort scrapers (last, flagged).
4. **Record the profile**: state the chosen bindings and every degradation in the
   deliverable — Mode 1: in the gaps/confidence section; Mode 2: in `search_trail`
   (bindings) and `gaps` (coverage cost). A degraded run is valid; an unstated
   degradation is not.
5. **Invariants that never degrade**, regardless of profile: zero fabricated citations;
   access-level tags reflect what was actually read; locator per extracted item;
   uncertainty marked, gaps reported rather than filled.

## Claude-only constructs — ignore, do not emulate

- Frontmatter `description` trigger phrasing and `~/.claude/skill-trigger-dict.md`
  references: Claude Code routing metadata. Other hosts invoke this skill explicitly.
- Cross-skill handoffs named in SKILL.md (deep-research, scientific-research-guide…):
  if the named skill does not exist in this runtime, absorb the need into the honest
  `gaps` output or ask the user — do not silently claim the handoff happened.
- MCP tool names (`mcp__prism__*` etc.): reference implementations of a slot, not
  requirements.

## Copies and adaptation

Run from an unmodified copy whenever possible — runtime self-assessment beats forking.
If a host truly requires editing the copy (as codex did for another skill's
`/compact` flow), back up first and log the change in the copy directory's
`README-PROVENANCE.md` adaptation log so the next re-sync re-applies it. Canonical
source stays `~/.claude/skills/literature-search-extract/` on the owner's machine;
improvements flow back there, not into copies.
