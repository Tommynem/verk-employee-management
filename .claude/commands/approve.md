# /approve Command - Multi-Agent Approval Workflow

Execute a multi-agent approval workflow for critical Verk Bookkeeping changes requiring coordinated signoff.

## When to Use This Command

**Triggers** (automatically invoke `/approve` when):
- Database schema changes (models.py, SQLAlchemy models)
- New API endpoints (FastAPI routes)
- Critical refactoring (files >600 LOC, multi-file changes)
- Changes to core patterns (Pydantic schemas, route structure)
- New architectural patterns (major changes requiring ADR)
- High Risk changes (data loss potential, architectural impact)
- High Complexity changes (multiple domains affected)
- High Impact changes (affects core business logic)

**Skip Approval When**:
- Simple, straightforward changes following established patterns
- Single-domain work clearly within one specialist's scope
- Urgent bug fixes (can get review after fix)
- Trivial changes (config, documentation fixes)
- Low Risk + Simple changes

## Approval Chain by Change Type

### Database Schema Changes (models.py)

```
Approval Chain:
1. architect              -> Design tables, relationships, indexes, business rules
2. performance-optimizer  -> Review query patterns, index strategy, N+1 prevention
3. api-documenter         -> Document data models, prepare REST schemas
4. Primary coordinates    -> Get architect + performance-optimizer approval before implementation
5. python-dev             -> Implement after approvals
```

**Quality Gates**:
- [ ] SQLAlchemy model follows existing patterns
- [ ] Relationships and foreign keys validated
- [ ] Indexes identified for new columns
- [ ] API impact documented (REST schema alignment)
- [ ] Migration strategy clear
- [ ] All specialists approved (no blocking concerns)

### New API Endpoints (FastAPI Routes)

```
Approval Chain:
1. architect              -> Endpoint design, REST conventions, Pydantic schemas
2. api-documenter         -> OpenAPI specs, documentation structure
3. performance-optimizer  -> Review if database-heavy operations, caching strategy
4. Primary coordinates    -> Get architect approval
5. python-dev             -> Implement endpoint + tests
6. frontend-dev           -> Create HTMX templates (if needed)
7. Multi-agent review:
   - api-documenter (docs complete)
   - code-reviewer (quality)
```

**Quality Gates**:
- [ ] REST endpoint designed following VaWW patterns
- [ ] Pydantic schemas follow inheritance (Update -> Create -> Response)
- [ ] HTMX response pattern correct (HX-Trigger headers)
- [ ] Performance validated (no N+1 queries, appropriate indexes)
- [ ] VaWW compatibility maintained
- [ ] All specialists approved

### Critical Refactoring

```
Approval Chain:
1. architect              -> Structural design strategy, new patterns (if needed)
2. test-runner            -> Test preservation/migration strategy
3. Primary coordinates    -> Get multi-agent design approval
4. python-dev/frontend-dev -> Implement refactoring with improved structure
5. Multi-agent review:
   - code-reviewer (quality)
   - test-runner (coverage maintained)
```

**Quality Gates**:
- [ ] Structure improved vs baseline
- [ ] Tests still pass (`make test`)
- [ ] Quality metrics better (`make lint`)
- [ ] 80%+ test coverage maintained
- [ ] GitHub issue created for tracking

### VaWW Compatibility Changes

```
Approval Chain:
1. architect              -> Review addon integration impact
2. frontend-dev           -> Validate template compatibility
3. Primary coordinates    -> Get architect approval
4. frontend-dev           -> Implement template changes
5. code-reviewer          -> Quality and compatibility review
```

**Quality Gates**:
- [ ] Template naming follows VaWW convention
- [ ] HTMX patterns match VaWW
- [ ] Pydantic schemas follow VaWW inheritance
- [ ] Route patterns match VaWW
- [ ] Future addon integration preserved

## Approval Protocol

### Step 1: Identify Change Type

```
Primary (orchestrator):
  -> Identify overlapping concerns
  -> Select appropriate approval chain from above
  -> Determine required specialists
```

### Step 2: Spawn Specialists

```
Primary:
  -> Spawn appropriate specialists sequentially
  -> Provide compressed context (summary, not full history)
  -> Define specific task scope
  -> Set success criteria
```

