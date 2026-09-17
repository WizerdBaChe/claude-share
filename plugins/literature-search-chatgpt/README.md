# Literature Search — ChatGPT/Codex plugin

**Distribution target: ChatGPT and Codex (OpenAI Agent Plugins format).**

This package bundles the `literature-search-extract` skill for evidence-traceable
scholarly search and targeted extraction. It enforces source identity checks,
access-level tags, locators for extracted claims, explicit gaps, and a zero-
fabrication boundary.

The package is intentionally labelled `chatgpt` in its directory and plugin
name. A future Claude package must use its own manifest, install instructions,
and adapter boundary; it should not be inferred from or merged into this
ChatGPT/Codex manifest.

## Install from the public Git repository

After this repository revision is available on GitHub, add its Git-backed
marketplace to Codex:

```powershell
codex plugin marketplace add WizerdBaChe/claude-share --ref main
codex plugin add literature-search-chatgpt@claude-share
```

The portable root manifest is the ChatGPT/Codex format. Codex installs it from
the Git-backed marketplace above; ChatGPT availability depends on the plugin
discovery surface enabled for the account and app version. To pin a release
later, replace `main` with a tag or commit selector supported by the local
Codex version.

For a sparse checkout, the marketplace and plugin trees are sufficient:

```powershell
codex plugin marketplace add WizerdBaChe/claude-share --ref main `
  --sparse .agents/plugins --sparse plugins
```

## Runtime boundary

The skill works with the host's available web search, page fetch, local-file,
and file-output capabilities. It records any missing capability as a gap. The
bundled `connectors/access_policy.py`, `verify/fetchsrc.py`, and `verify/citecheck.py` are
optional
stdlib tools for policy-aware retrieval and provenance recording; they do not
ship a user's institutional access policy or credentials. Set `LSE_HOST_POLICY`
to a user-owned policy file when a local policy is available. Without one, the
policy helper fails closed outside its built-in public API core.

Evidence runs can be persisted by setting `LSE_RUN_HOME` to a writable folder.
If it is unavailable, the skill can still return an inline result, but the
return must say that the run was not filed.

This package does not include Claude hooks, Claude routing dictionaries, local
Zotero/PDF-index connectors, credentials, or source-environment configuration.

## Included surfaces

- `skills/literature-search-chatgpt/SKILL.md` — the main ChatGPT/Codex skill
  (skill id: `literature-search-extract`).
- `references/` — extraction, search, portability, credibility, verification,
  templates, and feedback-loop guidance.
- `connectors/access_policy.py`, `verify/fetchsrc.py`, and `verify/citecheck.py` — optional
  portable policy, provenance, and support-span helpers.
- `loop/` — evidence-run records, identifiers, registry schemas, and tests.
- `scripts/zotero_ris_export.py` — an optional RIS export path using only
  DOI.org and Crossref.

## License

MIT. See the repository [LICENSE](../../LICENSE).
