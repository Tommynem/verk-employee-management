# Quality Gates Approval Checklist

Checklist items extracted from code-reviewer, test-runner, and multi-agent approval protocols.

---

## Pre-Review Verification

Before starting detailed review, verify:

- [ ] PR/Change has clear description and linked issue
- [ ] Branch is up to date with target branch
- [ ] CI pipeline passing (or failures explained)
- [ ] Changes are focused and atomic (not mixing concerns)

---

## Code Structure Review (code-reviewer)

### Critical - Must Fix Before Merge

- [ ] **Simplicity and readability** - Code follows project philosophy
- [ ] **No code duplication** or unnecessary complexity
- [ ] **Proper separation of concerns** - Single responsibility per file
- [ ] **Integration with existing architecture** patterns maintained
- [ ] **Clear subsystem boundaries** respected

### File/Module Standards

- [ ] **Priority one**: One concern per file
- [ ] **Priority two**: Aim for 200-400 lines per file
- [ ] **Hard limit**: 600+ LOC flags for splitting (create GitHub issue if violated)

### Violations That Block Merge

- [ ] Security vulnerabilities
- [ ] Breaking changes to existing functionality
- [ ] Code violating mandatory project standards
- [ ] Missing tests for new functionality
- [ ] Type hint violations
- [ ] Import convention violations

---

## Type Safety and Documentation (code-reviewer)

### Type Safety

- [ ] All functions have proper type hints (mandatory)
- [ ] No `any` types without explicit justification
- [ ] All function parameters annotated
- [ ] All return types annotated

### Documentation Quality

- [ ] Comprehensive docstrings for new/modified functions and classes
- [ ] Docstrings follow consistent style (Google or NumPy)
- [ ] Comments explain WHY, not WHAT
- [ ] No references to non-existent code or issues
- [ ] Code is self-documenting through clear naming

---

## Security Review ({{SECURITY_AGENT}})

### Authentication and Authorization

- [ ] No exposed secrets or credentials
- [ ] No hardcoded passwords, API keys
- [ ] Proper authentication checks in place
- [ ] Authorization verified before sensitive operations

### Data Handling

- [ ] Input validation implemented for all user input
- [ ] SQL injection prevention (parameterized queries used)
- [ ] File system operations are safe
- [ ] Path traversal prevented (file paths validated)

### Performance and Memory

- [ ] Performance implications considered
- [ ] Memory usage appropriate
- [ ] No N+1 query patterns
- [ ] No memory leaks introduced

---

## TDD Compliance (test-runner)

### RED Phase Verification

- [ ] Tests written BEFORE implementation code
- [ ] Tests fail for expected reasons (not syntax errors)
- [ ] Test scenarios cover: happy path, edge cases, errors, validation

### GREEN Phase Verification

- [ ] Minimal code written to pass tests (hard-coding acceptable)
- [ ] Only tested functionality added
- [ ] Existing patterns followed (entity_manager, entity_creator, etc.)

### REFACTOR Phase Verification

- [ ] Duplication removed, methods extracted
- [ ] Code style guide followed
- [ ] Comprehensive documentation added
- [ ] Debug artifacts tagged: `# artifact`

### Coverage Requirements

- [ ] 80%+ coverage for new/modified code
- [ ] Aim for 90%+ to compensate for resistant areas
- [ ] Tests are meaningful (not just coverage metrics)
- [ ] Tests verify behavior, not implementation details

### Test Quality

- [ ] Tests exist for new functionality
- [ ] Edge cases and error conditions tested
- [ ] Mocks are appropriate and focused
- [ ] Tests follow TDD RED-GREEN-REFACTOR pattern
- [ ] Integration tests for cross-component changes

---

## Project-Specific Standards

### Import Conventions

- [ ] Absolute imports from top-level: `from source.{{MODULE}}.{{SUBMODULE}} import xyz`
- [ ] Consistent with existing patterns in codebase

### Framework Integration

- [ ] Proper integration with project's entity/data management system
- [ ] No temporary tests outside `tests/` directory
- [ ] Framework-specific patterns followed (DPG, Gin, SvelteKit, etc.)
- [ ] Database operations use established patterns
- [ ] Validation follows subsystem conventions

---

## Documentation Updates (documenter)

### CHANGELOG

- [ ] CHANGELOG.md `[Unreleased]` section updated
- [ ] Correct category used: Added, Changed, Fixed, Deprecated, Removed, Security
- [ ] Format followed: `- [Subsystem] Brief description (#issue-number)`

