# Scientific Domain Expansion Guide
## How to Specialize the General-Purpose Research-Assistance SKILL

> This document defines the architectural conventions, decision-trigger
> mechanisms, and AI behavioral rules that apply when a new research Domain is
> added to the SKILL.
> Audience: anyone adding a new Domain Profile to the SKILL — users or
> developers.

---

## 1. Recap: The SKILL's Three-Layer Architecture

```
Layer A: Generic research skeleton (Tier 0-7)
  └─ references/tier-framework.md
  └─ Never modified directly. Supplies the structure shared by all domains.

Layer B: Domain-specific content (three kinds — see §2 decision tree)
  └─ domains/<domain_name>.md          = base profile (the domain's shared core, 7 nodes)
  └─ domains/<domain_name>/<x>.md      = sub-profile (a specialized branch: material /
  │                                      phenomenon / method; shares the domain's first
  │                                      principles but adds its own traps/methods/triggers)
  └─ domains/<domain_name>/<x>.md      = reference / boundary note (depth or orientation;
  │                                      NO standing triggers)
  └─ domains/_routing.md               = manifest: which files exist + when to load each
  └─ This document specifies how to write this layer.

Layer C: Task instance (Session Context)
  └─ Supplied by the user in each conversation (current research state,
     steps already completed, etc.)
  └─ Using Layer B's criteria, the AI maps Layer C onto Layer A's Tiers.
```

**Base profiles stay lean.** A base profile is the domain's *shared core* — the 7 nodes at
domain-general level. Specialized branches (a specific material, a specific phenomenon/
method) do NOT get appended to the base file; they become sub-profiles under
`domains/<domain_name>/`. This keeps the base = the intersection all sub-topics share, and
stops it from growing unbounded. Every new file must be registered in `domains/_routing.md`
in the same change — that manifest is the only place the AI's load list lives.

**AI's logical sequence when using this**:
1. Identify which domain the user is in (match against the `domains/` directory).
2. Load the corresponding Domain Profile (Layer B).
3. Map the user's input onto the generic framework's Tiers (Layer A).
4. Output: current position + gaps + next step + risk warnings.

---

## 2. Classifying new content: the two-gate decision tree

Whenever you want to add content, run it through **two gates in order**. This decides
whether it becomes a new domain, a sub-profile, or a reference/boundary note.

> **The test is NOT "is this new/unfamiliar content?"** Novelty alone never justifies a new
> domain — that fragments the taxonomy endlessly. Only the three divergence conditions in
> Gate 1 decide the domain boundary. New-but-related content that shares the domain's first
> principles and toolset stays *inside* the domain as a sub-profile.

### Gate 1 — Domain boundary: does it break any of the three divergence conditions?

If **any one** of the three conditions below holds, the content belongs to a **different
domain** (create a new base profile, or it belongs to a sibling domain that may not exist
yet). If **none** holds, the content stays inside the current domain → go to Gate 2.

#### Trigger condition 1: Non-overlapping measurement toolset

> The core characterization tools used in the new domain do not appear in any
> existing Domain Profile's tool inventory.

**Examples**:
- Expanding from "semiconductor physics" to "soft-matter biophysics" → adds
  Rheometer, Patch-Clamp, Confocal Microscopy → triggers a new profile
- Expanding from "semiconductor physics" to "III-V power devices" → tool
  overlap is high → stays in the same domain (Gate 2 decides sub-profile vs base)

#### Trigger condition 2: A shift in first principles

> The new domain's core theoretical framework is incompatible with existing
> Domain Profiles and cannot share the same set of "inviolable physical
> constraints."

**Examples**:
- Expanding from "electromagnetics/plasmonics" to "quantum many-body physics"
  → Maxwell's equations → second quantization; the core language changes →
  triggers a new profile
- Expanding from "plasmonics" to "photonic crystals" → still Maxwell's
  equations + periodic boundary conditions, same FDTD/FEM toolchain →
  stays in the same domain → Gate 2

#### Trigger condition 3: Incompatible quality-metric set

> The new domain's criteria for "what counts as good research" cannot be
> measured with an existing Domain Profile's metrics.

**Examples**:
- Expanding from "Ti materials" to "biomedical materials" → metrics shift from
  photocatalytic rate to cytotoxicity (IC₅₀) and osseointegration (BIC%) →
  triggers a new profile

### Gate 2 — Form: sub-profile vs reference/boundary note

Reached only when Gate 1 says the content stays inside the domain. Now decide its **shape**
by one question: **does it carry its own standing if-then rules?**

