# Mode B — Deployment & Environment Posture Audit

License: config files, infrastructure-as-code, dependency manifests, deployment
scripts, and (described, not probed) runtime environment. This mode reads and
reports — it does not scan live third-party systems or run intrusive tools
against anything the user doesn't own.

First: pin the deployment context from Part 0 (internet-facing / internal /
air-gapped; cloud / self-hosted). Then run §1–§3 always, plus the matching
context section (§4/§5/§6).

## 1. Security misconfiguration (A02:2025)

- **Default credentials & default config**: admin/admin, vendor defaults on DB /
  message broker / admin panels, framework `SECRET_KEY` left as the example
  value. Scanners find these in minutes.
- **Debug & development artifacts in production**: debug mode flags, verbose
  logging, exposed profilers/consoles (e.g. debug toolbars, `/actuator`,
  GraphQL introspection where not intended), directory listing enabled,
  `.git`/`.env`/backup files reachable under the web root.
- **Admin & management interfaces**: exposed beyond the intended network
  (management ports, DB ports, dashboards) — each open port/interface needs a
  reason; unnecessary services widen the attack surface.
- **Permissive defaults**: CORS `*` with credentials, overly broad file
  permissions, containers running as root, wildcard firewall rules,
  "temporarily relaxed for testing" settings that shipped (compare config
  against least privilege intent — ask the user what was intentional).
- **Security headers / platform hardening**: CSP, HSTS, X-Content-Type-Options,
  frame-ancestors for web apps; cookie flags verified in actual config, not
  assumed from code.

## 2. Software supply chain (A03:2025 — new category)

- **Dependency inventory exists**: lockfile / SBOM-equivalent present and
  committed; without a version-pinned manifest, CVE response is guesswork.
- **Known-vulnerable versions**: run the ecosystem's audit tool (`npm audit`,
  `pip-audit`, `cargo audit`, `dotnet list package --vulnerable`, OSV-Scanner)
  and report actual output — never assert CVEs from memory (volatile facts).
- **Provenance & typosquatting**: new/unusual package names verified against
  the canonical registry entry (author, downloads, repo link); install scripts
  (`postinstall`) reviewed for packages added recently; internal names not
  resolvable from public registries (dependency confusion).
- **Remote inclusion**: `<script src>` from third-party CDNs without SRI
  (subresource integrity), auto-updating plugins/extensions, curl-pipe-to-shell
  install steps in build scripts.
- **Build & CI trust**: secrets in CI logs/vars scoped minimally; third-party
  CI actions/plugins pinned to a hash, not a floating tag.
- **Update policy**: is there any mechanism (bot, scheduled audit) by which a
  vulnerable dependency would ever get noticed and bumped? "No process" is a
  finding even when today's audit is clean.

## 3. Patch & vulnerability management (all contexts)

- OS / web server / DB / runtime versions: supported and receiving updates?
  End-of-life components are standing findings regardless of current CVE list.
- A named owner/cadence for applying security updates exists ("who patches
  this, when?") — unpatched-forever is the single most exploited condition.
- Emergency path: could a critical patch be applied within days? What blocks it
  (no staging, no rollback, vendor lock)?

## 4. Context: internet-facing systems

- **Attack surface enumeration**: list every exposed port / endpoint / API and
  its reason to exist. Anything unexplained is a finding. Public APIs get auth
  + rate limiting by default (rate limiting details → Mode C).
- **Transport security**: TLS everywhere (no plain HTTP for anything carrying
  credentials/sessions), valid certs, HTTP→HTTPS redirect + HSTS; no mixed
  content. MITM assumption: any hop without TLS is readable and modifiable.
- **Cloud misconfiguration**: storage buckets not public unless serving public
  assets by design; security groups / firewall rules scoped to needed sources,
  not 0.0.0.0/0 for management ports; IAM roles least-privilege (no wildcard
  admin for app roles); cloud metadata endpoint unreachable from app-level SSRF
  (ties to Mode A §1); secrets in a secrets manager, not instance user-data or
  env files in images.
- **IoT / edge devices** (if present): per-device credentials (no shared/weak
  defaults), update path exists, network-segmented from core systems — a
  compromised device is a foothold, plan for it.
- **Mass-scan reality**: internet-facing services are found within hours by
  automated scanners; "obscure URL" or "nobody knows this server" is not a
  control. Zero-day exposure is mitigated by minimizing surface + fast patching
  (§3), not by secrecy.

## 5. Context: internal-network systems

- **No perimeter faith**: "it's internal" is not a control — assume phished
  workstation / compromised device on the LAN. Internal services still need
  auth, TLS where feasible, and patching.
- **Lateral-movement resistance**: network segmentation between tiers; internal
  admin interfaces not flat-open to every employee subnet.
- Shared accounts and service accounts with broad reach are the classic
  internal finding — see §7.

## 6. Context: air-gapped / isolated systems

Isolation removes remote attackers but concentrates these:

- **Insider threat**: privileged users are the primary threat actor — least
  privilege, separation of duties for destructive actions, and audit trails
  that the actor cannot edit (ties to Mode C).
- **Removable media**: USB/portable-drive policy and technical controls
  (allowlisting, scanning station) — the standard infection path into closed
  environments.
- **Long-term unpatched**: isolation makes updating hard, so vulnerabilities
  accumulate for years; require a documented offline-update procedure and
  cadence, and compensating controls while behind.
- **Data egress/ingress procedure**: how data legitimately crosses the gap, and
  whether that channel is controlled and logged.

## 7. Asset & access management (all contexts; heavier for internal/air-gapped)

- **Asset inventory**: an authoritative list of machines/services/accounts
  exists — you cannot defend (or patch, or monitor) what isn't inventoried.
- **No shared accounts**: individual identities everywhere or actions become
  untraceable; break-glass accounts documented and monitored.
- **Joiner/leaver process**: departed users' access actually revoked; stale
  accounts and forgotten API keys are standing backdoors.
- **Privilege review**: periodic re-check that access matches current role —
  privilege only ever accumulates unless something removes it.
