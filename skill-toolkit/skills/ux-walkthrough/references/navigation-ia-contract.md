# Navigation and information architecture — the questions that come before the pattern

> Loaded by ux-walkthrough **Step 2, and only when the surface has more than one
> destination** (a rail, a router, tabs, a multi-view shell, a mode switcher).
> Principles only; every entry names the source it rests on and the case that made
> it bind. This is the reference in this skill designed to GROW — §5 is the
> contract that keeps growth from becoming accumulation.

**Why this file leads with questions instead of patterns.** It was born
2026-09-09 from an external case study whose merits are real and were confirmed
on the live surface the same day: role segmentation at the entry, task-oriented
labels, query-parameter routing, working deep links, an explicit
persistence-scope sentence. On that same surface, the entire 23-item primary
navigation contains **zero focusable elements** — every item is
`<nav class="task-item" data-task="…">` with no anchor, no button, `tabIndex -1`
and no `aria-current`. A pattern checklist scores that navigation near full
marks. The question 「這 23 個目的地，鍵盤走得到嗎」 does not. **The catalogue is
the failure mode; the discriminator is the instrument.** Names of patterns appear
below only so a finding can be stated in one word — never as things to adopt.

## 0. How to read this file

- Entries are **discriminators**, not a checklist and not recommendations. Each
  is a question answered **from the artifact** (source, DOM, storage, records),
  plus what each answer means. An entry answered from taste was not applied.
- Order is fixed: **orient (§1) → discriminate (§2) → attribute the ruling
  (§3)**. Skipping §1 is how a walk turns into pattern shopping.
- **A non-applicable entry is declared, never silently skipped** — 「本面無分流
  入口，NAV-2 不適用」 — the same discipline `usability-evidence.md` §2 puts on
  its own list. Silence and a pass are indistinguishable to the next reader.
- Nothing here settles a classification. §3 says which findings belong to
  engineering and which are the user's; a walk that picks the user's answer has
  broken the global Interaction-style rule.
- **One destination, a linear wizard, or a single dialog → stop here.** Say the
  surface has no IA question and return to `decision-point-contract.md`. A rule
  set that fires everywhere is a broken instrument, not a thorough one.

## 1. Orientation — three questions before any pattern is named

**NAV-O1 — How many destinations, and what counts as one here?**
Count the places the person can BE, not the controls that go there. Zero or one
→ §0's stop clause. The count is also the denominator every later entry uses
(「23 個裡有 0 個可用鍵盤到達」): a finding reported without it cannot be sized,
and an unsized navigation finding is an opinion.

**NAV-O2 — Whose world is the division taken from?**
Three candidates and only one is the person's: the user's **tasks** ("what I have
to get done"), the provider's **organisation** (departments, teams, owning
systems), or the **data's** shape (tables, entities, file types). The reading
test is NAV-1. This comes before everything mechanical because it changes what
the mechanics mean: an org-shaped navigation with flawless keyboard support still
asks the person to know the org chart before they can start.

**NAV-O3 — Where does "which one am I in" actually live?**
Name the store: the URL, a component's memory, `localStorage`, a cookie, the
server — or several at once. Read it, never assume it (measured: a site whose
views are addressable by `?task=` keeps the person's ROLE in `localStorage`, so
two halves of "where am I" live in two stores with different lifetimes and
different sharing behaviour). Everything in §2 about restoring, sharing,
returning and resetting is downstream of this single answer.

## 2. Discriminators

### NAV-1 · the label reading test — whose world
**Ask:** read every navigation label as the sentence 「我要____」 / "I need to
___". How many fail to complete?
**Read it as:** failures are named for the provider's structure or the data's
shape (NAV-O2). A high failure rate is not a wording defect — renaming an org unit
produces a lie, not a task.
**Prevents:** the person who does not know which office owns 「健康檢查」 cannot
find it, and no amount of search or copy repairs the division.
**Ruling:** user (the division is a promise about whose world the product speaks);
engineering downstream once ruled.
**Evidence:** 實測 external (23/23 completed the sentence on the case site — a
positive control proving the test does not simply always fire).
**detect:** audit — this file via Step 2. Its checkable twin is
`usability-evidence.md` §2 「every instruction that names a DESTINATION…」, which
proves a label EXISTS; NAV-1 asks whether the SET is the person's.

