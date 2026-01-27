# Verk Bookkeeping Quality Control

This rule defines the quality control processes, multi-agent review patterns, and enforcement mechanisms for Verk Bookkeeping development.

## Multi-Agent Review Process

### Review Agent Configuration

The code-reviewer agent ensures quality standards before merge.

**When to Delegate to code-reviewer Automatically**:

- Refactor cycle completion (review quality improvements)
- Before committing significant changes
- Quality standards enforcement needed
- Type hint verification (Python type hints)
- Code style adherence check

**Explicit Commands**:

- "Use code-reviewer to analyze recent changes"
- "Have code-reviewer verify quality standards"
- "code-reviewer should check type hints completeness"

**Handoff Requirements**:

- Context: Files changed, modification scope
- Task: Review specific quality aspects
- Success criteria: Quality standards met, issues identified

**Expected Output**: Quality assessment, improvement recommendations, approval status

**Integration**: code-reviewer identifies issues, primary or python-dev/frontend-dev fixes

---

## Multi-Agent Approval Workflows

### When to Require Multi-Agent Approval

**Database Schema Changes**:

1. **architect**: Design tables, relationships, indexes, business rules
2. **performance-optimizer**: Review query patterns, index strategy, N+1 prevention
3. **api-documenter**: Document data models, API impact
4. **Primary coordinates**: Get architect + performance-optimizer approval before implementation
5. **python-dev**: Implement after approvals

**New API Endpoints**:

1. **architect**: Endpoint design, REST conventions, Pydantic schemas
2. **api-documenter**: OpenAPI specs, documentation structure
3. **performance-optimizer**: Review if database-heavy operations
4. **Primary coordinates**: Get architect approval, performance review if needed
5. **python-dev**: Implement endpoint + tests
6. **Multi-agent review**: api-documenter (docs), code-reviewer (quality)

**Critical Refactoring** (Files >600 LOC, multi-file changes):

1. **architect**: Structural design strategy, new patterns (if needed)
2. **test-runner**: Test preservation/migration strategy
3. **Primary coordinates**: Get multi-agent design approval
4. **python-dev/frontend-dev**: Implement refactoring
5. **Multi-agent review**: code-reviewer (quality), test-runner (coverage)

---

## Quality Gates

### Code Quality Checklist

**Code Structure**:

- Simplicity and readability (focus on maintainability)
- No code duplication or unnecessary complexity
- Proper separation of concerns
- File/Module separation:
  - Priority one: one concern per file
  - Priority two: aim for 200-400 lines
  - Hard limit: 600+ LOC flags for splitting (create GitHub issue if violated)
- Integration with existing patterns

**Type Safety & Documentation**:

- All functions have proper type hints (mandatory)
- Comprehensive docstrings for new/modified functions and classes
- Comments explain WHY, not WHAT
- No references to non-existent code or issues
- Code is self-documenting through clear naming

**Verk Bookkeeping-Specific Standards**:

- Absolute imports from `source/`: `from source.api.app import app`
- Consistent with existing patterns in codebase
- VaWW template compatibility maintained
- No temporary tests outside `tests/` directory

**Security & Performance**:

- No exposed secrets or credentials
- Input validation and error handling
- Performance implications of changes
- Memory usage considerations
- SQL injection prevention (use SQLAlchemy ORM)
- File system operations are safe

**Testing Quality**:

- Tests exist for new functionality (80%+ coverage target)
- Tests are meaningful, not just achieving coverage percentage
- Tests verify behavior, not implementation details
- Edge cases and error conditions tested
- Mocks are appropriate and focused
- Tests follow TDD RED-GREEN-REFACTOR pattern

---

## TDD Enforcement (test-runner Agent)

### TDD Enforcement Rules

1. **REFUSE** to write implementation code without failing tests first
2. Tests must fail for the RIGHT reasons (not syntax errors)
3. Use pytest framework as specified in project documentation
4. Follow existing test patterns in `tests/` directory
5. Use Factory Boy for test data generation
6. Keep tests in `tests/` directory (never create temporary tests elsewhere)