### Project Index

- [ ] {{PROJECT_INDEX}} updated if files added/moved/removed

### ADR Management

- [ ] ADR created if significant architectural decision
- [ ] ADR format compliant (documenter approved)
- [ ] ADR status updated (Proposed -> Accepted) if applicable

---

## Pre-Merge Final Checks (code-reviewer + Primary)

### Cleanup

- [ ] All debug artifacts removed (`# artifact` tags, print statements)
- [ ] No commented-out code (unless justified)
- [ ] No debug statements left in code

### Quality Verification

- [ ] `{{FORMAT_COMMAND}}` passes
- [ ] `{{LINT_COMMAND}}` passes
- [ ] Tests still passing after cleanup
- [ ] `{{QUALITY_COMPARE_COMMAND}}` shows improvement or maintenance

### HALT Points Cleared

- [ ] Phase 2 Course Correction - User approved approach
- [ ] Phase 7 User Testing - User verified functionality

---

## Multi-Agent Approval Status

### For Changes Requiring Multi-Agent Approval

Track approval status for each required reviewer:

| Agent | Status | Notes |
|-------|--------|-------|
| architect | [ ] Approved / [ ] Concerns | |
| {{PERFORMANCE_AGENT}} | [ ] Approved / [ ] Concerns | |
| {{SECURITY_AGENT}} | [ ] Approved / [ ] Concerns | |
| code-reviewer | [ ] Approved / [ ] Concerns | |
| api-documenter | [ ] Approved / [ ] Concerns | |
| test-runner | [ ] Approved / [ ] Concerns | |

### Approval Required For

| Change Type | Required Approvers |
|-------------|-------------------|
| Database Schema Changes | architect, {{PERFORMANCE_AGENT}}, api-documenter |
| New API Endpoints | architect, api-documenter, {{SECURITY_AGENT}} |
| Critical Refactoring (>600 LOC) | architect, refactor-specialist, test-runner |
| Security Features | {{SECURITY_AGENT}}, architect, code-reviewer |
| New Architectural Patterns | architect, code-reviewer, test-runner + ADR |

---

## Final Signoff

### Gate Summary

| Gate | Status | Reviewer |
|------|--------|----------|
| Pre-Implementation | [ ] Pass / [ ] Fail | |
| Test Coverage | [ ] Pass / [ ] Fail | |
| Code Quality | [ ] Pass / [ ] Fail | |
| Security Review | [ ] Pass / [ ] Fail | |
| Documentation | [ ] Pass / [ ] Fail | |
| Pre-Merge Check | [ ] Pass / [ ] Fail | |

### Approval Decision

- [ ] **APPROVED** - All gates pass, ready to merge
- [ ] **APPROVED WITH CONDITIONS** - Can merge after conditions met
- [ ] **CHANGES REQUESTED** - Must address feedback before re-review
- [ ] **BLOCKED** - Critical issues, cannot proceed

### Reviewer Signoff

```
Decision: [APPROVED / CHANGES REQUESTED / BLOCKED]
Reviewer: ________________________
Date: ________________________
Gates Verified: All / [List specific gates]
Comments:

```

---

## Escalation Quick Reference

| Failure Type | Action |
|--------------|--------|
| Test Coverage | Return to TDD cycle, test-runner creates tests |
| Code Quality | code-reviewer documents, delegate to refactor-specialist if structural |
| Security | HALT immediately, {{SECURITY_AGENT}} documents, mandatory fix |
| Architectural | Return to Course Correction, architect re-evaluates, ADR update |
| Multi-Agent Disagreement | Primary synthesizes, escalate to user, document in ADR |

---

## Placeholders Reference

| Placeholder | Description |
|-------------|-------------|
| `{{SECURITY_AGENT}}` | Security review agent (security-specialist or code-reviewer) |
| `{{PERFORMANCE_AGENT}}` | Performance review agent (performance-optimizer or debugger) |
| `{{PROJECT_INDEX}}` | Project file index (PROJECT_INDEX.md) |
| `{{FORMAT_COMMAND}}` | Format command (make format) |
| `{{LINT_COMMAND}}` | Lint command (make lint) |
| `{{QUALITY_COMPARE_COMMAND}}` | Quality comparison (make quality-compare) |
| `{{MODULE}}` | Project module path component |
| `{{SUBMODULE}}` | Project submodule path component |
