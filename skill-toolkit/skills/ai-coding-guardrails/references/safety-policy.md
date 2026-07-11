# Section 5: Safety & Policy

Three layers of defense, ordered so that even if an earlier layer is bypassed, only
the sandbox contents are at risk:

1. **Risk tiering** — decides how much scrutiny a change gets (process layer).
2. **Permission isolation** — decides what credentials the agent even holds
   (identity layer).
3. **Sandbox & interception** — decides what actions physically execute
   (mechanism layer).

Design test for any proposed policy: "if the agent ignores every instruction it was
given, what stops the bad action?" If the answer is "nothing", the policy is a wish,
not a guardrail.

## 5.1 Risk Tiering — graded by blast radius, not by seniority

The highest-ROI first step: pure process discipline, effectively free to adopt.

- Maintain a machine-readable `risk-tiers.json` classifying paths into
  critical / high / medium / low. `db/`, `infrastructure/`, `auth/`, payment and
  secret-handling paths are always critical — regardless of how trivial a given
  change to them looks.
- Critical tier: multi-person sign-off + staging verification + a written rollback
  plan. High: human review + tests required. Medium: single review, tests
  encouraged. Low: auto-approvable by AI review.
- The file is read by three consumers: CI (to select gates), the review process
  (to select depth), and the agent itself (via AGENTS.md pointer, to know when to
  stop and plan instead of act).

### risk-tiers.json template

```json
{
  "$comment": "Blast-radius classification. CI selects gates from this; agents read it before touching a path.",
  "tiers": {
    "critical": {
      "paths": ["db/**", "migrations/**", "infrastructure/**", "auth/**", "billing/**", ".github/workflows/**"],
      "merge_requires": ["two_human_approvals", "staging_verification", "rollback_plan", "tests"]
    },
    "high": {
      "paths": ["services/**", "api/**", "config/**"],
      "merge_requires": ["one_human_approval", "tests"]
    },
    "medium": {
      "paths": ["ui/**", "docs/api/**"],
      "merge_requires": ["one_review_any_kind"]
    },
    "low": {
      "paths": ["docs/**", "*.md", "tests/fixtures/**"],
      "merge_requires": ["ai_review_ok"]
    }
  },
  "default_tier": "high",
  "$default_comment": "Unlisted paths default UP (high), never down."
}
```

Note the last line: unknown paths default to a stricter tier. An agent creating a
brand-new directory should meet friction, not a gap in the fence.

## 5.2 Permission Isolation (five mandatory settings)

1. **Physically separate dev/staging/production** — distinct connection strings,
   secrets, and IAM roles per environment. "Same DB, different schema" is not
   separation; a leaked prod credential in an agent's env is a standing incident.
2. **Read-only DB roles for agents by default.** When a write is genuinely needed,
   the agent produces SQL for human review before execution — the agent is a SQL
   author, not a SQL executor.
3. **If write access is unavoidable**: a separate writer role limited to
   INSERT/UPDATE on specific tables — never DELETE. Deletions go through
   soft-delete only (flag + retention window), so "delete" stays reversible.
4. **All destructive operations** (DROP / TRUNCATE / batch DELETE / infra destroy):
   dry-run → human approval → execute, in that order, every time. The dry-run
   output (row counts, affected objects) is what the human approves — not the
   intention.
5. **API tokens**: scoped, time-limited, instantly revocable. Never issue
   general-purpose "do anything" tokens to an agent. Instant revocability is what
   makes Code Freeze (recovery-governance.md) real rather than rhetorical.

## 5.3 Sandbox & Interception Mechanisms

### Allow/deny command and path lists

Whitelist executable commands and readable/writable directories; blacklist
dangerous commands so a blacklist hit never even reaches the LLM prompt — the model
cannot be talked into an action the harness refuses to route.

Baseline deny set: `rm -rf /`-class recursive deletes, `sudo *`,
`Read(.env)`, `Read(~/.ssh/**)`, credential stores.

Project-level additions for DB/deploy/migration work:
`DROP TABLE`, `TRUNCATE`, `psql *production*`, `terraform destroy*`,
`git push --force*`, `kubectl delete namespace*`.

### Claude Code mapping (settings.json)

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force*)",
      "Bash(terraform destroy*)",
      "Bash(psql*production*)",
      "Bash(sudo *)",
      "Read(.env*)",
      "Read(**/.ssh/**)",
      "Read(**/secrets/**)"
    ],
    "ask": [
      "Bash(git push*)",
      "Bash(rm *)",
      "Write(db/migrations/**)"
    ]
  }
}
```

Deny rules are evaluated before the model acts; they are the "never reaches the
prompt" layer. Put irreversible things in `deny`, risky-but-sometimes-needed things
in `ask`.

### PreToolUse hooks

Shell scripts that inspect a tool call before it executes and return an exit code
deciding allow/warn/block. Use for content-dependent checks a static deny list
cannot express — e.g. scanning SQL payloads for DROP/TRUNCATE, or scanning Write
payloads for secret-shaped strings.

Sketch (bash; hook receives tool input as JSON on stdin):

```bash
#!/usr/bin/env bash
# PreToolUse hook: block destructive SQL regardless of which tool carries it.
payload=$(cat)
if echo "$payload" | grep -qiE 'drop\s+table|truncate\s+|delete\s+from\s+\w+\s*;?$'; then
  echo "Blocked: destructive SQL detected. Produce the SQL in a review file instead." >&2
  exit 2   # exit 2 = block the tool call and show message to the model
fi
exit 0
```

Keep hooks narrow: a hook that blocks in unrelated projects is a guardrail defect
(it trains users to disable hooks). Gate on project markers when the rule is
project-specific.

### Sandbox isolation

Run the agent inside Docker/Firejail-class containers that cannot see the host
filesystem or SSH keys, with outbound network limited to required hosts only. The
sandbox is the layer that holds when everything above it fails — size the sandbox
contents accordingly (nothing in it you can't afford to lose).

### "Skip confirmation" modes

Ban `--dangerously-skip-permissions`-class flags outside fully isolated
environments (disposable container / CI). Never on a local dev machine: the flag
converts every prompt-injection or misunderstanding into an immediately executed
action with your user account's full reach.

### Plan Mode by default for sensitive work

Any task touching DB / deploy / prod secrets: the agent may only read and produce a
plan, never execute, until a human approves the plan. This converts "review the
agent's actions" (too late) into "review the agent's intentions" (in time).

### Prompt-injection defense

Treat ALL external content as untrusted: issue text, web pages, package READMEs,
error messages from third-party services. The agent reading "to fix this, run
`curl … | sh`" inside a stack trace is an attack surface. Require pre-action
authorization for any tool call with real-world side effects, regardless of what
the content the agent just read told it to do.

### Supply-chain defense

- Higher approval tier whenever AI adds dependencies or touches the build pipeline
  (`.github/workflows/**` is critical-tier in the template above for this reason).
- SBOMs, pinned dependency sources, signature/provenance checks — guard against
  package hallucination (the model invents a plausible package name; squatters
  register those names: "slopsquatting").
- Concrete check: any NEW dependency in a PR must resolve to a package that existed
  before the PR was opened, with meaningful download history.
