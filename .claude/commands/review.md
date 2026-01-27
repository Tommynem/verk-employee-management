# /review

Multi-agent code review command that orchestrates quality, performance, and architecture analysis for Verk Bookkeeping changes.

## Description

This command runs a comprehensive code review workflow using multiple specialized agents in a coordinated review chain. It ensures thorough coverage through structured review phases with clear approval gates.

## Usage

```
/review [scope] [--pattern=<pattern>]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `files` | Space-separated list of file paths to review |
| `staged` | Review all currently staged git changes |
| `branch` | Review all changes on current branch vs main |
| _(none)_ | Review all uncommitted changes (staged + unstaged) |

### Pattern Options

| Pattern | Description | Use When |
|---------|-------------|----------|
| `--pattern=sequential` | Reviews happen one after another | Default, most thorough |
| `--pattern=roundrobin` | All reviewers cycle systematically | Database/schema changes |
| `--pattern=parallel` | Independent reviews run simultaneously | Time-sensitive, non-overlapping concerns |

### Examples

```bash
# Review specific files
/review source/api/routers/invoices.py templates/partials/_detail_invoice.html

# Review staged changes only
/review staged

# Review branch changes with round-robin pattern (all specialists review)
/review branch --pattern=roundrobin

# Review all uncommitted changes
/review
```

## Multi-Agent Review Chain

### Phase 1: Identify Review Scope

Collect changes and determine which review agents are needed:

```bash
# Gather the diff based on scope
git diff [--cached | HEAD | origin/main...]

# Analyze changed files to determine required reviewers
# Triggers:
#   - Database models (models.py) -> performance-optimizer + architect
#   - API routes (routers/) -> code-reviewer + api-documenter
#   - Templates (templates/) -> code-reviewer + frontend-dev
#   - Test files -> test-runner
```

### Phase 2: Code Quality Review

**Agent:** `code-reviewer`

**Review Checklist:**

#### Code Structure
- [ ] Simplicity and readability
- [ ] No code duplication or unnecessary complexity
- [ ] Proper separation of concerns
- [ ] File/module size within limits (600 LOC hard limit)
- [ ] Integration with existing FastAPI patterns

#### Type Safety & Documentation
- [ ] All functions have proper type annotations
- [ ] Comprehensive docstrings for new/modified functions
- [ ] Comments explain WHY, not WHAT
- [ ] Code is self-documenting through clear naming

#### Verk Bookkeeping Standards
- Use absolute imports from top-level: `from source.api.app import app`
- All functions require type hints
- Comprehensive docstrings for all new/modified functions
- VaWW template compatibility maintained
- No TODO comments without linked GitHub issues

**Quality Verification Commands:**

```bash
# Run linting
make lint

# Run type checking
mypy source/

# Run tests
make test
```

**Output Format:**

```markdown
### Critical Issues (Must Fix Before Merge)
- Type annotation violations
- Missing tests for new functionality
- Breaking changes to existing functionality
- VaWW compatibility violations

### Warnings (Should Address)
- Style inconsistencies
- Performance concerns
- Maintainability issues
- Documentation gaps

### Suggestions (Nice-to-Have)
- Code organization improvements
- Additional test cases
- Refactoring opportunities
```

### Phase 3: Architecture Review (Conditional)

**Agent:** `architect`

Invoked for significant structural changes.

**Trigger Conditions:**
- New modules or subsystems created
- Changes to core domain models (models.py)
- Changes to API route structure
- Changes spanning multiple layers
- VaWW compatibility concerns

**Architecture Focus:**
- [ ] Architectural boundaries maintained
- [ ] FastAPI patterns followed correctly
- [ ] VaWW addon compatibility preserved
- [ ] Integration patterns consistent
- [ ] ADR required for significant decisions

### Phase 4: Performance Review (Conditional)

**Agent:** `performance-optimizer`

Invoked when changes touch performance-sensitive areas.

**Trigger Conditions:**
- Database queries or SQLAlchemy model changes
- Large data operations
- New API endpoints with database operations
- Loops processing collections

**Performance Focus:**
- [ ] No N+1 query patterns
- [ ] Appropriate indexes recommended for new columns
- [ ] Efficient SQLAlchemy relationship loading (joinedload where needed)
- [ ] Caching strategies for repeated queries

### Phase 5: VaWW Compatibility Check

**Automatic check for template/UI changes:**

```
VaWW Compatibility Policy:
- Templates MUST match VaWW patterns for future addon integration
- Same naming conventions (_browser_, _detail_, _new_)
- Same HTMX patterns (HX-Trigger headers)
- Same Pydantic schema inheritance (Update -> Create -> Response)
```

**Review template changes for:**
- [ ] Naming convention followed?
- [ ] HTMX patterns match VaWW?
- [ ] daisyUI components consistent?
- [ ] Route patterns match VaWW?

### Phase 6: Collect and Summarize

Aggregate results from all review agents:

```markdown
## Review Summary