- **Sub-profile** — it has domain-specialist traps, named fitting methods, plausibility
  ranges, or decision triggers that a domain generalist would miss and that should fire
  automatically. Litmus test: *you can write "user says/does X → AI should warn/ask Y".* It
  reuses the parent's Nodes 1-3 (theory/tools/toolchain) and fills only the nodes where it
  adds specialist judgment — typically Node 4 (fitting), 5 (metrics), 6 (pitfalls), 8
  (triggers). See the sub-profile mini-template in §8. File: `domains/<domain>/<x>.md`,
  registered as `sub-profile` in the manifest with `Active triggers? = yes`.
- **Reference / boundary note** — pure depth (derivation, background) or orientation, with
  **no** standing triggers. A *boundary note* specifically demarcates the domain edge and
  routes the user OUT to a sibling domain when they cross it. File: `domains/<domain>/<x>.md`,
  registered as `reference` or `boundary` with `Active triggers? = no`.

One-line rule: **can write "user says X → auto-warn Y" ⇒ sub-profile; only readable ⇒
reference.**

### Base vs sub-profile: where does in-domain content go?

- **Base** = what *all* sub-topics of the domain share (the intersection). Only content
  every researcher in the domain needs belongs here.
- **Sub-profile** = a branch relevant only when the user is in that branch (a specific
  material, phenomenon, or method).

This is what keeps the base profile from bloating: it holds the shared core, branches live
beside it.

### Worked examples (Topological Insulator domain)

| Content | Gate 1 | Gate 2 | Verdict |
|---|---|---|---|
| **Bi₂Se₃** specifics | shares TI first principles + ARPES/transport toolset → in-domain | material-specific traps (bulk conduction from Se vacancies, aging/oxidation) | **sub-profile** (material-scoped) |
| **WAL** (weak antilocalization) | shares TI framework + magnetotransport → in-domain | own fitting method (HLN) + fit pitfalls (single-field-range α, decoherence-length temperature dependence) | **sub-profile** (phenomenon/method-scoped) |
| **HOTI** (higher-order TI) | still single-particle band topology + tight-binding/DFT; extends bulk-boundary correspondence but does NOT break the 3 conditions → in-domain | new-territory traps (trivial corner states via filling anomaly, nested Wilson loop prerequisites) | **sub-profile** (new-territory; *candidate for future promotion* to its own domain if it later grows a non-overlapping toolset or incompatible metrics — do NOT pre-promote) |
| **SPT order vs Topological order** | the *comparison* is orientation; but *intrinsic topological order* itself breaks all 3 conditions (long-range entanglement, anyons/TQFT, entanglement-entropy metrics) → that side is a **future separate domain** | the comparison note carries no experimental traps; its job is to route out | **boundary note** in TI (points to the future intrinsic-topological-order domain) |

---

## 3. Required Structure of a Domain Profile (Seven Nodes)

Every Domain Profile must contain the following seven nodes; none may be
omitted. This is the minimum requirement for the AI to use the Profile
correctly.

```markdown
# Domain Profile: <Domain Name> (English full name)

> Scope of applicability (2-3 lines)
> Scientific nature:
> Engineering nature:

## 1. Theoretical Framework Anchoring
## 2. Measurement Tool Inventory
## 3. Standard Modeling Toolchain
## 4. Domain-Specific Fitting Methods
## 5. Domain-Specific Quality Metrics
## 6. Common Assumption Pitfalls
## 7. Literature Anchors
## AI Decision-Trigger Checklist for This Profile
```

---

## 4. Authoring Rules for Each Node

### Node 1: Theoretical Framework Anchoring

**Must include**:
- A table of core first principles, classified by scale or problem type
- A list of **"inviolable physical constraints"** (precise conditional
  statements the AI can use for automatic warnings)
- At least one "mandatory Tier 0 confirmation" decision point, in this format:

```markdown
> **Decision point (mandatory Tier 0 confirmation)**: when the user describes
> X, the AI must confirm:
> "Is your goal (A)... / (B)... / (C)...?"
> The three goals correspond to entirely different [measurement / modeling /
> analysis] paths.
```

**Authoring principles**:
- "Inviolable physical constraints" should be precise conditional statements,
  not vague "things to watch out for"
