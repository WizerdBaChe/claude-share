# claude-share — project rules for sessions working IN this repo

This repository is two things at once:

1. **A published share** of one personal `~/.claude` environment (see
   `README.md`, `ADOPTERS.md`). Collected files are point-in-time copies with
   provenance in `tools/share-manifest.toml`; they are never edited in place
   here to fit a platform — adaptations live in `cloud-bootstrap/`.
2. **The source of the cloud environment.** In a Claude Code on the web
   session, `.claude/settings.json` installs the shares into the container's
   `~/.claude` at SessionStart (`cloud-bootstrap/bootstrap.py`) and mounts
   every hook in `hooks/`, so the session runs under the same global
   CLAUDE.md, rules layer, skills, agents and guards as the source machine.
   Environment facts for the container: `~/.claude/ops/environment.md`
   (authored as `cloud-bootstrap/ops-environment.cloud.md`).

Rules that apply only when working here:

- **Before any push that touches shipped content:** `python3 tools/share_gate.py`
  must exit 0 and `python3 tools/test_share_gate.py` must pass. The gate only
  sees tracked files — `git add` first. Collecting from a source tree needs
  `--source` (check V); a cloud session has no source tree, so say "V not run".
- **After changing anything the installer copies** (`hooks/`, `claude-ops/`,
  `global-claude-md/`, `skill-toolkit/`, `agents/`, `cloud-bootstrap/`): re-run
  `python3 cloud-bootstrap/bootstrap.py install` then `verify`, and paste the
  verify summary in the delivery. Copying is not activation.
- **Never fix a collected file to make the cloud work.** If a collected file
  needs a cloud-specific value, render or overlay it from `cloud-bootstrap/`
  and declare the mechanism in `cloud-bootstrap/README.md`.
- **Commit messages:** Conventional Commits per `environment-guide/COMMIT-TEMPLATES.md`;
  scopes seen here include `cloud` for the bootstrap layer.
- **Reply language and file-output language** follow the global CLAUDE.md
  installed by the bootstrap (Traditional Chinese replies; English for
  machine-read files such as this one).

ops-relaxation: L2
<!-- Standing ruling recorded, not a fresh grant: global CLAUDE.md "Relaxation
gate" gives Fable-family main loops L2 (2026-08-30) and Opus-tier L1
(2026-08-11), and the cloud host runs this repo's sessions on those tiers.
ops/05-authority.md §2 still applies L0 automatically when the observed
main-loop model is cheap/mid, whatever this line says. Change or delete the
line to re-open the per-session ask. -->