### NAV-2 · an entry gate answers three questions or it is a quiz
**Ask:** (a) does the person know the answer **at the moment they are asked**;
(b) can they change it later, and from where; (c) what happens if they never
answer?
**Read it as:** a gate asking for a fact the person has not yet learned (an
incoming student who does not yet know whether they count as 僑生) is not
segmentation — it is an exam at the door. (c) is the one nobody writes down.
**Prevents:** an unanswerable first step; and the silent assignment measured on
the case site — a deep-linked arrival that never saw the gate was written
`ntu_onboarding_role = "ug"` in `localStorage`, i.e. quietly placed in the
largest group with no notice and no visible way back to the choice.
**Ruling:** user (whether to gate, and the default); engineering (revisability,
disclosure of the current value).
**Evidence:** 實測 external (localStorage read on a clean session, 2026-09-09).
**detect:** audit — this file; the default's existence is greppable at the write
site.

### NAV-3 · every funnel level must earn its toll
**Ask:** for each level of a cascading selection, how much of what follows does
this level actually remove?
**Read it as:** a level that removes little is a toll booth. Progressive
disclosure is a budget, not a virtue: the person pays one decision per level and
must be repaid in reduced load.
**Prevents:** four-level funnels whose last two levels change three items.
**Ruling:** user (the funnel is the product's shape).
**Evidence:** borrowed (2-level funnel in the case study, convergence not
measured — the ratio was not observable from outside).
**detect:** audit — this file; `none (candidate: a builder-side count of items
before/after each level)`.

### NAV-4 · contextual navigation must disclose that the world was trimmed
**Ask:** when the destination set changes with identity, mode or entitlement,
how does the person learn they are seeing a subset — and how do they see the
whole, or switch?
**Read it as:** a filtered navigation makes 「找不到」 and 「不存在」
indistinguishable, and the person cannot tell which one they are in.
**Prevents:** a hunt for a feature that was never on this identity's rail; the
support question no log can answer.
**Ruling:** user (what each identity sees); engineering (the disclosure and the
switch path).
**Evidence:** 推論 (the case site trims by role; the disclosure was not located
on the two pages read).
**detect:** audit — this file.

### NAV-5 · master–detail has four questions, and three are usually unanswered
**Ask:** (a) how is the selected item marked, in the DOM and not only in pixels;
(b) what does the layout collapse to at the product's declared narrow floor;
(c) what does the detail view show when opened on its own from a link; (d) where
does Back go from the detail?
**Read it as:** (a) is `aria-current`/`aria-selected` or nothing; (b) is usually
"detail only, list lost"; (c) is where a deep link meets an empty context; (d) is
where Back leaves the site.
**Prevents:** the narrow-width dead end — the person opens a shared detail link on
a phone, has no list, and Back exits.
**Ruling:** engineering (a, c, d); user (b, when the collapse changes what the
product is).
**Evidence:** 實測 external (no `aria-current` anywhere on the case site).
**detect:** `usability-evidence.md` §2 selected-state item + the narrow-floor rule
in SKILL.md's Inputs section.

### NAV-6 · addressability — the state that must survive three round trips
**Ask:** which part of "what the person is looking at" survives (1) refresh,
(2) Back, (3) a **clean session** opening the link they would send someone?
**Read it as:** the answer is read from the store named in NAV-O3, never from the
address bar's appearance. State deliberately kept OUT of the URL (privacy, size,
secrets) is a design **when the reason is stated**; the same omission with no
reason is a defect.
**Prevents:** work that cannot be handed to anyone; a refresh that silently
resets a filtered view.
**Ruling:** engineering — this is determinable, not a taste question.
**Evidence:** 實測 local (HTMLToolsLobby: 18 tools, a search box and a category
filter group, and **zero** occurrences of
`URLSearchParams|pushState|replaceState|location.hash` anywhere in its markup
or client script — the filtered view cannot be linked, refresh resets it, and
Back after filtering leaves the site); 實測 external (`?task=` restores the view
in a clean session).
**detect:** `usability-evidence.md` §2 URL round-trip / Back / clean-session
items; `rules/web-navigation-state.md` at build time.

