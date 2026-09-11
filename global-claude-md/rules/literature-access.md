---
paths:
  - "**/verify/*facts*.json"
  - "**/verify/w1*_*.json"
  - "**/*evidence*.{json,md}"
  - "**/record/W*證據表*.md"
  - "**/02_文獻證據/**"
  - "**/references/*.bib"
  - "**/fetch_*.py"
  - "**/*_wave*.py"
  - "**/literature-search-extract/**"
  - "**/EvidenceRuns/**"
  - "**/literature-host-policy.json"
review-when: the machine's VPN resolves to an institution other than NTU (a different licence agreement then governs, and the allowlist below is void); a publisher on the routing table changes its Terms of Use; an official text-and-data-mining API becomes available for a host currently on the hand-it-to-the-user row; or a publisher blocks the institution's IP range (that event retires the whole automated row, not just one host)
---

# Literature access: the evidence artifact records how it was obtained, and never defeats an access control

Written 2026-09-10 from the SSLD W15 wave, where an institutional VPN turned four
paywalled publishers reachable in one step and the obvious next thought was
"drive a headless browser with a logged-in profile". That thought is the reason
this file exists. Index: not in `CLAUDE.md` (over budget) — registered in
`ops/rule-registry.md` and discovered by the `paths:` globs above.

## The property

**A citation-bearing evidence artifact states, per source, the access route it
came through and the licence basis for that route; and it never contains content
obtained by circumventing a technical access control.**

Two consequences, both of which are the asset's property and not a reminder to a
reader:

- A source row whose `access` field says only "read the paper" is incomplete. The
  field names the route (`open access` · `institutional IP via VPN, browser,
  human-paced` · `publisher TDM API` · `abstract only` · `handed to the user`)
  and, when the route was institutional, the fact that the reader was a Licensed
  User of that subscription.
- An artifact may hold a quotation, a number and a citation obtained under a
  subscription. It may **not** hold a redistributable copy of the licensed
  full text, and no deliverable built from it may ship that copy onward — the
  licence names *Licensed Users* as the audience, and a proposal, a deck or a
  published page is not that audience.

## Why circumvention is out of scope, not merely risky

The technical control IS the licensor's enforcement of the licence term. Read the
two governing texts before treating an anti-bot challenge as an obstacle:

- **IEEE Xplore Terms of Use, Institutional Subscribers, prohibited list**
  (read 2026-09-10 through an entitled session): institutional subscribers are
  NOT permitted to *"Use robots or intelligent agents to access, search and/or
  systematically download any portion of IEEE Xplore."* Note the verb list —
  **access** and **search**, not only bulk download. The same list forbids making
  Xplore content available to anyone who is not a Licensed User, and transmitting
  any portion of it by e-mail or file transfer. The permitted list, by contrast,
  covers viewing, searching, downloading documents and printing individual
  articles. So: a person reading is licensed; a program reading is not, whatever
  its volume.
- **NTU 校園網路使用規範** (計中, 101.4.24 修正) §2 forbids「不法下載或重製受著作
  權法保護之著作」and §3 forbids「以任何方式濫用網路資源…及其他影響本校網路系統
  正常運作之行為」. The VPN is a campus network service; abusing it is a campus
  offence independent of what the publisher does about it.

The failure mode that matters is not a warning e-mail. Publishers enforce these
clauses by **suspending the subscribing institution's IP range**, which takes
every researcher at the university offline, not the one who ran the script. That
is why the rule is a redline and not a judgement call about volume.

A headless browser or a real profile carrying a live SSO session does not change
any of this. It makes the access *look* human while remaining an intelligent
agent, which is the specific act the clause names — dressing it up is aggravation,
not mitigation. Separately, a session must never enter credentials to obtain
access; an already-authenticated profile is not a loophole around that, it is the
same act at one remove.

## Routing — try in this order, stop at the first that answers

1. **Open access, preprint, repository, government report.** arXiv, OSTI, PMC,
   institutional repositories, publisher OA. No licence question, full text,
   quotable. Always look here first even when the paywalled copy is reachable —
   it is faster and it leaves no compliance question behind.