**Context Template:**
```
"Working on [change]. Database models in source/database/models.py.
VaWW compatibility context: [relevant/not-relevant]."
```

### Step 3: Collect Design Approvals

Each specialist must signal one of:
- **"Approved"** - No concerns, ready to proceed
- **"Approved with recommendations"** - Minor suggestions, can proceed
- **"Concern: [specific issue]"** - Blocking issue that must be addressed
- **"No concerns"** - Reviewed, nothing to add

### Step 4: Gate Check

**Before implementation can proceed**:
- All required specialists have approved
- No blocking concerns remain
- Quality gates for change type are satisfied
- Implementation path clear

If blocked:
- Address concerns with relevant specialist
- Re-submit for approval
- Escalate to user if specialists cannot agree

### Step 5: Coordinate Implementation

```
Primary:
  -> Delegate to python-dev and/or frontend-dev
  -> Monitor quality gates
  -> Gather review signoffs
  -> Integrate results
```

### Step 6: Final Signoff

```
Multi-agent review (parallel when possible):
  -> code-reviewer: Quality, standards, type hints
  -> test-runner: Test coverage verified
  -> api-documenter: API documentation (if external-facing)
  -> documenter: CHANGELOG, docs
```

## Example Approval Flow

**Scenario**: New Invoice API Endpoint

```
1. Primary: "This needs new API endpoint with database operations"
2. Primary -> architect: "Design /invoices endpoint with Pydantic schemas"
3. architect: Returns endpoint design with rationale
   Output: "Routes: GET/POST/PATCH/DELETE /invoices. Schemas: InvoiceCreate,
   InvoiceUpdate, InvoiceResponse. Follow VaWW patterns."
4. Primary -> performance-optimizer: "Review this design for query performance"
5. performance-optimizer: Approves with recommendations
   Output: "Approved. Add index on invoice_date for date range queries.
   Use joinedload for related data."
6. Primary -> api-documenter: "Document REST endpoint"
7. api-documenter: Approves
   Output: "Approved. OpenAPI spec complete. Pydantic schemas documented."
8. Primary -> python-dev: "Implement approved endpoint with recommendations"
9. python-dev: Implements routes, tests
10. Primary -> frontend-dev: "Create invoice templates matching VaWW"
11. frontend-dev: Creates templates
12. Primary -> code-reviewer: "Review implementation quality"
13. code-reviewer: Approves
    Output: "Approved. Type hints complete, tests cover edge cases,
    VaWW patterns followed."
14. Primary: Integrates, coordinates vc-manager for merge
```

## Decision Guide Summary

| Risk Level | Complexity | Action |
|------------|------------|--------|
| High Risk | Any | Multi-agent approval required |
| Any | High Complexity | Multi-agent approval required |
| Any | High Impact | Multi-agent approval required |
| Low Risk | Simple | Single agent or direct implementation |

**High Risk Examples**: Database schema changes, core API patterns, VaWW compatibility
**High Complexity Examples**: Multiple domains affected, cross-cutting concerns
**High Impact Examples**: Core business logic changes, breaking changes

## Memory Tracking

After approval workflow completion, update `.claude/memory/current-session.md`:

```markdown
## Approval Completed: [Change Description]

**Type**: [Database Schema | API Endpoint | Refactoring | VaWW Compatibility]
**Specialists Consulted**: [list]
**Key Decisions**:
- [decision 1]
- [decision 2]

**Quality Gates Passed**:
- [x] [gate 1]
- [x] [gate 2]

**Implementation Agent**: python-dev / frontend-dev
**Status**: Approved for implementation
```

## Output Format

### On Success

```
[feature-name] APPROVED

Approval Chain: Completed
Quality Gates: All passed
Specialists: [list of approving agents]

Key Approvals:
- architect: "Design approved with index recommendations"
- performance-optimizer: "Query patterns validated, joinedload recommended"
- api-documenter: "REST endpoint documented, VaWW compatible"
- code-reviewer: "Quality standards met"

Implementation: Delegated to python-dev + frontend-dev
Audit recorded in .claude/memory/current-session.md
```

### On Blocked

```
[feature-name] APPROVAL BLOCKED

Blocking Issues:
- [agent]: "Concern: [specific issue]"

Required Actions:
1. [Action to address concern]
2. [Re-submit for approval]

Status: Awaiting resolution before implementation
```
