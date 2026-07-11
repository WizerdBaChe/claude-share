# Extraction Taxonomy

Use this table to classify items flagged during conversation scan. Each category includes a description, typical dialogue signals, and output format.

---

## Category 1: Technical Decisions

**What to include**
- Which technical approach was chosen and why
- Which approaches were explicitly rejected and why
- Architectural forks ("we discussed X vs Y, went with Y")

**Typical dialogue signals**
- "Let's go with X because..."
- "Don't use Y, we tried it and hit Z"
- "This makes more sense because..."

**Output format**
```markdown
### Decision: [topic]
- **Chosen**: [final choice]
- **Reason**: [why]
- **Rejected option(s)**: [X], because [reason]
- **Context**: [conditions under which this decision holds]
```

---

## Category 2: Pitfalls & Bugs

**What to include**
- Traps in tools, packages, or APIs and how to work around them
- Wrong assumptions that led to wasted effort
- Version compatibility or environment setup issues
- Repeated mistakes Claude made in this conversation

**Typical dialogue signals**
- An error appeared and a fix was found
- "No, you did it again..." (Claude repeated a mistake)
- "This has a bug", "this doesn't work"

**Output format**
```markdown
### Pitfall: [short description]
- **Symptom**: [when/how you hit this]
- **Root cause**: [why it happens]
- **Fix/workaround**: [how to resolve]
- **Prevention**: [how to avoid next time]
```

---

## Category 3: Effective Workflows

**What to include**
- Task decomposition patterns that worked ("do A before B")
- Prompt patterns that produced better outputs
- Steps that required human confirmation and couldn't be automated
- Particularly effective tool combinations

**Typical dialogue signals**
- User proactively broke down the task ("first show me X, then...")
- Output quality improved after user requested a specific format
- "This is faster", "let's always do it this way"

**Output format**
```markdown
### Workflow: [topic]
- **Approach**: [concrete steps or sequence]
- **When to use**: [applicable scenarios]
- **Why it works**: [underlying reason]
- **Caveats**: [exceptions or limitations]
```

---

## Category 4: Project Constraints & Context

**What to include**
- Hard limits that cannot be changed (technical or business constraints)
- Project-specific term definitions ("in this project, X means Y")
- Stakeholder restrictions or preferences
- Environment specifics (pinned versions, target platform)

**Typical dialogue signals**
- "We can't use X because..."
- "In our context, X means..."
- "That can't be changed, it's an external constraint"

**Output format**
```markdown
### Constraint: [topic]
- **Limit**: [what it is specifically]
- **Reason**: [why this limit exists]
- **Impact**: [which decisions this constraint shaped]

### Term Definitions
| Term | Meaning in this project | Notes |
|------|------------------------|-------|
| X    | Y                      | ...   |
```

---

## Category 5: User Preferences

**What to include**
- Output format preferences ("no bullets, give me prose")
- Tone preferences ("cut to the conclusion, skip the preamble")
- Working rhythm ("give me a draft first, I'll revise" vs "get it right first try")
- Confirmation habits ("check with me before each step")

**Typical dialogue signals**
- User revised Claude's output format and said "this is better"
- "Always do it this way", "I like this approach"
- User corrected the same type of formatting issue repeatedly

**Output format**
```markdown
### Preference: [category]
- **Preference**: [specific description]
- **Anti-pattern**: [what this user dislikes]
- **Scope**: [universal preference, or only in specific contexts]
```

---

## Category 6: Reusable Principles

**What to include**
- General principles that apply beyond this project
- Judgment rules derived from this project's experience
- Behavioral guidelines worth passing to future Claude instances

**Test**: If you moved this rule to a completely different project, would it still be useful? If yes, it goes here.

**Output format**
```markdown
### Principle: [topic]
- **Rule**: [concrete, actionable description]
- **Source**: [which experience this was derived from]
- **Applies when**: [conditions under which this rule holds]
- **Exceptions**: [when not to apply it]
```

---

## Classification Decision Tree

```
This piece of information is about...

A choice between tools / architecture / packages?
  └→ Category 1 (Technical Decisions)

An error, trap, or wrong turn?
  └→ Category 2 (Pitfalls & Bugs)

How to break down a task, phrase a prompt, or confirm progress?
  └→ Category 3 (Effective Workflows)

A hard limit or a term specific to this project?
  └→ Category 4 (Project Constraints & Context)

The user's format, tone, or pacing preferences?
  └→ Category 5 (User Preferences)

A principle that generalizes across projects?
  └→ Category 6 (Reusable Principles)
```