2. **An official programmatic interface**, where one exists and the project is
   entitled: Crossref, Unpaywall, OpenAlex for metadata; a publisher's own TDM
   API for text. This is the licensed automation route and it is the ONLY route
   on which systematic retrieval is legitimate.
3. **Ordinary HTTP retrieval of hosts that serve it**, at human pace, for
   named targets — never a sweep. Measured hosts live in `ops/environment.md`;
   they are facts with a shelf life, not a permission.
4. **The in-app browser, driven at human pace, for a NAMED article**, on a host
   whose terms do not ban agent access. One target, one fetch, the citation
   recorded. This is the boundary of what an agent does on a subscription.
5. **Hand it to the user.** For any host that bans agent access outright (IEEE
   Xplore by the clause above), or that answers with an anti-bot challenge: name
   the article, give the DOI and the URL, and let the user open it. Their reading
   is licensed; the assistant reading it for them, on that host, is not.

**An anti-bot challenge (202, 403, 418, a JS interstitial, a CAPTCHA, a
proof-of-work page) is a routing signal, never a difficulty to overcome.** On
seeing one: stop, record the host as hand-to-the-user for this wave, and move to
the next source. Retrying with a different user agent, a cookie jar, a headless
browser or a logged-in profile is the prohibited act, and CAPTCHAs specifically
are never to be solved or bypassed.

**The surface-escalation ladder is the same act, spread over four calls.** curl →
WebFetch → headless browser → the user's real logged-in browser is not four
independent attempts; it is one attempt that keeps changing costume until the
control gives way, and the last rung is the most prohibited, not the most
legitimate. Two hard stops inside it:

- **Do not read a licence stop out of a hook that is not about licences, and do
  not read a licence pass out of one either.** `browser_pane_scope_guard` denies
  third-party hosts in the in-app pane for blast-radius reasons — the pane shares
  the desktop app's GPU child process — and its own allowlist file names
  claude-in-chrome as the sanctioned alternative. So moving to Chrome after that
  denial is what that guard intends, and it settles nothing about whether the
  publisher permits agent access. The licence question has no hook: it is checked
  here, against the host's own terms, before any surface is chosen. A guard that
  DID encode the constraint would end the route outright; this one does not, and
  a session that treats its redirect as clearance has confused two controls.
- **This binds the dispatcher first.** A wave prompt that tells a subagent which
  browser to use on a banned host has already committed the violation; the
  subagent merely executed it. Name the routing table in the prompt, not a
  surface, and let step 5 be reachable — a licensed empty answer.

Recovery when a source was already read this way: keep the citation, mark the
row's route as non-compliant, and have the user — a Licensed User — re-open the
article and confirm any quote that is load-bearing before it enters a
deliverable. Do not silently keep it, and do not silently delete the finding.

## What a wave may do, stated as limits

- Named targets only. "Find whether anyone has published X" is a search over
  metadata (step 2) followed by individual retrievals (steps 1, 3, 4) — never a
  crawl of a publisher's corpus.
- No mirroring. A PDF fetched to extract three sentences and a number is working
  material; it lives in the scratch directory and does not become a project
  asset. What lands in the repository is the quote, the numbers and the citation.
- The `still_open` list is part of the deliverable. A gap that stayed open
  because the only source sits behind a host on step 5 is recorded as exactly
  that — "not retrieved, hand-to-user, DOI ..." — never as "not found".
- One quote per claim, as short as carries the fact. A verbatim clause quoted for
  compliance (as above) is fair use of a functional text; a verbatim page of a
  paywalled article is redistribution.

## The instrument side

A fetch helper that a project keeps must print, per source, the host, the route
taken and the HTTP status — so that a later reader can tell a paywall from an
absence, and a challenge from a 404. A wave that reports "no source found" for a
target whose only host answered 403 has misreported a routing outcome as an
evidentiary one; that is the same error class as a gate ruling on what it cannot
determine, and it is caught the same way — by printing the ruler beside the rate.
