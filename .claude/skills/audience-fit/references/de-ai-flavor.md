# De-AI-flavor rules (borrowed, adapted)

> Loaded by audience-fit when the produced text reads AI-flavored, or the
> user says 「AI味」「太像 AI 寫的」. Borrow ledger per the prior-art borrow
> mandate: source is **Nanako0129/sepia** (MIT License, © 2026 Nanako Tsai,
> https://github.com/Nanako0129/sepia) — professional-pass rules extracted
> and adapted 2026-08-30. Fiction/narrative passes were NOT borrowed; this
> environment produces professional documents and UI text only.

## Borrow ledger

| # | Borrowed rule | Adaptation here |
|---|---|---|
| B-1 | Aim at the band, not the opposite pole: human writing is moderate, not the inverse of AI patterns; forced casualness is a new fingerprint | Applies unchanged, and to zh-TW output too |
| B-2 | Select, don't accumulate: 3–5 targeted interventions per document; fix only what a check flagged | Caps every audience-fit rewrite pass |
| B-3 | Deletion > addition (sepia's measured human-editor ratio 74 replace / 18 delete / 8 insert) | Default bias for Mode A rewrites |
| B-4 | Sample the venue first: read 2–3 recent human artifacts from the same venue and match register/length/formatting — "half of measured AI-ness is register mismatch" | Venue = the project's existing accepted docs, or the user's own corrections (e.g. the MFP UAT copy round) |
| B-5 | Never invent specifics (brands, dates, quotes, numbers) | Reinforces the honesty guardrails; a translation pass adds ZERO new facts |
| B-6 | Whitelist before flagging: formulaic containers (changelog sections, RFC/spec headings), formal register in formal venues, enumerated lists, terse replies are NOT slop | Extended: this environment's 「中文名稱 (English name)」 convention and YAML blocks in guides are whitelisted |
| B-7 | Run checks one at a time, sequentially; one isolated hit means little, clusters demand rewrite | Verdict scale kept: clean / isolated hits / cluster |
| B-8 | Four operations — write / review / refactor / recreate | Mapped to audience-fit modes: A≈refactor-or-recreate (into a NEW file), B≈refactor, C≈review |

## The ten professional-text checks (run in order, one at a time)

1. **Support-desk formality** — greetings, apologies, offers to help
   further. Colleagues skip this.
2. **Padding density** — statements adding zero information; long
   explanations of simple facts.
3. **Reader-irrelevant content** — background the reader already has,
   restated questions, scope tours.
4. **Missing judgment** — comparisons without a recommendation, reviews
   without a verdict, postmortems that dodge naming the mistake. (Absent
   subjectivity is a measured slop dimension.)
5. **Vague or invented specifics** — missing versions/paths/commands where
   the venue expects them; confidently wrong facts are the top-tier tell.
6. **Formatting flags** — bold headings substituting for prose; emoji
   decoration; lists of exactly three; identical section lengths; a heading
   restated by its own first sentence.
7. **Conclusion bloat** — "in conclusion/總結來說" sections; generic future
   outlook (「我們會持續改進」).
8. **Template recycling** — the same sentence frame reused across items.
9. **Rhythmic uniformity** — every paragraph and sentence the same length;
   real prose varies depth strategically.
10. **Unsayable fluency** — grammatical but fails reading aloud.

Weight by shape: long-form (reports, postmortems) → checks 2/3/4/9 first;
short replies and UI strings → checks 5/1 first.

## Report format (Mode C, or the self-check before delivering A/B)

Document type · venue sampled (B-4) · checks failed with quoted evidence ·
checks passed · verdict: clean / isolated hits (fix in place) / cluster
(recreate under B-8).
