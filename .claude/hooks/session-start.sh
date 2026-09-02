#!/bin/bash
# SessionStart hook (project scope): install this repo's environment into the
# cloud container's ~/.claude before the first turn, so the session runs with
# the source environment's global CLAUDE.md, rules, ops layer, skills, hooks
# and agents ("LikeLocal"). Idempotent; the installer's log goes to a file and
# only a one-line card reaches the session context (SessionStart stdout is
# injected into context, so verbosity here is a per-session tax).
#
# ops_health_nudge.py is chained here AFTER the install rather than mounted as
# a sibling: hooks in one matcher group run in parallel, and on a fresh
# container the nudge would otherwise stat() an ops/ that does not exist yet
# (fail-open, so silent — which is a missed session, not an error). Chaining
# gives it the tree it checks. The hook's stdin (session_id, cwd, source) is
# captured first and replayed to it unchanged.
#
# Cloud-only by design: on the operator's own machine ~/.claude IS the source
# and this repo is reference material (ADOPTERS.md, "Where to put things").
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

input="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PY="$(command -v python3 || command -v python)" || exit 0
LOG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/cloud-bootstrap.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null

{
  echo "== $(date -u +%FT%TZ) session-start install"
  "$PY" "$ROOT/cloud-bootstrap/bootstrap.py" install
} >>"$LOG" 2>&1 || {
  echo "[cloud-bootstrap] install FAILED — read the log at ~/.claude/cloud-bootstrap.log, then run: python3 cloud-bootstrap/bootstrap.py install"
  exit 0
}

"$PY" "$ROOT/cloud-bootstrap/bootstrap.py" summary
if [ -f "$ROOT/hooks/ops_health_nudge.py" ]; then
  printf '%s' "$input" | "$PY" "$ROOT/hooks/ops_health_nudge.py" 2>/dev/null
fi
exit 0
