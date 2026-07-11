<!--
  <URL> — curated, agent-neutral distillation of the
  workflow-checkpoint methodology (canonical source:
  ~/.claude/skills/workflow-checkpoint/<URL>).

  Reference-compile class (<URL>): the automatic triggering does
  not migrate; this file carries the checkpoint format and flows only. The
  phase-log FILES it produces are plain markdown inside project repos —
  they are readable by every agent platform, which is exactly why this
  protocol is worth carrying across platforms: any agent can both write
  and reconstruct from the same log.
-->

# Phase-Log Protocol — checkpoints for long-running multi-session projects

Purpose: leave concise, high-quality checkpoints at phase boundaries so a
future session reconstructs context by reading ONE small file — never by
replaying conversation history.

## When to checkpoint

Proactively ASK whether to checkpoint when:
- A phase/milestone clearly completed and the user is moving on.
- Work mode shifts from idea/discussion into implementation, or a key
  document asset is delivered (spec, architecture, finalized design).
- A large task just passed validation (build all-green, feature accepted).
- The user explicitly asks for a checkpoint / phase summary.

Do NOT trigger for minor edits, single-file changes, pure Q&A, or mid-phase
work. Never write files without explicit consent.

## Project name resolution

Prefer the project's existing short code; otherwise a concise slug from the
working directory name. Always use the SAME name across sessions so
`references/<project><URL>` stays consistent and appendable.

## Writing a checkpoint

1. Ask first; on consent, draft a concise phase summary.
2. Write to `references/<project><URL>` inside the project:
   - Create `references/` and the file if absent; ALWAYS append a new
     section — never overwrite existing content.
   - Write the section entirely in English (read by AI in future sessions;
     English maximizes token efficiency and parsing reliability).
   - Sections are concise and scannable, like index entries: one sentence
     per point, keywords and highlights for rapid navigation.
   - **Two-layer principle**: the log stays summary-only. Longer details
     worth preserving (full decision rationale, extended design notes,
     post-mortems) go to a separate English file
     `references/<project>-phase<N>-<slug>.md`, linked via a `- Detail:`
     line in the section header.
3. After writing, report which file and which phase section was written.

### Section format (follow order and headings strictly; all English)

```
# Phase Checkpoint
- Project: <project name>
- Phase: <phase number and name, e.g. Phase 2 – UI Layout>
- Status: in-progress / completed
- Date: <absolute date — never relative dates>
- Detail: <references/<URL> — omit line if no detail file>

## Goals
- Bulleted goals for this phase

## Decisions
- Key design/technical decisions, including rejected alternatives and why

## Changes
- <file path>: <summary of what changed>

## Open Questions / TODO
- Unresolved issues and next actions
```

Multiple checkpoints = multiple `# Phase Checkpoint` sections in the same
file, appended chronologically.

## After the checkpoint — context compaction

If the platform supports compacting/summarizing the conversation, offer it
after the checkpoint is written: the phase-log now holds the durable
context, so lossy compaction is safe. A good compaction note preserves:
project name and phase structure/status, key recent decisions, modified
files, critical constraints for continuing, and any standing language/
formatting rules. Safe to drop: debug detail, outdated option exploration,
trial-and-error history.

## New-session reconstruction (user says "continue this project")

1. Minimum tokens first: read ONLY `references/<project><URL>` —
   do not replay history; do not read the whole repo first.
2. Reconstruct: project goals, phase progress and status, most recent key
   decisions, unresolved TODOs.
3. Load a `- Detail:` file only when deep-diving that phase is necessary.
4. Summarize current state in one sentence, then ASK the user which
   phase/TODO to start from.

## Design principles

- Always seek consent before writing files or compacting.
- The phase-log is an index/entry — details live in separate files.
- The goal is always: the next session takes over by reading one small file.
