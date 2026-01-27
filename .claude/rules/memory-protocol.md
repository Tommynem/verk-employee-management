# Verk Bookkeeping Memory System Protocol

This rule defines the persistent memory system for maintaining context across agent sessions, tracking decisions, and enabling clean agent handoffs.

## Memory File Structure

All memory files live in `.claude/memory/`.

### Core Memory Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `current-session.md` | Active session state, work tracking | Every session, during work |
| `decisions.md` | Architectural decisions, references to ADRs | When decisions made |
| `agent-performance.md` | Agent effectiveness tracking | Monthly review |
| `groupchat-sessions.md` | Multi-agent conversation logs | Per GroupChat session |

### Optional Memory Files

Create additional memory files for specialized tracking when patterns emerge:
- `technical-debt.md` - Track known issues, future improvements
- `vaww-compatibility.md` - VaWW addon integration tracking

---

## Session Lifecycle

### Session Start Protocol

1. **Check system time**: `date +"%Y-%m-%d"` (NEVER guess or assume current date)
2. **Read current-session.md** to restore context
3. **Update date** with accurate date from step 1
4. **Review** recent decisions and active work
5. **Note** which agents will be active this session

### During Development

1. **Update "Active Work"** section through workflow phases
2. **Document key decisions** (reference ADRs, don't duplicate content)
3. **Trigger documenter** for significant architectural decisions
4. **Update quality gates** status as work progresses
5. **Record agent handovers** when delegating work

### Session End Protocol

1. **Update session state** with final progress
2. **Record decisions** in decisions.md (reference ADRs for formal decisions)
3. **Note agent performance** observations
4. **Mark completed items** and update next steps
5. **Ensure clean handoff** state for next session

---

## current-session.md Format

```markdown
# Current Session State
**Date**: YYYY-MM-DD
**Branch**: feature/branch-name
**Active Agents**: python-dev, frontend-dev, test-runner
**Primary Focus**: Description of current work

## Session Context
### Recent Decisions
- **Decision Name**: Brief description
- Reference ADRs when applicable

### Active Work
- **In Progress**: Current task description
- **Status**: Phase/status (e.g., "TDD GREEN phase")
- **Completed This Session**:
  - Item 1
  - Item 2
- **Previous Session Completed**:
  - Previous completion

### Agent Handovers
(Document when work transfers between agents)
- **From**: Source agent
- **To**: Target agent
- **Context**: What was passed
- **Next Steps**: What target agent should do

### Quality Gates Status
- [ ] Tests passing (test-runner)
- [ ] Code review complete (code-reviewer)
- [ ] Documentation updated (documenter)
- [ ] Architecture validated (architect)
- [ ] Ready for VC (vc-manager)
```

---

## decisions.md Format

```markdown
# Architectural Decision Log

## Decision-N: Title
**Date**: YYYY-MM-DD
**Status**: Proposed/Approved/Superseded
**Context**: Why this decision needed
**Decision**: What was decided (or "See ADR-XXXX for complete documentation")
**Consequences**:
- Positive: Benefits
- Negative: Tradeoffs
- Neutral: Side effects
```

### Decision Tracking Guidelines

- Use this for informal decisions and agent coordination choices
- For formal architectural decisions, create full ADRs in `docs/adr/`
- Record agent workflow pattern evolution
- Document agent performance insights

---

## Agent Handover Protocol

When delegating work between agents, document in current-session.md:

1. **What current agent accomplished**
2. **Key decisions made** during the work
3. **What next agent needs** to continue
4. **Constraints or blockers** affecting the work

### Handover Context Structure

```markdown
### Agent Handover: architect to python-dev
**Completed**: Designed invoice endpoint schema with Pydantic models
**Decisions**: Using eager loading for invoice relationships
**Next Steps**: Implement endpoint following design in docs/
**Blockers**: None
**Quality Gates**: architect approved, awaiting implementation
```

---

## When to Update Memory

### Read Memory
- Session start (restore context)
- Resuming work after break
- Before making architectural decisions (check prior decisions)
- When coordinating with other agents

### Write Memory - Milestones
- Task completion (update Active Work section)
- Key decisions made (update decisions.md)
- Agent handover (document handover section)
- Quality gate changes (update status)
- Significant findings during investigation

### Write Memory - Session Events
- Session start (date, branch, focus)
- Session end (final progress, next steps)
- Task switches (update focus, preserve prior work context)

---

## Weekly Review (CRITICAL)

Perform weekly review to maintain memory quality:
- Review memory for bad patterns, flawed decisions
- Remove memorized design flaws, anti-patterns
- Ensure only valid architectural decisions and good practices
- Verify no code style flaws memorized
- Clean up stale entries

---

## Monthly Archival

1. Check date: `date +"%Y-%m-%d"`
2. Create archive directory: `.claude/memory/archive/YYYY-MM/`
3. Archive files:
   - `decisions.md`
   - `agent-performance.md`
   - `groupchat-sessions.md`
4. Create summary with 3-5 key decisions
5. Start fresh monthly files
6. Migrate significant decisions to formal ADRs in `docs/`

---

## Memory Hygiene Rules

1. **No duplication**: Reference ADRs and docs, don't copy content
2. **Accurate dates**: Always verify with system command
3. **Clean state**: Remove completed items after archival
4. **Concise entries**: Summary format, not verbose logs
5. **Actionable next steps**: Always include clear next actions
6. **Quality gates**: Maintain accurate status for workflow tracking

---

## Merge Readiness Checklist Pattern

For feature branches approaching merge:

```markdown
## MERGE READINESS CHECKLIST

### Blocking
- [ ] Backend compiles/builds successfully (`make lint`)
- [ ] Backend tests pass (`make test`)
- [ ] Type checking passes

### Quality
- [ ] All identified issues resolved
- [ ] VaWW compatibility maintained
- [ ] CHANGELOG updated
- [ ] Tests added for all fixes

### Ready
- [ ] Working tree clean
- [ ] All commits have proper messages
- [ ] No destructive operations pending
```
