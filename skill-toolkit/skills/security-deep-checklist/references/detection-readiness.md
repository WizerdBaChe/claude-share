# Mode C — Detection & Response Readiness Audit

Premise (blue-team reality): prevention eventually fails; the differentiating
questions are how fast a compromise is DETECTED (MTTD) and RESPONDED to (MTTR).
This mode audits whether the system produces the signals a defender would need
and whether anyone/anything would act on them. For a solo-developer or small
project, "SIEM" scales down to "centralized logs + a few alerts + a written
what-if note" — audit proportionally, don't demand a SOC.

## 1. Security event logging (A09:2025 — Logging & Alerting Failures)

Are the security-decisive events recorded at all? Minimum set:

- Authentication: login success/failure, lockouts, MFA events, password/
  credential changes, token issuance and revocation.
- Authorization: DENIED access attempts (failed authz is attacker telemetry),
  privilege/role changes, admin-function use.
- Data: access/export of sensitive records (bulk reads especially), deletion
  and modification of critical data.
- System: config changes, dependency/deployment changes, service start/stop,
  security-control state changes (e.g. a validation layer disabled).
- Input rejections: validation failures and malformed-request spikes — early
  probe signature.

Each event needs: timestamp (synced clock/timezone), actor identity, source
(IP/session), action, target, outcome. A log line that can't answer "who did
what to what, from where, and did it work" won't support an investigation.

## 2. Log hygiene (logs must not become the leak)

- **No secrets/PII in logs**: passwords (including failed-login attempted
  passwords), tokens, session IDs, full card/ID numbers, private keys — grep
  log statements and error handlers for sensitive fields (pairs with Mode A §6
  data classification). Logs are usually the least-protected copy of data.
- **Log injection**: user-controlled strings written raw can forge lines or
  break parsers — encode/escape newlines and control chars.
- **Tamper resistance**: logs shipped off-host (or at least append-only /
  separately permissioned) so the attacker — or insider (Mode B §6) — can't
  edit their own trail; retention long enough to investigate an incident
  discovered late (breaches are often found months in).
- **Volume sanity**: log storms (retry loops, repeated errors) can drown
  signals and fill disks — that's an availability finding too (Mode A §7).

## 3. Alerting & abuse-rate controls (detection engineering, scaled down)

Logging without alerting is forensics-only — A09:2025's rename to "Logging &
ALERTING Failures" is exactly this point:

- **Alert-worthy conditions defined**: brute-force pattern (N failed logins),
  logins from new geography/impossible travel where relevant, privilege
  escalation, mass data export, error-rate spikes, integrity-check failures.
  For small systems even an email/webhook on the top 3 conditions beats zero.
- **Rate limiting exists and is observable**: login/OTP endpoints, expensive
  queries, public APIs — limits enforced server-side, and LIMIT HITS are logged
  (a tripped rate limit is a detection event, not just a 429).
- **Someone receives it**: an alert channel nobody reads is a finding; name the
  receiving human/rotation, even if it's just the owner's inbox.
- **Baseline & anomaly awareness** (mature setups): normal traffic/behavior
  baselined so deviations (odd hours, odd volumes, odd endpoints) are
  detectable; MITRE ATT&CK can serve as the coverage map for which attacker
  behaviors have any detection at all.

## 4. Monitoring coverage & blind spots

- **Coverage across tiers**: app logs alone miss the OS/network layer; host
  metrics alone miss app-level abuse. List which tiers (app / host / network /
  cloud control plane) emit anything, and name the blind spots explicitly.
- **Centralization**: logs aggregated somewhere queryable across sources —
  correlating an attack across 5 machines by hand-ssh is not a capability.
- **Health of the monitoring itself**: would anyone notice if logging stopped
  (agent died, disk full, misconfigured shipper)? Silent monitoring death is a
  classic pre-incident condition.
- **Third-party/dependency signals**: security advisories for the stack reach
  the owner somehow (mailing list, bot) — pairs with Mode B §2 update policy.

## 5. Incident-response readiness

Scaled to the organization — for a solo project this is a one-page note, but it
must exist BEFORE the incident:

- **Playbook**: for the top realistic scenarios (credential leak, data breach,
  defacement/malware, ransomware/data loss), who does what first? Includes the
  decision of when to take the system offline.
- **Containment levers inventoried**: can you actually rotate all secrets,
  invalidate all sessions, block an IP, disable a compromised account, roll
  back a deployment — and how long does each take? Untested levers count as
  half-existing.
- **Forensics-ready**: the logs from §1–§2 are sufficient to reconstruct "what
  did the attacker touch" — test by walking one hypothetical incident through
  the actual log fields.
- **Backups as security control**: backups exist, are versioned/offline enough
  to survive ransomware, and RESTORE has been tested (an unrestored backup is a
  hope, not a control).
- **Post-incident loop**: lessons feed back into Mode A/B checks and new §3
  alert conditions — detection engineering is iterative by nature.
