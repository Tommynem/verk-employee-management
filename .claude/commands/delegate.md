# /delegate - Task Delegation Command

Delegate tasks to specialist agents following the three-tier delegation model for Verk Bookkeeping.

## Usage

```
/delegate <task-description>
/delegate --agent <agent-name> <task-description>
/delegate --analyze <task-description>  # Auto-select appropriate agent
```

---

## Three-Tier Delegation Model

### Tier 1: Primary Does Itself (<5 min, trivial)

Do NOT delegate these - handle directly:
- One-line config edits
- Simple variable renames
- Quick documentation fixes
- Coordination tasks, workflow orchestration
- Final integration of specialist work

### Tier 2: Delegate to Implementation Agents (5-30 min, straightforward)

**python-dev** (backend):
- Implement FastAPI routes following established patterns
- Write tests for new functionality
- Refactor single files following code style
- Implement business logic
- Bug fixes with clear root cause
- Add fields to SQLAlchemy models

**frontend-dev** (frontend):
- Create/modify Jinja2 templates
- HTMX interactions and event handling
- Tailwind CSS and daisyUI styling
- JavaScript for state management and DOM manipulation
- Template structure matching VaWW patterns

**Critical Boundaries** - Implementation agents ESCALATE when:
- Architectural decisions needed -> architect
- Test strategy questions -> test-runner
- Complex optimization required -> performance-optimizer
- Mysterious bugs -> debugger

### Tier 3: Delegate to Specialist Agents (requires expertise)

| Agent | Domain | When to Delegate |
|-------|--------|------------------|
| architect | System design | ADRs, architectural decisions, new patterns |
| test-runner | Testing | TDD enforcement, test strategy, infrastructure |
| debugger | Investigation | Complex bugs, mysterious failures, profiling |
| code-reviewer | Quality | Standards enforcement, quality review, type hints |
| api-documenter | API documentation | OpenAPI specs, REST API design, documentation |
| documenter | Documentation | CHANGELOG, doc structure maintenance |
| vc-manager | Version control | GitHub issues, PRs, branches, merge workflow |
| performance-optimizer | Performance | Database queries, N+1 detection, caching |

---

## Decision Flowchart

```
Task Assessment:

1. Trivial (<5 min)?
   YES --> Do it yourself
   NO  --> Continue

2. Straightforward backend implementation?
   YES --> python-dev agent
   NO  --> Continue

3. Frontend/template work?
   YES --> frontend-dev agent
   NO  --> Continue

4. Requires design/analysis/expertise?
   YES --> Select specialist agent(s)

5. Overlapping concerns (multiple domains)?
   YES --> Multi-agent approval workflow (see /approve command)
```

---

## Handoff Protocol

When delegating, provide these FOUR elements:

### 1. Compressed Context (summary, not full history)

```
"Working on [feature]. Database models in source/database/models.py.
VaWW compatibility relevant for templates."
```

### 2. Specific Task Scope (clear boundaries)

```
"[SPECIFIC_ACTION]. Include [EDGE_CASES]."
```

### 3. Success Criteria

```
"[SUCCESS_CONDITION]. Use [PATTERNS_TO_FOLLOW].
Follow existing patterns in [EXAMPLE_LOCATION]."
```

### 4. Expected Return Format

```
"Return [DELIVERABLES] and confirmation [VERIFICATION_STEPS]."
```

---

## Agent-Specific Delegation Templates

### python-dev Agent

```markdown
## Delegation to python-dev

**Context:** Working on [feature]. Database models in source/database/models.py.

**Task:** Implement [specific functionality] following FastAPI patterns.

**Success Criteria:**
- Implementation complete following patterns
- Type hints and docstrings added
- Tests written and passing
- Code formatted (make format) and lint passing (make lint)
- Any uncertainties escalated to specialists

**Return:** What you implemented, tests added, specialists consulted (if any), remaining concerns.
```

### frontend-dev Agent

