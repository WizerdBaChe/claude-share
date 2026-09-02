#!/bin/bash
# Fail-open mount shim: `run-hook.sh <name>.py` execs the REPO copy of
# hooks/<name>.py with stdin passed through, and exits 0 whenever it cannot.
#
# Why a shim and not a direct python mount: a mount whose target file is
# absent makes python exit 2, which Claude Code treats as a BLOCKING error for
# every matched tool call (hooks/settings.example.json _README; incident #3 in
# hooks/branch_commit_guard.py). Every hook in hooks/ is fail-open by contract;
# the mount must be too. The repo copy is the source of truth and is present on
# every branch that carries this file, so nothing here depends on the
# SessionStart installer having finished.
#
# Cloud-only: outside a remote session (CLAUDE_CODE_REMOTE != true) the
# operator's own ~/.claude/settings.json already mounts these hooks, and a
# second mount would run each guard twice per call.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOK="$ROOT/hooks/$1"
[ -f "$HOOK" ] || exit 0
PY="$(command -v python3 || command -v python)" || exit 0
exec "$PY" "$HOOK"
