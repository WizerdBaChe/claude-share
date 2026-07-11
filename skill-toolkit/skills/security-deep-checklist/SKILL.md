---
name: security-deep-checklist
description: >-
  Deep security (資安) audit — blue-team informed defensive review beyond a quick diff
  scan. Trigger on "資安檢核", "資安健檢", "security audit", "找漏洞" on a module/project,
  deployment/config posture review, air-gapped risk assessment, "如果被攻擊我們看得到嗎", or named
  vulnerability classes (XSS, SQL injection, CSRF, supply chain 投毒…) as the review goal.
  Modes: (A) code-level audit, (B) deployment & environment posture, (C) detection &
  response readiness. NOT for a quick pre-merge scan (→ /security-review); no
  penetration testing or exploit writing. Full disambiguation:
  ~/.claude/skill-trigger-dict.md.
---

# Security Deep Checklist

Security review fails in two directions: scanning only the code while the system
falls to a default credential, or hardening the perimeter while the code trusts
every input. This skill is the deliberate, blue-team-informed deep pass: it audits
what an attacker would try AND what a defender would need. It is NOT the fast
pre-merge gate — "check my pending changes for vulns" → stop and use
/security-review instead.

Defensive scope only: findings and remediation guidance. Never produce working
exploit payloads; a proof-of-concept description ("this input reaches this sink
unescaped") is enough evidence.

## Blue-team frame (why the three modes)

A real blue team's work splits into: prevent (hardening, secure config, patch &
vulnerability management), detect (SIEM/log monitoring, detection engineering,
threat hunting), and respond (incident response, containment, forensics) — with
asset inventory and threat intelligence underneath, and MTTD/MTTR as the
performance measures. A codebase audit only covers "prevent". The mode split
mirrors this: Mode A = is the code itself attackable; Mode B = is the deployed
environment attackable; Mode C = when (not if) something gets through, would we
see it and could we act. A system that passes A and B but has no logging fails
the audit — undetectable compromise is a finding, not a nice-to-have.

## Mode router — settle this FIRST

| User's ask | Mode | Read |
|---|---|---|
| Security audit of code: file / module / PR / repo | A: Code audit | [references/code-audit.md](references/code-audit.md) |
| Config, deployment, infra, network exposure, supply chain | B: Posture audit | [references/deployment-audit.md](references/deployment-audit.md) |
| "Can we detect/respond?" — logging, alerting, IR readiness | C: Detection readiness | [references/detection-readiness.md](references/detection-readiness.md) |
| Full security 健檢 ("整體資安健檢") | A + B + C | all three, report per mode |

Deployment context modifies Mode B/C weighting — establish it in Part 0.

## Part 0 — Meta questions before reading anything

1. **Asset & data sensitivity**: what does this system hold that an attacker
   would want (credentials, PII, money-moving actions, compute)? Depth follows
   value — an internal toy tool does not get an ASVS L3 pass.
2. **Deployment context** (changes the whole checklist): internet-facing /
   internal network only / air-gapped? Cloud or self-hosted? Each context gets
   its own risk section in deployment-audit.md.
3. **Trust boundaries**: sketch where untrusted data enters (users, third-party
   APIs, files, devices) and where privilege changes. Findings concentrate at
   boundaries; a review that doesn't know the boundaries is grep with extra steps.
4. **Existing controls**: auth mechanism, framework (its built-in protections
   count — flagging "no CSRF token" in a framework that auto-injects one is a
   false positive), WAF/proxy, secrets manager, logging stack.
5. **Standards anchor**: default to OWASP Top 10:2025 categories as the shared
   vocabulary for findings (A01 Broken Access Control … A10 Mishandling of
   Exceptional Conditions), and OWASP ASVS 5.0 when the user wants a
   requirements-level checklist. Cite the category ID in each finding.

## Scope rules (override checklist enthusiasm)

- **Findings-only by default.** This skill produces a report; it does not patch
  code or change configs. Apply fixes only when the user asks after seeing
  findings.
