# Mode A — Code-Level Security Audit

License: applies to the code unit the user named (file / module / PR / repo).
Establish trust boundaries and existing framework protections first (SKILL.md
Part 0) — every finding below must name the actual unprotected path.

Tactic: work source → sink. Enumerate entry points (HTTP handlers, message
consumers, file parsers, CLI args, IPC), then follow untrusted data to dangerous
sinks (query builders, template output, shell/exec, file paths, deserializers,
redirects). Grep-first passes (dangerous APIs, secret patterns) are cheap — run
them before manual reading and report what was scanned.

## 1. Access control & authorization (A01:2025)

- **Object-level checks**: every data access verifies the requester may touch
  THAT resource, not just "is logged in" — direct object references (IDs in
  URL/body) are the classic miss (IDOR). Changing an ID in a request must not
  yield someone else's data.
- **Server-side enforcement only**: any check that exists only in the UI (hidden
  button, disabled field, client-side route guard) counts as absent.
- **Default deny**: unmatched routes / new endpoints require auth by default
  (middleware ordering), not per-handler opt-in that a new handler can forget.
- **Privilege escalation paths**: role changes, admin functions, mass-assignment
  (request body setting `role`/`is_admin` fields directly into a model).
- **SSRF** (folded into A01 in 2025): user-supplied URLs fetched server-side —
  validate scheme/host allowlist; block link-local/metadata addresses.
- **Function-level authz**: admin/API endpoints reachable without the role check
  the UI implies (hidden ≠ protected).

## 2. Authentication & session (A07:2025)

- Password storage: adaptive hash (argon2/bcrypt/scrypt) with per-user salt —
  never MD5/SHA-x, never reversible, never plaintext.
- Password/MFA policy exists where it matters; no hardcoded or default
  credentials in code, seed data, or test fixtures that ship.
- Session tokens: unpredictable, regenerated on login (session fixation),
  invalidated on logout/password change, sane expiry.
- Cookies: `HttpOnly`, `Secure`, `SameSite` set for session cookies.
- Token handling: JWTs verified (algorithm pinned, `none` rejected, signature
  actually checked), secrets not in client code; refresh-token rotation.
- Credential-recovery and "remember me" paths get the same rigor as login —
  they are login.
- Brute-force resistance exists at the code level (lockout/backoff hooks) or is
  explicitly delegated to infra (record which — Mode C verifies alerting).

## 3. Injection & output encoding (A05:2025)

- **SQL/NoSQL**: parameterized queries / ORM bindings everywhere; grep for
  string concatenation and f-string/template interpolation into query text —
  including ORDER BY / table-name dynamic fragments that parameterization can't
  cover (need allowlists).
- **XSS**: template auto-escaping on; every `innerHTML` / `dangerouslySetInnerHTML`
  / `v-html` / manual HTML assembly justified and sanitized (DOMPurify-class,
  not homemade regex); output encoding matches context (HTML body vs attribute
  vs JS vs URL). Stored XSS: data written by one user and rendered to another is
  the highest-value path.
- **Command/path**: shell exec with user input (prefer arg arrays, no
  `shell=True`-style paths); path traversal on file names (`../` — resolve and
  prefix-check against a base dir).
- **Deserialization / parsing** (A08:2025): no `pickle`/`eval`/`Function` on
  untrusted input; XML external entities disabled; YAML safe-load.
- **CSRF**: state-changing endpoints protected by framework CSRF middleware or
  same-site + token pattern; GET never mutates state. Check the framework's
  default first — flag only the actually-unprotected route.

## 4. Input-validation architecture

Not just "is there validation" but WHERE and HOW:

- **One layer, at the trust boundary**: a unified server-side validation layer
  (schema/DTO validation) rather than per-module ad-hoc checks — scattered
  validation guarantees a missed spot and version drift.
- **Allowlist over blacklist**: type / length / format / range positively
  defined. A blacklist filter ("strip `<script>`") is a finding by itself —
  encoding and format tricks bypass it.
- **Client-side checks are UX, not security**: any validation existing only in
  the front end counts as absent.
- **Upstream-shape assumptions**: data from third-party APIs / files / other
  services is untrusted input too; schema-validate it, or an upstream change
  becomes a silent security/correctness hole.

## 5. Error & exception handling (A10:2025 — new category)

- **Swallowed failures around security checks**: `catch { }` (or broad
  catch-and-continue) wrapping authn/authz/validation means the check can fail
  open. Every security-relevant exception path must fail CLOSED (deny).
- **Verbose errors to clients**: stack traces, SQL text, file paths, framework
  versions in production responses = reconnaissance material. Generic message
  out, detail into server logs.
- **Partial-failure states**: multi-step writes without transaction/rollback →
  half-committed "dirty data" that later authz/business logic misreads.
  Consistency failures become security failures.
- **Abnormal-condition logic**: what happens on timeout, null, overflow,
  concurrent modification? "Exceptional" paths that skip the normal
  authorization flow are a classic bypass.

## 6. Cryptography & data handling (A02/A04:2025)

- **No hand-rolled crypto**: custom algorithms or misused primitives (ECB mode,
  static IV/nonce reuse, homemade token generation with `random` instead of a
  CSPRNG) — use the platform's vetted library and cite it in the remediation.
- **Secrets in code**: grep for API keys, tokens, connection strings, private
  keys in source / config committed to VCS / client-side bundles. Found one →
  location + rotation recommendation, never echo the value.
- **Sensitive-data classification**: PII / credentials / tokens identified and
  treated differently — encrypted at rest where warranted, excluded from logs
  and debug output (pairs with Mode C log hygiene), masked in error messages.
- **Transport assumptions in code**: no hardcoded `http://` endpoints for
  sensitive calls; TLS verification not disabled (`verify=False`,
  `rejectUnauthorized: false` are findings).

## 7. Resource stability as a security property (DoS-by-neglect)

Availability is a security objective; these are code-level checks, not ops:

- **Unbounded growth**: caches/maps without eviction, listeners/handles never
  released, queues without backpressure → memory leak → OOM under normal load,
  trivially forceable by an attacker.
- **Retry storms**: retries without cap + exponential backoff + jitter; fan-out
  retries amplifying into an internal DDoS against DB/downstream APIs; circuit
  breaker absent on critical dependencies. Also floods logs (drowns Mode C
  signals).
- **Unbounded input dimensions**: request body size, file upload size,
  pagination limits, regex on user input (catastrophic backtracking / ReDoS),
  zip-bomb style decompression without limits.
- **Dirty-data accumulation**: error records / orphan rows that grow without
  cleanup and degrade queries or distort permission/business decisions.

## 8. AI-generated code security addendum

When the unit under audit is substantially AI-generated (pairs with
code-review-deep-checklist Mode A §9):

- Plausible-but-wrong security code is the signature failure: verify the
  security-relevant lines actually do what they look like (e.g. sanitizer
  imported but not applied to this path; auth decorator present but ordered
  after the route registration).
- Check for hallucinated/unofficial package names in new dependencies
  (typosquatting risk) — verify each new import exists upstream and is the
  canonical package (feeds Mode B supply chain).
- Copied boilerplate may carry permissive CORS (`*`), debug flags, or example
  credentials — grep the diff for these defaults.