```markdown
## Delegation to frontend-dev

**Context:** Working on [feature]. VaWW template compatibility required.

**Task:** Create/modify [templates/components] following VaWW patterns.

**Success Criteria:**
- Templates match VaWW naming convention (_browser_, _detail_, _new_)
- HTMX interactions work correctly
- Tailwind/daisyUI styling consistent
- HX-Trigger headers used appropriately
- Consult docs/UI_DESIGN.md for guidelines

**Return:** Template files created/modified, HTMX patterns used, any VaWW compatibility notes.
```

### architect Agent

```markdown
## Delegation to architect

**Context:** [Current architecture state], [constraints], VaWW compatibility needs.

**Task:** [Specific design problem or ADR topic].

**Success Criteria:**
- Design documented with rationale
- Alternatives analyzed with pros/cons
- VaWW addon integration considered
- Impact on existing structure assessed

**Return:** ADR draft or design recommendations, alternatives considered, consequences identified.
```

### test-runner Agent

```markdown
## Delegation to test-runner

**Context:** [Feature requirements], [acceptance criteria].

**Task:** Create failing tests for [functionality]. Include [edge cases].

**Success Criteria:**
- Tests fail appropriately (not syntax errors)
- Edge cases and error conditions covered
- Follow existing test patterns in tests/
- Use Factory Boy for test data

**Return:** Test file paths, confirmation tests fail with expected messages.
```

### code-reviewer Agent

```markdown
## Delegation to code-reviewer

**Context:** [Files changed], [modification scope], [quality aspects to check].

**Task:** Review [quality aspects] for recent changes.

**Success Criteria:**
- Quality standards verified
- Type hint completeness verified
- VaWW compatibility checked
- Issues identified with specific locations
- Approval status clear

**Return:** Quality assessment, improvement recommendations, approval/rejection with rationale.
```

### vc-manager Agent

```markdown
## Delegation to vc-manager

**Context:** [Branch name], [issue details], [commit scope].

**Task:** [Specific VC operation - branch/issue/PR/merge].

**Success Criteria:**
- Clean VC state
- Issue properly linked
- Proper commit message format

**Return:** [Branch created / Issue number / PR URL / Merge confirmation].
```

---

## Escalation Patterns

Implementation agents should escalate when encountering work outside scope:

### Escalation Phrase Pattern

```
"I need [SPECIALIST] agent to [ACTION] before I [CONTINUE_WORK]."
```

### Common Escalation Triggers

**From python-dev/frontend-dev to:**

| Escalate To | When |
|-------------|------|
| architect | "Should this be a new service or extend existing?", design decisions |
| test-runner | "How should I structure these integration tests?" |
| debugger | "Can't figure out why this is failing", mysterious bugs |
| performance-optimizer | "This query is slow", N+1 detected |

---

## Agent Coordination Patterns

### Sequential Pipeline (Feature Development)

```
architect (design)
  --> test-runner (failing tests)
  --> python-dev (backend)
  --> frontend-dev (templates)
  --> code-reviewer (quality)
  --> documenter (docs)
  --> vc-manager (merge)
```

### Frontend-Only Pipeline

```
architect (if new pattern)
  --> frontend-dev (implement)
  --> code-reviewer (quality)
```

### Parallel Coordination (Independent Work)

```
Simultaneous specialist work on independent aspects:
performance-optimizer (analyze bottlenecks)
+ api-documenter (document APIs)
+ documenter (update CHANGELOG)
```

---

## Memory Updates After Delegation

Update `.claude/memory/current-session.md` with:

```markdown
## Delegation: [Agent Name]

**Task:** [Task description]
**Status:** [pending|in-progress|completed|blocked]

**What was accomplished:**
- [Outcome 1]
- [Outcome 2]

**Key decisions made:**
- [Decision 1]

**What's next:**
- [Next step]

**Blockers/concerns:**
- [Any blockers]
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Ambiguous task | Ask for clarification before delegating |
| No matching agent | Default to python-dev or frontend-dev with full context |
| Missing context | Gather available context, note gaps for agent |
| Agent escalates back | Route to appropriate specialist, provide additional context |
| Multi-domain task | Identify primary domain, note secondary concerns |
