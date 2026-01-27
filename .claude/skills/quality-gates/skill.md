# Quality Gates Skill

Quality gate definitions and multi-agent approval protocols for ensuring code quality, security, and architectural integrity before merge.

## Quick Reference: When Quality Gates Are Required

| Change Type | Required Reviewers | Approval Pattern |
|-------------|-------------------|------------------|
| Database Schema Changes | architect, {{PERFORMANCE_AGENT}}, api-documenter | RoundRobinPattern |
| New API Endpoints | architect, api-documenter, {{SECURITY_AGENT}} | DefaultPattern |
| Critical Refactoring (>600 LOC, multi-file) | architect, refactor-specialist, test-runner | RoundRobinPattern |
| Security Features | {{SECURITY_AGENT}}, architect, code-reviewer | RoundRobinPattern |
| New Architectural Patterns | architect, code-reviewer, test-runner, {{DX_AGENT}} | RoundRobinPattern + ADR |

## Quality Gate Definitions

### Gate 1: Pre-Implementation Approval

**When Required**:
- Significant architectural decisions
- Database schema changes
- New patterns or component designs
- Changes affecting multiple subsystems

**Approval Protocol**:
1. architect: Design tables, relationships, indexes, business rules
2. {{PERFORMANCE_AGENT}}: Review query patterns, index strategy, optimization
3. api-documenter: Document data models, prepare API schemas
4. {{DX_AGENT}}: Review module structure, import paths (if new package)
5. **Primary coordinates**: Get architect + {{PERFORMANCE_AGENT}} approval before implementation

**Output Required**: Documented design with multi-agent signoff

---

### Gate 2: Test Coverage Gate

**When Required**: All code changes to be merged

**Minimum Standards**:
- 80%+ coverage for new/modified code
- Aim for 90%+ to compensate for areas resistant to testing
- Tests must be meaningful, not just achieving coverage percentage
- Tests verify behavior, not implementation details

**TDD Enforcement** (test-runner agent):
- **REFUSE** to write implementation code without failing tests first
- Tests must fail for the RIGHT reasons (not syntax errors)
- Follow RED-GREEN-REFACTOR cycle strictly

**Checklist**:
- [ ] Failing tests written BEFORE implementation (RED phase)
- [ ] Tests pass after implementation (GREEN phase)
- [ ] Code refactored with tests still passing (REFACTOR phase)
- [ ] Edge cases and error conditions tested
- [ ] Integration tests for cross-component changes

---

### Gate 3: Code Quality Gate

**When Required**: All code changes before merge

**Code Review Standards** (code-reviewer agent):

**Critical Issues (Must Fix Before Merge)**:
- Security vulnerabilities
- Breaking changes to existing functionality
- Code violating mandatory {{PROJECT_NAME}} standards
- Missing tests for new functionality
- Type hint violations
- Import convention violations

**Warnings (Should Address)**:
- Style inconsistencies
- Performance concerns
- Maintainability issues
- Documentation gaps
- Potential architectural drift
- Code duplication
- Complex functions that should be split

**Quality Metrics**:
- File length: 200-400 lines ideal, 600+ requires GitHub issue for splitting
- Function length: Aim for <50 lines, flag >100 lines
- Cyclomatic complexity: Keep functions simple, split complex logic
- Nesting depth: Avoid >3 levels, extract functions

---

### Gate 4: Security Review Gate

**When Required**:
- Authentication/authorization features
- Handling sensitive user data
- Creating public-facing API endpoints
- Database access patterns
- File upload/download features
- Before merge to main (for security-sensitive features)

**Review Focus** ({{SECURITY_AGENT}} agent):
- No exposed secrets or credentials
- Input validation and error handling
- SQL injection prevention (use parameterized queries)
- File system operations are safe
- {{PROJECT_SPECIFIC_SECURITY_CONCERNS}}

**Checklist**:
- [ ] No hardcoded passwords, API keys, or secrets
- [ ] All user input validated and sanitized
- [ ] Parameterized queries used (no string concatenation)
- [ ] File paths validated, safe file operations
- [ ] Appropriate error handling (no information leakage)