### NAV-7 · the spoken-path test — NAV-6's human twin
**Ask:** say out loud how another person reaches this exact view.
**Read it as:** if the sentence is a click sequence (「首頁 → 碩博班 → 左邊第二
個」), the URL is not doing its job. If it is a link, it is.
**Prevents:** the defect being deferred to implementation — this test needs no
tooling and fires in a design review before any code exists, which is the only
moment addressability is cheap.
**Ruling:** engineering.
**Evidence:** 推論 (restatement of NAV-6 in a form usable without a browser).
**detect:** audit — this file; it is the design-time form of NAV-6's checks.

### NAV-8 · navigation items must be operable controls — parity is not a later pass
**Ask:** of the NAV-O1 destinations, how many are reachable by Tab, activated by
Enter/Space, and openable in a new tab?
**Read it as:** `data-*` plus a click handler ROUTES correctly and AFFORDS
nothing. Routing correctness and navigation affordance are independent axes —
which is why this is a separate entry from NAV-6 and not a clause inside it.
**Prevents:** the founding measurement: 0 of 23 destinations focusable, on a
surface that otherwise models routing cleanly.
**Ruling:** engineering, always. A navigation nobody can Tab to is not a
preference.
**Evidence:** 實測 external (0/23, `tabIndex -1`, no anchors); 實測 local
(HTMLToolsLobby's own nav uses `<a href>` + `aria-current="page"` — the negative
control: the check does not fire on a surface that does it right).
**detect:** `usability-evidence.md` §2 keyboard-equivalence item, counted against
NAV-O1's denominator.

### NAV-9 · one seam for "where am I"
**Ask:** how many stores answer NAV-O3 for the same fact?
**Read it as:** more than one → this is a **state-model** finding, routed as such,
not a navigation one. `decision-point-contract.md` §9 owns the rule; this entry
is only its navigation-layer projection and does not restate it.
**Prevents:** a shared link that opens the right view in the wrong identity.
**Ruling:** engineering.
**Evidence:** 實測 external (view in the URL, role in `localStorage`).
**detect:** `usability-evidence.md` §2 single-seam grep.

### NAV-10 · persistence declares its scope where the person is
**Ask:** for anything the surface remembers, where is the sentence saying how
long it lasts and what loses it — and is that sentence in the same view as the
thing remembered?
**Read it as:** the declaration is part of the feature, not part of the help. It
must also MATCH the implementation (grep the copy against the storage call).
**Prevents:** the person believing progress follows their account.
**Ruling:** engineering (that the declaration exists and is true); user (whether
to upgrade the storage).
**Evidence:** 實測 external — positive control, verbatim on the owning page:
「勾選進度僅儲存於本裝置，更換裝置或瀏覽器後將不會保留」.
**detect:** `usability-evidence.md` §2 persistence-scope item.

### NAV-11 · a progress indicator may claim only what it knows
**Ask:** does a tick mean "the person says they did it" or "the system knows they
did it"?
**Read it as:** the two must not share a visual language. A self-reported
checklist rendered as a system-tracked progress bar is the honest-data rule
broken at the reassurance line — the person reads 「10/10」 as "I am done" when
the product knows nothing of the kind.
**Prevents:** false completion; and its mirror, a real system state shown so
weakly the person re-does the step.
**Ruling:** engineering (the visual distinction and the wording); user (whether
to track for real).
**Evidence:** 實測 external (10 native checkboxes, counter 0/10, self-reported by
the same page that declares device-only storage — internally consistent, and the
positive example of stating the limit).
**detect:** audit — this file; the copy half is handed to audience-fit Mode B.

