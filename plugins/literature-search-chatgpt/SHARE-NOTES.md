# ChatGPT/Codex package notes

## Boundary

This is a staging and distribution copy for the OpenAI ChatGPT/Codex plugin
format. The source skill remains at
`skill-toolkit/skills/literature-search-extract/`. A future Claude package is a
separate target and must receive its own manifest and adapter review.

## Portability decisions

- Kept the share-reviewed, de-identified skill payload as the content base.
- Added a portable root `plugin.json` and a `.codex-plugin/plugin.json`
  compatibility fallback.
- Kept the plugin's `skills/` tree self-contained so remote Git installation
  does not depend on the parent repository's skill loader.
- Removed dependence on the source machine's global Claude hook policy by
  making policy configuration explicit through `LSE_HOST_POLICY`.
- Kept local corpus connectors, credentials, institutional entitlements, and
  Claude hooks outside the package.
- Marked the package as ChatGPT/Codex in the plugin name, README, metadata, and
  marketplace label.

## Known limits

- The host still needs a usable web search/page-fetch or user-supplied source
  to perform discovery and extraction. The skill must report degradation when
  that capability is absent.
- The package includes the portable P4.5 support-span gate
  (`references/verification-gate.md` and `verify/citecheck.py`); it does not
  include institution-specific connectors or entitlement handling.
- The public package does not include an institutional literature entitlement
  or a shared host policy. Users must supply their own permitted access route.

## Verification record

The package must pass the plugin manifest validator, the skill frontmatter
validator, the package's Python self-tests, the share pre-scan, and the parent
repository's public share gate before publication. These checks establish
package structure and exercised code behavior; they do not establish a user's
licensed access to every publisher or human acceptance of every research
answer.