### RED-GREEN-REFACTOR Process

**RED Phase** (test-runner Primary Responsibility):

- **test-runner agent (preferred)**: Creates failing tests, refuses implementation
- **Primary agent fallback**: Explicit focus on test-first methodology
- Start by listing test scenarios for the new feature/fix
- Write specific failing tests that define expected behavior
- Run tests to confirm they fail for expected reasons
- Write tests for edge cases, error conditions, and boundary values
- Focus on one small, testable unit at a time
- NO IMPLEMENTATION CODE IN RED PHASE

**GREEN Phase** (Coordination):

- **Primary agent or python-dev**: Implements minimal passing code
- Write simplest code that makes the failing test pass
- Don't worry about elegance - focus only on making tests pass
- Run specific tests to ensure new code passes
- Hard-coding and inelegant solutions are acceptable at this stage
- No code should be added beyond tested functionality

**REFACTOR Phase** (Validation):

- **code-reviewer agent (preferred)**: Quality-focused refactoring
- **Primary agent fallback**: Explicit attention to code quality standards
- Clean up implementation code for readability and maintainability
- Remove code duplication and apply design patterns
- Follow CODING_STYLE_GUIDE.md strictly and mimic existing code style
- Improve naming conventions and add proper type hints
- Run tests after each refactor to ensure no functionality is broken

### Refusal Protocol

If implementation code is attempted without failing tests:

1. **STOP** the process immediately
2. Point out the TDD violation
3. Request RED phase tests first
4. Refuse to proceed until tests are written and failing correctly

---

## Review Output Format

### Critical Issues (Must Fix Before Merge)

- Security vulnerabilities
- Breaking changes to existing functionality
- Code that violates mandatory Verk Bookkeeping standards
- Missing tests for new functionality
- Type hint violations
- Import convention violations
- VaWW compatibility violations

### Warnings (Should Address)

- Style inconsistencies
- Performance concerns
- Maintainability issues
- Documentation gaps
- Potential architectural drift
- Code duplication
- Complex functions that should be split

### Suggestions (Nice-to-Have)

- Code organization improvements
- Additional test cases
- Performance optimizations
- Documentation enhancements
- Refactoring opportunities
- Better naming conventions

---

## Quality Commands

### Code Quality

- Check style: `make lint`
- Format code: `make format`
- Type check: `mypy source/`

### Testing

- Run all tests: `make test` (WARNING: verbose output, prefer specific tests)
- Run specific tests: `uv run pytest tests/path/to/test.py`
- Check coverage: `uv run pytest --cov=source tests/`
- Coverage report: `uv run pytest --cov-report=html tests/`

---

## Agent Integration for Quality

### code-reviewer Integration

- With **architect**: Validates implementation matches architectural decisions
- With **test-runner**: Validates test quality and meaningfulness
- With **documenter**: Checks code documentation quality
- With **vc-manager**: Focuses on code quality while vc-manager handles git operations

### test-runner Integration

- With **architect**: Ensures architecture supports isolated component testing
- With **code-reviewer**: Test-runner ensures tests exist, code-reviewer validates quality
- With **documenter**: Maintains testing documentation
- With **vc-manager**: Links test improvements to GitHub issues

---

## Enforcement

### Blocking Conditions

Changes are **blocked** if any of the following occur:

- Any quality gate fails
- Performance review identifies unresolved query issues
- Code review surfaces unaddressed concerns
- Multi-agent approval not obtained for critical changes
- Human maintainer has not approved (for merge to main)
- VaWW compatibility broken

### Exception Process

To bypass a quality gate (emergency situations only):

1. Document the reason for bypass
2. Obtain explicit human/user approval
3. Create a follow-up task to address the bypassed check
4. Set a deadline for remediation

### Audit Trail

All quality control decisions should be logged in memory files:

- Who reviewed what and when
- Gate pass/fail results
- Any exceptions granted and their justification
- Final approval timestamp and approver