### NAV-12 · a semantic encoding travels with the items it encodes
**Ask:** where is the legend for a one-glyph code (必/選, ●/○, a colour), and is
it in the same view as the encoded items? Is colour the only carrier?
**Read it as:** a legend one page away is not a legend. Colour-only encoding fails
WCAG 1.4.1 regardless of contrast.
**Prevents:** a code the person decodes by guessing, then acts on.
**Evidence:** 實測 external (the 必/選 legend produced 0 hits on both task pages
read; per the case study it lives on the entry page).
**Ruling:** engineering.
**detect:** `usability-evidence.md` §2 legend item.

## 3. Who rules what

| Finding from | Owner | Because |
|---|---|---|
| NAV-1 NAV-O2, NAV-2 (a)(c) defaults, NAV-3, NAV-4 subset policy | **user ruling** | the division of the world, the gate and the default are promises about whose product this is (global Interaction-style rule) |
| NAV-6, NAV-7, NAV-8, NAV-9, NAV-10 existence, NAV-12 | **engineering** | determinable; a check can decide it, so it may not be deferred to 「只有人能判斷」 |
| NAV-5 | split — (a)(c)(d) engineering, (b) user | the collapse changes what the product IS at narrow width |
| NAV-11 | engineering (encoding), user (whether to track) | |
| wording of any of the above | audience-fit Mode B | this skill hands the row over; audience-fit hands non-wording findings back |

## 4. Tells that you are in the wrong frame

- You are naming patterns before answering NAV-O1–NAV-O3 → catalogue mode. The founding
  measurement is what that costs.
- Every finding you have lands in the wording layer → you are running audience-fit
  Mode B with extra steps; hand it over and stop.
- You are recommending a structure (「加一個側邊欄」「先問身分」) without a
  destination count or a convergence ratio → you are giving a solution to an
  unmeasured problem.
- You judged the navigation good because the URLs are clean → NAV-8 is the
  independent axis you have not read yet.
- You have a finding but no owner from §3 → it is not finished; an unattributed
  navigation finding becomes a unilateral pick the moment someone implements it.

## 5. Growth contract — extension, amendment, retirement

This file will be asked to grow every time a new surface shape shows up. The
contract below binds the FILE (asset property), not whoever edits it.

**Entry shape (all fields, no exceptions).** `id` · Ask · Read it as · Prevents ·
Ruling (§3 owner) · Evidence (`borrowed` external only | `推論` from local
code/semantics | `實測` measured locally or on a named live surface) · `detect`
(a named check in `usability-evidence.md` §2, a rule file, or `audit — this file`;
an explicit `none (candidate: …)` is allowed and countable, silence is not).

**Admission — all four, or it is not an entry.**
1. **Non-duplication:** the question is not already answered by an existing entry.
   A new failure explained by an existing question is a new *example*, and
   examples go in that entry's Evidence line, not into a new NAV-n.
2. **Named failure:** it prevents a failure that can be described as an event, not
   an unease. 「導覽不夠直覺」 is not admissible.
3. **Detect:** someone or something finds the violation. If nothing does, the
   entry is admitted only with `none (candidate: …)` spelled out.
4. **Two-sided calibration:** one surface where it fires (known-true) and one
   where it must not (known-false). An entry with only positive examples is a
   rule that cannot be wrong, which is the same as a rule that measures nothing.

**Amendment.** Loosening an entry ships a regression case reproducing what it
used to catch (global CLAUDE.md gate rule). Tightening states which existing
surfaces newly fail — a tightening that fails nothing is either free or wrong,
and both are worth knowing before it lands.

**Evidence promotion (the intended life of an entry).** `borrowed` → `推論` →
`實測`. An entry still `borrowed` after it has been carried through **three**
walks is reviewed, not renewed: either a walk finally measured it, or the local
world has no instance and it is a rule about someone else's product.