- Each constraint should note the consequence of violating it (wrong
  computed result / invalid measurement / conclusion that doesn't generalize)

### Node 2: Measurement Tool Inventory

**Must include**:
- A table organized around "measurement target," with columns: Tool / Output
  information / Applicable conditions / **Common misuse**
- The "Common misuse" column is the core payload — it's what lets the AI give
  preventive warnings

**Authoring principles**:
- For every tool, also write down the situations where it does *not* apply,
  not just what it can do
- Destructive vs. non-destructive measurements need to be flagged (this
  affects the ordering of an experimental sequence)

### Node 3: Standard Modeling Toolchain

**Must include**:
- A tool pipeline (ASCII flow diagram) running from "the most fundamental
  theoretical scale" to "the final application scale"
- For each tool: its input requirements + the conditions under which its
  output can be trusted

**Authoring principles**:
- Don't just list tool names — explain "under what conditions you'd use this
  tool instead of the next one"
- Note the data-handoff format between tools (so the AI doesn't recommend a
  tool combination that can't actually be chained together)

### Node 4: Domain-Specific Fitting Methods

**Must include**:
- The domain's "named" standard fitting methods (e.g. Tauc Plot,
  Oliver-Pharr, Scherrer)
- For each method: applicable conditions + common errors (⚠️ format) +
  the correct approach

**Authoring principles**:
- The point isn't to explain the method's underlying principle, but to spell
  out clearly "under what circumstances this method gives a spurious result"
- If there's a corresponding "correct way to read off the value" (e.g. the
  standard linear-extrapolation procedure for a Tauc Plot), describe it
  explicitly

### Node 5: Domain-Specific Quality Metrics

**Must include**:
- Metric name / abbreviation / physical meaning / typical value range
- "Typical value range" is the key item — the AI needs this to judge whether
  the user's result is plausible

**Authoring principles**:
- Typical value ranges should distinguish "industry/commercial level" from
  "research frontier level"
- Also flag the "suspicious result range" (both too good and too bad need
  confirmation)

### Node 6: Common Assumption Pitfalls

This is the **highest-value node** in the entire Domain Profile.

**Must include four columns**: Pitfall description / Trigger condition / How
to recognize it / Correct approach

**Authoring principles**:
- The "trigger condition" needs to be specific enough that the AI can
  automatically recognize it from the user's own wording
- A pitfall should be tacit knowledge that only a domain expert would know,
  not an obvious mistake
- Target count: at least 6 pitfalls per domain

**Example of how to write a trigger condition**:
```
Trigger condition: "User says: we used the Drude model to simulate the
response of Au nanostructures at 550 nm"
→ The AI should warn immediately, regardless of whatever the user says next
```

### Node 7: Literature Anchors

**Must include**: 3-5 references that "every researcher in this field should
know"

**Authoring principles**:
- Prefer, in order: Textbook > Review > Methods paper
- For each reference, note "why this one is essential reading" (what
  standard terminology it defines, what methodology it established)

### AI Decision-Trigger Checklist (Node 8, required)

Format: `- [ ] User says/does X → AI should do Y`

This checklist is what the AI uses to proactively trigger confirmations
during a conversation.
Each trigger point should be:
- Something recognizable from the user's natural-language input (a behavior
  or statement)
- Mapped to a concrete AI action (ask / warn / suggest)

---

## 5. AI Behavioral Rules: When Confirmation with the User Is Mandatory

In the following situations, the AI must not assume anything on its own and
must confirm the user's current need and goal.

### Category A: Theoretical-framework divergence (scale/model choice)

**Trigger phrases**:
- "I want to simulate X" → must confirm the intended simulation scale
- "I want to compute Y" → confirm whether this is a first-principles
  calculation or a device-level one
- "I'm using model Z" → confirm whether model Z is applicable at the current
  problem's scale/material/frequency range

**Why the AI cannot assume**:
The same term (e.g. "simulate carrier transport") means something entirely
different at the DFT, k·p, and TCAD levels. Picking the wrong level
invalidates the entire computational path, and this is very hard to notice
partway through.

### Category B: Research-goal trade-off triangle

**Trigger phrases**:
- A design task described in terms of "performance metrics" (maximize
  efficiency, minimize loss)
- And the domain has a known "trade-off triangle" (e.g. SPP's
  confinement–propagation–loss triangle, or a semiconductor device's
  speed–power–breakdown-voltage triangle)

**How to confirm**:
"What is your priority ordering among design goals (A)... / (B)... / (C)...?
Different orderings lead to different optimization directions."

**Why the AI cannot assume**:
A trade-off triangle has no single "optimal solution" — only a "Pareto-optimal
point" for a specific goal. The AI choosing on its own is effectively making
the user's research-direction decision for them.