---

### Gate 5: Documentation Gate

**When Required**: All features before merge

**Required Updates** (documenter agent):
1. CHANGELOG.md `[Unreleased]` section
   - Categories: Added, Changed, Fixed, Deprecated, Removed, Security
   - Format: `- [Subsystem] Brief description (#issue-number)`
2. {{PROJECT_INDEX}} if files added/moved/removed
3. API documentation (if endpoints changed)
4. ADR status update if applicable (Proposed -> Accepted)

**Checklist**:
- [ ] CHANGELOG updated with appropriate category
- [ ] {{PROJECT_INDEX}} reflects file changes
- [ ] Docstrings added for new/modified functions
- [ ] ADR finalized and approved (if applicable)

---

### Gate 6: Pre-Merge Quality Check

**When Required**: Final gate before merge to main

**Process** (code-reviewer + Primary):
1. Remove debug artifacts: `# artifact` tags, print statements, commented code
2. Run formatters and linters: `{{FORMAT_COMMAND}} && {{LINT_COMMAND}}`
3. Run tests on modified areas (verify cleanup did not break anything)
4. Quality comparison: `{{QUALITY_COMPARE_COMMAND}}` (should improve or maintain)
5. Verify all HALT points cleared (user approvals)

**Final Checklist**:
- [ ] All artifacts removed
- [ ] Format and lint passing
- [ ] Tests still passing
- [ ] Quality metrics improved/maintained
- [ ] User testing completed (HALT point cleared)
- [ ] Documentation complete

---

## Multi-Agent Approval Protocol

### Coordination Pattern

```
Primary (orchestrator):
  -> Identify overlapping concerns
  -> Spawn appropriate specialists
  -> Collect design approvals
  -> Coordinate implementation
  -> Gather review signoffs
  -> Integrate results
```

### Example Flow (Database Feature with API Impact)

```
1. Primary: "This needs database schema changes with API implications"
2. Primary -> architect: "Design schema for [feature]"
3. architect: Returns schema design with rationale
4. Primary -> {{PERFORMANCE_AGENT}}: "Review this schema for query performance"
5. {{PERFORMANCE_AGENT}}: Approves with index recommendations
6. Primary -> api-documenter: "Document API impact"
7. api-documenter: Documents data models and endpoint changes
8. Primary -> {{IMPLEMENTATION_AGENT}}: "Implement approved schema"
9. {{IMPLEMENTATION_AGENT}}: Implements, writes tests
10. Primary -> code-reviewer: "Review implementation quality"
11. code-reviewer: Approves
12. Primary: Integrates, coordinates vc-manager for merge
```

### When NOT to Require Multi-Agent Approval

- Simple, straightforward changes following established patterns
- Single-domain work clearly within one specialist's scope
- Urgent bug fixes (can get review after fix)
- Trivial changes (config, documentation fixes)

### Decision Guide

| Risk Level | Complexity | Impact | Approval Required |
|------------|------------|--------|-------------------|
| High (data loss, security, architectural) | Any | Any | Multi-agent approval |
| Any | High (multiple domains affected) | Any | Multi-agent approval |
| Any | Any | High (affects many systems/users) | Multi-agent approval |
| Low | Simple | Low | Single agent or {{IMPLEMENTATION_AGENT}} |

---

## GroupChat Approval Patterns

### RoundRobinPattern: Systematic Multi-Agent Review

**Use For**: Database schema changes, security reviews, critical refactoring

**How It Works**:
1. Primary defines participant list in specific order
2. Each agent speaks once (or until they signal "no concerns")
3. Cycle repeats if needed (max 2-3 cycles)
4. Terminates when all approve or issues raised

**Invocation Example**:
```
Primary: "Initiating RoundRobinPattern GroupChat for [change type]: [Description].
All participants must review. Order: architect, {{PERFORMANCE_AGENT}}, api-documenter.
Goal: Design approved by all. Max cycles: 2."
```