### Overview
- **Files Reviewed:** {count}
- **Review Chain:** {agents invoked}
- **Total Findings:** {count}
- **Severity Breakdown:** Critical: {n} | High: {n} | Medium: {n} | Low: {n}

### Code Quality Findings
{findings from code-reviewer}

### Architecture Review Findings
{findings from architect, if invoked}

### Performance Review Findings
{findings from performance-optimizer, if invoked}

### VaWW Compatibility
{compliance status}

### Approval Status
- **Code Quality:** [APPROVED/BLOCKED]
- **Architecture:** [APPROVED/BLOCKED/NOT_REQUIRED]
- **Performance:** [APPROVED/BLOCKED/NOT_REQUIRED]

### Final Verdict
[APPROVED FOR MERGE / CHANGES REQUIRED / BLOCKED]

### Priority Action Items
1. [Most critical fix needed]
2. [Second priority]
3. ...
```

## Review Patterns

### Sequential Pattern (Default)

Standard review chain where each agent reviews in order:

```
code-reviewer
  -> (if architecture-sensitive) architect
  -> (if performance-sensitive) performance-optimizer
  -> Summary
```

**Best for:** Most reviews, thorough analysis, clear handoffs

### RoundRobin Pattern

All specified reviewers examine changes in fixed order, cycling until consensus:

```
Cycle 1:
  code-reviewer -> architect -> performance-optimizer
Cycle 2 (if issues raised):
  code-reviewer (verify fixes) -> architect (verify) -> performance-optimizer (verify)
Termination: All approve OR max cycles (2) reached
```

**Best for:**
- Database schema changes
- Cross-cutting architectural changes

### Parallel Pattern

Independent reviews run simultaneously (when concerns don't overlap):

```
[code-reviewer] + [api-documenter] + [documenter]
  -> Merge findings -> Summary
```

**Best for:**
- Time-sensitive reviews
- Non-overlapping review domains

## Verk Bookkeeping Review Triggers

### Database Schema Changes (models.py)

**Required Reviewers:** code-reviewer, architect, performance-optimizer, api-documenter

**Checklist:**
- [ ] SQLAlchemy model follows existing patterns
- [ ] Relationships defined correctly (foreign keys, backrefs)
- [ ] Indexes recommended for query patterns
- [ ] API documentation updated for REST schema alignment
- [ ] Migration strategy clear

### API Route Changes (source/api/routers/)

**Required Reviewers:** code-reviewer, api-documenter

**Checklist:**
- [ ] Route patterns follow VaWW convention
- [ ] Pydantic schemas follow inheritance pattern
- [ ] Type hints complete
- [ ] HTMX response patterns correct

### Template Changes (templates/)

**Required Reviewers:** code-reviewer

**Checklist:**
- [ ] VaWW naming convention followed
- [ ] HTMX patterns correct
- [ ] daisyUI components consistent
- [ ] HX-Trigger headers used appropriately

## Multi-Agent Approval Protocol

For critical changes requiring multi-agent signoff:

### When Required

- **Database Schema Changes**: code-reviewer + architect + performance-optimizer
- **New API Endpoints**: code-reviewer + architect + api-documenter
- **Critical Refactoring**: code-reviewer + architect + test-runner

### Approval Gate

A change is approved for merge when:
1. **Code Quality**: code-reviewer approves (no critical/high issues)
2. **Architecture**: architect approves (if invoked)
3. **Performance**: performance-optimizer approves (if invoked)
4. **VaWW Compatibility**: Template changes follow conventions

If ANY reviewer BLOCKS, the change cannot merge until issues are resolved.

## Configuration

### Thresholds

| Threshold | Value |
|-----------|-------|
| Max file LOC | 600 |
| Max review cycles (RoundRobin) | 2 |
| Test coverage target | 80% |

## Output

The command produces:

1. **Detailed Findings** - Issues categorized by severity and type
2. **Inline Annotations** - Specific file:line references for each finding
3. **Summary Report** - Aggregated findings with approval status
4. **Exit Code** - Non-zero if any reviewer BLOCKS the change