- **Severity is exploitability × impact, not category.** An XSS on an admin-only
  page behind VPN is not the same severity as the same XSS on a public form.
  State the assumed attacker position (external / authenticated user / insider)
  for every finding.
- **No speculative CVE claims.** Dependency-vulnerability assertions (a library
  version being vulnerable) are volatile external facts — verify against a
  current advisory source (`npm audit` / `pip-audit` / OSV / GitHub advisories)
  before asserting; never from memory. An unverified suspicion is labeled a
  suspicion.
- **False-positive discipline**: before flagging, check whether a framework or
  upstream layer already mitigates (ORM parameterization, template auto-escaping,
  SameSite defaults). A finding must name the actual unprotected path.
- **Secrets found during audit**: report the location and rotate-recommendation;
  never echo the secret value itself into the report.
- **Report artifact**: NEW file, never overwrite an existing report;
  human-readable body in Traditional Chinese with English technical terms inline.

## Handoffs (do not absorb neighboring skills' jobs)

- Quick scan of pending branch changes → /security-review.
- General quality / smells / debt on the same code → code-review-deep-checklist.
- "Should we replace this risky dependency" decision record → engineering:architecture (ADR).
- Findings are design-level for a system still being designed → product-design-thinking Phase 2 security-by-design rules.
- Findings are about AI-agent permissions, blast radius, review process → ai-coding-guardrails.
- Fixing a confirmed vulnerability → normal implementation flow after user approval; re-audit the fix (author ≠ verifier).
- Active incident ("we're being attacked NOW") → engineering:incident-response, not an audit.

## Severity & output contract (all modes)

Rank findings; each carries:

- **Severity**: `critical` (remotely exploitable, high impact — RCE, auth bypass,
  injection reaching data) > `high` (exploitable with conditions, or
  undetectable-compromise class) > `medium` (requires privileged position /
  significant chaining) > `low` (hardening gap, defense-in-depth).
- **OWASP category ID** (A01–A10:2025) or "operational" for Mode B/C items
  outside the Top 10.
- **Attacker position assumed** + **evidence path** (source → sink, or the
  config line), no working exploit code.
- **Remediation**: the canonical fix first (parameterized query, framework
  middleware), not a bespoke filter — blacklist-style patches are a known
  failure mode.
- End with: (a) what was NOT covered (mode, directory, or check skipped —
  silent truncation reads as full coverage), (b) top-3 "fix first" list, since
  a 40-finding report with no ordering gets nothing fixed.

## Pitfalls this skill exists to prevent (builder-negligence patterns)

- "先做功能，安全之後再說" → security absent from design → audit finds
  architecture-level gaps too late. Flag as design finding, hand to
  product-design-thinking if redesign is in scope.
- "權限先放寬，避免影響測試" → permissive defaults ship to production →
  Mode A access-control checks + Mode B config diff against least privilege.
- "輸入我有做基本過濾" → blacklist/front-end-only validation → Mode A demands
  the server-side, allowlist, typed validation layer.
- "錯誤訊息多一點方便除錯" → verbose errors in production leak SQL/paths/versions
  → Mode A error-handling checks (A10:2025).
- "套件先裝，之後再來整理" → unpinned, unaudited dependencies → Mode B supply
  chain checks (A03:2025).
- Perimeter-only mindset ("內網/不聯網就安全") → Mode B air-gapped section:
  insider threat, removable media, long-term unpatched, shared accounts.
- "有 log 就好" → logs exist but nobody would be alerted, or logs leak secrets →
  Mode C.

## Reference files

- [references/code-audit.md](references/code-audit.md) — Mode A: access control,
  authn/session, injection & XSS/CSRF, input-validation architecture, error &
  exception handling, crypto & data handling, resource stability (leak / dirty
  data / retry storm).
- [references/deployment-audit.md](references/deployment-audit.md) — Mode B:
  misconfiguration, supply chain, patching, attack surface, transport security,
  cloud & IoT, air-gapped/internal-network risks, asset & access management.
- [references/detection-readiness.md](references/detection-readiness.md) —
  Mode C: security event logging, log hygiene, alerting & rate limiting,
  monitoring coverage, incident-response readiness.