**Termination Conditions**:
- All agents approve (no concerns)
- Critical issues identified (halt for redesign)
- Max cycles completed (2-3)

### DefaultPattern: Explicit State Machine

**Use For**: API endpoint design, ADR creation workflows

**State Machine Example**:
```
START
  |
architect (design, request/response types, business logic)
  |
api-documenter (specs, documentation, examples)
  |
{{SECURITY_AGENT}} (security validation, recommendations)
  |
architect (incorporate feedback, final approval)
  |
DECISION (approved/needs-revision)
```

**Termination Conditions**:
- Reach DECISION state
- All required transitions complete
- Max turns reached (escalate to user)

---

## Recording and Tracking Approvals

### Session Tracking

Document in `.claude/memory/groupchat-sessions.md`:

```markdown
## Session: [Feature/Change Name]
**Date**: YYYY-MM-DD
**Pattern**: [RoundRobinPattern/DefaultPattern/AutoPattern]
**Participants**: [list agents]
**Goal**: [specific objective]

### Approval Status
- [ ] architect: [Approved/Concerns: X]
- [ ] {{PERFORMANCE_AGENT}}: [Approved/Concerns: X]
- [ ] code-reviewer: [Approved/Concerns: X]
- [ ] {{SECURITY_AGENT}}: [Approved/Concerns: X]

### Outcome
[Approved for implementation / Needs revision / Blocked]

### Key Decisions
- [Decision 1]
- [Decision 2]
```

### Quality Gates Status in Memory

Track in `.claude/memory/current-session.md`:

```markdown
## Quality Gates Status
Feature: [Name] (#issue)

| Gate | Status | Notes |
|------|--------|-------|
| Pre-Implementation | PASSED | architect + {{PERFORMANCE_AGENT}} approved |
| Test Coverage | PASSED | 85% coverage achieved |
| Code Quality | IN PROGRESS | code-reviewer reviewing |
| Security Review | PENDING | Awaiting {{SECURITY_AGENT}} |
| Documentation | PENDING | |
| Pre-Merge | PENDING | |
```

---

## Escalation Protocol

### When Gates Fail

1. **Test Coverage Failure**:
   - Return to TDD cycle (Phase 5)
   - test-runner creates additional failing tests
   - {{IMPLEMENTATION_AGENT}} implements to pass

2. **Code Quality Failure**:
   - code-reviewer documents issues
   - Delegate to refactor-specialist if structural
   - Re-review after fixes

3. **Security Failure**:
   - HALT immediately
   - {{SECURITY_AGENT}} documents vulnerabilities
   - Mandatory fix before proceeding
   - Re-review required

4. **Architectural Concerns**:
   - Return to Course Correction (Phase 2)
   - architect re-evaluates design
   - May require ADR update

5. **Multi-Agent Disagreement**:
   - Primary synthesizes concerns
   - Escalate to user for decision
   - Document resolution in ADR if significant

---

## Placeholders Reference

| Placeholder | Description | Example Values |
|-------------|-------------|----------------|
| `{{PROJECT_NAME}}` | Project name | VERK, VuWebsite |
| `{{PERFORMANCE_AGENT}}` | Performance review agent | performance-optimizer, debugger |
| `{{SECURITY_AGENT}}` | Security review agent | security-specialist, code-reviewer |
| `{{DX_AGENT}}` | Developer experience agent | dx-optimizer (optional) |
| `{{IMPLEMENTATION_AGENT}}` | Primary implementation agent | python-dev, go-dev, svelte-dev |
| `{{PROJECT_INDEX}}` | File index document | PROJECT_INDEX.md, INDEX.md |
| `{{FORMAT_COMMAND}}` | Code formatting command | make format |
| `{{LINT_COMMAND}}` | Linting command | make lint |
| `{{QUALITY_COMPARE_COMMAND}}` | Quality comparison command | make quality-compare |
| `{{PROJECT_SPECIFIC_SECURITY_CONCERNS}}` | Project-specific security items | OWASP Top 10, DPG freeze |