### Category C: Invasive/destructive measurement tools

**Trigger phrases**:
- The user has planned a sequence of measurement steps that includes a
  destructive measurement (TEM, SIMS, FIB)
- And that destructive measurement is placed in the middle of the sequence

**How to confirm**:
"[Tool name] is a destructive measurement — the sample cannot be used for
further measurements afterward. Has your measurement order already accounted
for this?"

**Why the AI cannot assume**:
Sample preparation is costly (epitaxy/nanofabrication can take days to
weeks); getting the destructive-measurement order wrong can make the rest of
the plan impossible to execute.

### Category D: Model choice in data fitting

**Trigger phrases**:
- The user describes a fitting task, and the Domain Profile has a
  corresponding "domain-specific pitfall" for it
- The user hasn't explained why they chose that particular fitting model

**How to confirm**:
"[Fitting method] has an applicability condition: [condition description].
Does your sample meet this condition?"

**Why the AI cannot assume**:
The wrong fitting model produces a result that "looks numerically reasonable
but is physically meaningless" — this is the hardest type of error to catch
after the fact.

### Category E: Anomalous results (too good or too bad)

**Trigger phrases**:
- The value the user reports for a metric falls outside the Domain Profile's
  "typical value range" (whether too high or too low)

**How to confirm**:
"The [metric] value you reported ([value]) is [above/below] the typical range
for this field ([typical value]). Has this been cross-confirmed with another
measurement method?"

**Why the AI cannot assume**:
An anomalous result could be either a major discovery or a measurement/
computation error. Until the user confirms which, the AI should not steer the
interpretation toward either direction.

### Category F: Cross-domain conflict (highest alert level)

**Trigger phrases**:
- The user's question spans two Domain Profiles, and the two Profiles'
  "inviolable physical constraints" potentially conflict

**How to confirm**:
"Your research spans [Domain A] and [Domain B], which apply different
judgment criteria on [specific issue]. Which domain's standard are you
currently treating as primary?"

**Example**:
- A user researching "TiN as an SPP waveguide material" → involves both
  ti_materials.md (TiN mechanical/compositional properties) and
  plasmonic_waveguide.md (ε(ω) accuracy)
- The two Profiles have different concerns about "how to measure TiN's
  optical properties" (the Ti-materials profile cares about composition; the
  Plasmonics profile cares about ε(ω) accuracy)

---

## 6. Domain Profile Quality Verification Checklist

Before a newly created Domain Profile is added to the SKILL, it should pass
the following checks:

### Structural completeness

- [ ] All seven nodes are present
- [ ] The decision-trigger checklist (Node 8) has no fewer than 5 items
- [ ] All table columns are filled in (no blank cells)
- [ ] There are no fewer than 6 common assumption pitfalls, each with all
  four columns complete

### Content quality

- [ ] The "inviolable physical constraints" can be converted into precise
  if-then rules
- [ ] Every measurement tool has a description of "when it doesn't apply"
- [ ] Typical value ranges are backed by literature and distinguish research
  level from commercial level
- [ ] Literature anchors point to original papers that are actually
  accessible (not secondary sources)

### Boundary clarity

- [ ] The Profile's scope of applicability is clearly stated (to avoid
  overlap with other Profiles)
- [ ] A comparison against the closest existing Domain Profile confirms
  sufficient difference in measurement tools / first principles / quality
  metrics

### Cross-domain compatibility

- [ ] The domains this profile is most likely to cross with have been
  identified
- [ ] In a cross-domain situation, there is a clear Layer-A-Tier mapping for
  how the AI should switch between the two Profiles

---

## 7. _template.md (Blank Template for Adding a New Domain Profile)

```markdown
# Domain Profile: <Domain Name> (English full name)

> Scope of applicability:
> Scientific nature:
> Engineering nature:

---

## 1. Theoretical Framework Anchoring

### Core first principles

| Scale/problem type | Foundational theory | Core physical quantity |
|------------|---------|-----------|
| | | |

### Inviolable physical constraints (the AI should warn the user here)

1.
2.
3.

> **Decision point (mandatory Tier 0 confirmation)**: when the user describes
> [X], the AI must confirm:
> "Is your goal (A)... / (B)... / (C)...?"
> The three goals correspond to entirely different [measurement / modeling /
> analysis] paths.

---

## 2. Measurement Tool Inventory

### <Measurement category 1>

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|---------|------|---------|---------|---------|
| | | | | |

### <Measurement category 2>

| Measurement target | Tool | Output information | Applicable conditions | Common misuse |
|---------|------|---------|---------|---------|
| | | | | |

---

## 3. Standard Modeling Toolchain

```
<First-principles-scale tool>
→ Output:
    ↓