**Retirement.** Never a silent delete. A retired entry leaves a one-line tombstone
in §6 — id, date, reason, and the failure it used to prevent — because the next
person's first question is always 「這條為什麼不見了」. An entry that has never
fired in any walk is a candidate for review, not for deletion: never-firing can
mean the rule is dead, or that the local surfaces are healthy on that axis, and
those two need different responses.

**Ownership.** rule-tier, 🟡. Entries change through the skill's co-upgrade loop
(gap round → disposition), never by drive-by edit during a walk. A walk that
wants a new entry writes the finding and proposes the entry; it does not add it
mid-run — the instrument may not be modified by the measurement it is taking.

**review-when.** (a) WCAG or the NN/g pages cited in Sources change their
numbering or guidance; (b) a project adopts a framework whose router owns the URL
contract (Next.js app router, Nuxt) — then NAV-6 keeps the property and gives up
the mechanism; (c) an entry reaches its third walk still `borrowed` (above).

## 6. Calibration — measured 2026-09-09, two-sided

The pair below is what licenses this file's claims. Each surface passes exactly
where the other fails, which is how a rule set is shown to discriminate rather
than to rubber-stamp.

| Axis | Case site (external, live) | HTMLToolsLobby (local) |
|---|---|---|
| NAV-1 task-shaped labels | ✅ 23/23 complete 「我要…」 | ✅ tools named by the job |
| NAV-6 view state in the URL | ✅ `?task=` restores in a clean session | ❌ 0 URL-state calls; filter + search unlinkable |
| NAV-8 destinations operable | ❌ 0 of 23 focusable | ✅ `<a href>` |
| NAV-5(a) selected state in DOM | ❌ no `aria-current` | ✅ `aria-current="page"` |
| NAV-10 persistence scope stated | ✅ verbatim on the owning page | n/a — nothing persisted |
| NAV-2(c) unanswered gate | ❌ silent `role = "ug"` default | n/a — no gate |

Evidence and method: recorded in the source environment's own skill-review
records (borrow ledger B-1…B-8, the DOM/storage reads, and what was NOT
observed).

**Corrected 2026-09-09 by a controlled A/B run** (same surface, same prompt, same
model; only the instrument varied — recorded in the source environment's own
skill-review records): the arm without this file **also found the NAV-6 defect**, reaching it through the
existing state-model lens. So NAV-6's detection is NOT unique to this file, and no
entry here may claim it is. What the run did measure as this file's contribution
on that surface: the finding was classed as `routing` and attributed to
engineering by §3 rather than hedged as a product-priority call; its verification
covered all three round trips instead of reload alone (a one-round-trip check
would have passed a fix that never exercised Back or a clean session); it ranked
4th rather than 7th. One finding was attributable to the new lens alone — Back not
closing a modal, a routing question about an exit. The arms overlapped on four
findings and diverged on the rest, so this file is an addition to the walk's
vocabulary, never a replacement for it.

Tombstones: none yet.

## Sources (read 2026-09-09)

- W3C WCAG 2.2 Understanding: 1.4.1 Use of Color (A); 2.1.1 Keyboard (A);
  2.4.5 Multiple Ways (AA); 3.2.3 Consistent Navigation (AA); 2.4.8 Location
  (AAA). Cited as CHECKS, never as a compliance claim.
- WAI-ARIA Authoring Practices: `aria-current` for the current item in a set.
- Rosenfeld, Morville & Arango, *Information Architecture* (4th ed.) — the
  organisation-scheme vocabulary behind NAV-O2; used for naming, not as authority.
- NN/g: Progressive Disclosure; 10 Usability Heuristics (2 — match between system
  and the real world) — the standing sources behind NAV-1 and NAV-3.
- Local: `decision-point-contract.md` §9 (single seam), §11 (layout-change
  semantics), §4 (show/disable/hide); `usability-evidence.md` §2 (the checks this
  file's detects point at).
- External case study supplied by the user 2026-09-09 (pattern inventory) plus
  the live measurement in §6 — the inventory is untested prose, the measurement
  is what the entries cite.
