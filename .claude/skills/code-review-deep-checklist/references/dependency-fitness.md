# Mode C — Syntax / Library / Framework Fitness Audit

This mode audits choices ALREADY MADE (retrospective fitness). Making and
documenting a NEW choice is an ADR → engineering:architecture. Evaluate layers in
order — each is a gate; a failure at an earlier layer makes later layers moot.
Use WebSearch/WebFetch for maintenance-health and CVE facts — do not answer these
from memory.

## Layer 1 — Does it solve the real problem

- The fundamental question: does this tool solve the problem we ACTUALLY have?
- Watch for trend-driven adoption — a fashionable framework without a confirmed
  need for the complexity it brings.

## Layer 2 — License & compliance

- License compatible with project/company policy? This is the first HARD filter.
- License incompatibility discovered after deep integration is the textbook
  "should've been checked on day one" failure — check it now regardless.

## Layer 3 — Maintenance health

- Last release date, issue/PR response speed, maintainer count and activity.
- Hobby-maintained package → require a backup plan: forkable? alternative exists?
  sponsoring the maintainer worth it?
- Stars / open issues / commit activity are initial signals, never the sole basis.

## Layer 4 — Security & vulnerability history

- Serious CVEs? How fast and consistently were they patched?
- For packages handling sensitive input or authorization: security track record
  outweighs feature richness.

## Layer 5 — Integration cost with the existing system

- How much does this tool touch the architecture — how many new RUNTIME (not just
  dev-time) dependencies, how deep the tree?
- Replacement cost: wrapped behind an abstraction interface, or called directly
  everywhere? (Cross-check Mode B's DIP probe.)
- Upgrade cost: what does a typical version bump require?

## Layer 6 — Ecosystem maturity & hype-cycle position

- Position on the maturity curve: experimental / early adopter / mainstream /
  being abandoned?
- Community size, surrounding ecosystem, and non-official documentation determine
  whether the team can self-resolve issues.

## Build vs Buy framework

- Reserve self-building for capabilities that create genuine competitive
  differentiation; adopt existing solutions for everything else.
- Real cost is TCO: integration + training + long-term maintenance + future
  migration/exit — not sticker price.
- Not a one-time decision: scale and needs change; recommend a re-evaluation
  cadence, not a locked-in verdict.

## The unifying question

For every audited dependency, answer explicitly:

> Is this dependency/syntax choice locked into the system's core path, or properly
> wrapped as a boundary component that can evolve or be replaced as requirements
> change?

If the audit concludes "replace / wrap / fork X": recommendation goes in this
report; the decision record itself is an ADR — hand off to
engineering:architecture. If the fix is "put it behind a swappable interface",
that aligns with the user's standing baseline-behind-interface preference — say so
and scope the wrapper, don't rewrite the pipeline.