<Intermediate-scale tool>
→ Input:
→ Output:
    ↓
<Device/application-scale tool>
→ Output:
```

---

## 4. Domain-Specific Fitting Methods

### <Method name 1>

**Applicable conditions**:
**Common error**: ⚠️
**Correct approach**:

---

## 5. Domain-Specific Quality Metrics

| Metric | Abbreviation | Physical meaning | Typical value range |
|------|------|---------|------------|
| | | | |

---

## 6. Common Assumption Pitfalls

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|------|---------|---------|---------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

---

## 7. Literature Anchors

| Type | Reference | Why it matters |
|------|------|-------|
| | | |
| | | |
| | | |

---

## AI Decision-Trigger Checklist for This Profile

- [ ] User says/does X → AI should do Y
- [ ] User says/does X → AI should do Y
- [ ] User says/does X → AI should do Y
- [ ] User says/does X → AI should do Y
- [ ] User says/does X → AI should do Y
```

---

## 8. Sub-profile mini-template (Blank Template for a Branch)

A sub-profile is NOT a full 7-node profile. It **inherits** the parent base profile's
Nodes 1-3 (theoretical framework, measurement tools, modeling toolchain) and fills only the
nodes where it adds specialist judgment. Omit any node it does not extend. It MUST have the
Decision-Trigger Checklist (that is what makes it a sub-profile rather than a reference).

Register it in `domains/_routing.md` as a `sub-profile` row before it is considered done.

```markdown
# Sub-profile: <Branch Name> (English full name) — under <Parent Domain>

> Parent domain: <domain_name>.md
> Branch axis: material | phenomenon | method | new-territory
> Scope (1-2 lines): what this branch covers, and where it stops (defer to parent / sibling).
> Inherits from parent: Nodes 1-3 (theory / tools / toolchain) unless overridden below.

## 4. Branch-Specific Fitting Methods   (include only if it adds any)

### <Method name>
**Applicable conditions**:
**Common error**: ⚠️
**Correct approach**:

## 5. Branch-Specific Quality Metrics   (include only if it adds any)

| Metric | Abbreviation | Physical meaning | Typical value range |
|------|------|---------|------------|
| | | | |

## 6. Branch-Specific Assumption Pitfalls   (the core payload)

| Pitfall | Trigger condition | How to recognize it | Correct approach |
|------|---------|---------|---------|
| | | | |

## AI Decision-Trigger Checklist for This Sub-profile   (REQUIRED)

- [ ] User says/does X → AI should warn/ask Y
- [ ] User says/does X → AI should warn/ask Y
```

> **Promotion note.** A new-territory sub-profile that later grows a non-overlapping toolset
> or an incompatible quality-metric set has crossed Gate 1 — promote it to its own base
> profile (7 nodes) and leave a boundary note behind in the parent. Do not pre-promote.

---

## Appendix: SKILL Directory Structure (this skill's actual layout)

```
skills/scientific-research-guide/
├── SKILL.md                          ← Operating protocol (Gate A-E; load order:
│                                        tier framework first, then domain, then session)
├── references/
│   ├── tier-framework.md             ← Layer A: generic Tier 0-7 skeleton
│   │                                    (not modified per domain)
│   ├── method-selection.md           ← Generic method-selection decision aids
│   └── deliverables.md               ← Output templates for each Tier
├── domains/                          ← Layer B: domain-specific content
│   ├── _routing.md                   ← Manifest: which domain files exist + load triggers
│   ├── _template.md                  ← Blank template for a new BASE profile (7 nodes)
│   ├── domain-expansion-guide.md     ← This document (expansion conventions)
│   ├── plasmonic_waveguide.md        ← base profile (established)
│   ├── topological_insulator.md      ← base profile (established)
│   └── topological_insulator/        ← that domain's sub-profiles & boundary notes
│       ├── bi2se3.md                 ← sub-profile (material)      [example, when authored]
│       ├── wal.md                    ← sub-profile (phenomenon)    [example, when authored]
│       ├── hoti.md                   ← sub-profile (new-territory) [example, when authored]
│       └── spt_vs_topological_order.md ← boundary note            [example, when authored]
└── evals/
    └── evals.json                    ← Test cases
```

> Sub-profile folders (`domains/<domain>/`) are created only when a domain actually needs
> its first branch — do not pre-create empty folders.
