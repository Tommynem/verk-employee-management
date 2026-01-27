# Multi-Agent Coordination Examples

Real workflow examples extracted from production CLAUDE.md files demonstrating GroupChat patterns for common development scenarios.

---

## Example 1: API Endpoint Design (DefaultPattern)

**Scenario**: Designing a new REST API endpoint for customer management.

**Pattern**: DefaultPattern (repeatable state machine)

**Participants**: architect, api-documenter, {{SPECIALIST_A}}, architect (final)

### State Machine

```
START
  |
architect (design REST endpoints, Pydantic/Go types)
  |
api-documenter (OpenAPI specs, documentation)
  |
{{SPECIALIST_A}} (validate performance/security implications)
  |
architect (incorporate feedback, final approval)
  |
DECISION (go/no-go)
```

### Invocation

```
Primary: "Initiating DefaultPattern GroupChat for Issue #300: Customer Management API.
Following REST API design state machine.
Goal: Production-ready API design approved by all specialists.
Max turns: 8."
```

### Flow

**State 1 [architect]**: Designs GET/POST/PUT/DELETE /customers endpoints, defines request/response schemas (CustomerCreate, CustomerUpdate, CustomerResponse), plans integration with business logic layer.

**State 2 [api-documenter]**: Creates OpenAPI documentation, adds tags ["customers"], defines response models, suggests pagination for GET /customers (limit/offset parameters).

**State 3 [{{SPECIALIST_A}}]**: Reviews query patterns. GET /customers needs efficient joins to prevent N+1 queries. Add indexes: customer.email (unique), customer.name (search). Recommends caching strategy for read-heavy endpoints.

**State 4 [architect]**: Incorporates all feedback. Pagination added, indexes documented, caching strategy noted. Design complete and approved.

**Termination**: DECISION = GO. All specialists approved. Delegate to {{DEV_AGENT}} for implementation.

### Success Criteria

- REST endpoints designed following conventions
- OpenAPI documentation complete
- Performance/security validated
- All specialists approved

---

## Example 2: Database Schema Change Review (RoundRobinPattern)

**Scenario**: Adding a new 'product_variants' table with relationships to existing products.

**Pattern**: RoundRobinPattern (systematic coverage)

**Participants**: architect, {{SPECIALIST_A}}, api-documenter, {{SPECIALIST_B}}

**Order**: architect --> {{SPECIALIST_A}} --> api-documenter --> {{SPECIALIST_B}}

### Invocation

```
Primary: "Initiating RoundRobinPattern GroupChat for Issue #256.
Participants: architect, {{SPECIALIST_A}}, api-documenter, {{SPECIALIST_B}}.
Goal: Review new 'product_variants' table.
Order: architect --> {{SPECIALIST_A}} --> api-documenter --> {{SPECIALIST_B}}.
Max cycles: 2."
```

### Flow

**Cycle 1**:

Turn 1 --> architect: Reviews relationships, foreign keys, business logic alignment.
- **Concern**: Missing unique constraint on (product_id, variant_name)

Turn 2 --> {{SPECIALIST_A}}: Reviews indexes and query patterns.
- **Recommendation**: Index on product_id for joins, variant_name for searches
- **Note**: Watch for cascade deletion performance on large datasets

Turn 3 --> api-documenter: Confirms REST schema alignment.
- **Suggestion**: GET /products/{id}/variants endpoint
- **Note**: Need variant-specific response schema

Turn 4 --> {{SPECIALIST_B}}: Reviews module placement.
- **Suggestion**: Organize in source/products/variants/ for clear separation
- **Benefits**: Clean imports, follows established patterns

**Cycle 2**:

- architect: Constraint added. **Approve.**
- {{SPECIALIST_A}}: Indexes noted, cascade reviewed. **Approve.**
- api-documenter: Endpoint added to plan. **Approve.**
- {{SPECIALIST_B}}: Module structure approved. **Approve.**

**Termination**: All specialists approved. Delegate to {{DEV_AGENT}} for implementation.

### Success Criteria

- All specialists approve (no blocking concerns)
- Indexes identified for new columns
- API impact documented
- Migration strategy clear

---

## Example 3: Complex Bug Investigation (AutoPattern)

**Scenario**: Customer order slowdown - mysterious performance degradation.

**Pattern**: AutoPattern (dynamic routing based on findings)

**Participants**: debugger, {{SPECIALIST_A}}, refactor-specialist, architect

### Routing Logic

- Logs/stack traces --> debugger
- Performance/query issues --> {{SPECIALIST_A}}
- Structural issues/code smells --> refactor-specialist
- Architectural concerns --> architect

### Invocation

```
Primary: "Initiating AutoPattern GroupChat for Issue #234.
Participants: debugger, {{SPECIALIST_A}}, refactor-specialist, architect.
Goal: Identify root cause of customer order slowdown.
Max turns: 10."
```

### Flow

**Turn 1 --> debugger** (Initial investigation):
- Analyzes stack traces and logs
- Finds slow operations in OrderManager.get_order_items()
- Suspects database query issue

**Primary routes to {{SPECIALIST_A}}** (performance concern identified)

**Turn 2 --> {{SPECIALIST_A}}**:
- Confirms N+1 query pattern in get_order_items()
- Each order triggers separate query for items
- Recommends eager loading with joinedload

**Primary routes to debugger** (validate fix approach)

**Turn 3 --> debugger**:
- Validates eager loading approach
- Confirms joinedload will reduce queries from N+1 to 2
- Provides test query for verification

**Primary routes to architect** (check architectural impact)

**Turn 4 --> architect**:
- Reviews if fix impacts other query patterns
- No conflicts found with existing patterns
- Approves approach

**Termination**: Root cause identified (N+1 query). Fix strategy validated (eager loading with joinedload). Delegate to {{DEV_AGENT}} for fix implementation.

### Success Criteria

- Root cause identified with evidence
- Fix approach validated by relevant specialists
- No conflicting recommendations
- Clear implementation path

---

## Example 4: Critical Architecture Decision (ManualPattern)

**Scenario**: Choosing caching strategy (Redis vs in-memory vs none) for high-traffic endpoints.

**Pattern**: ManualPattern (user controls each step)

**Participants**: architect, {{SPECIALIST_A}}, {{SPECIALIST_B}}

### Invocation

```
Primary: "Initiating ManualPattern GroupChat for Issue #400: Choose caching strategy.
Participants: architect, {{SPECIALIST_A}}, {{SPECIALIST_B}}.
User will guide conversation."
```

### Flow

**Turn 1 --> architect**: Presents three options with trade-offs.
- Redis: Distributed, persistent, adds infrastructure complexity
- In-memory: Fast, simple, lost on restart, limited by RAM
- None: Simplest, slowest for cache-friendly operations

[HALT - Present to user]

**User**: "Ask {{SPECIALIST_A}} about performance implications of each."

**Turn 2 --> {{SPECIALIST_A}}**:
- Redis adds network latency (2-5ms per request)
- In-memory fastest but limited by available RAM
- None simplest but slowest for repeated reads of same data
- For current load, in-memory sufficient with 5min TTL

[HALT - Present to user]

**User**: "Ask {{SPECIALIST_B}} about operational complexity."

**Turn 3 --> {{SPECIALIST_B}}**:
- Redis requires infrastructure (Docker/managed service), monitoring, failure handling
- In-memory simple but cache lost on restart, no sharing between instances
- None has no operational overhead
- In-memory acceptable for single-instance deployment

[HALT - Present to user]

**User**: "Decision: Start with in-memory for simplicity, migrate to Redis if needed. Architect, document this as ADR."

**Turn 4 --> architect**:
- ADR drafted with rationale
- Documents: context, decision, consequences, migration path

[HALT - Present to user]

**User**: "Approved. Proceed."

**Termination**: User approval received. Decision documented in ADR.

### Success Criteria

- User guided exploration
- All perspectives considered
- Decision documented with rationale
- Migration path defined

---

## Example 5: Security Feature Review (RoundRobinPattern)

**Scenario**: New authentication endpoint with JWT tokens.

**Pattern**: RoundRobinPattern (systematic security coverage)

**Participants**: security-specialist, architect, code-reviewer

**Order**: security-specialist --> architect --> code-reviewer

### Invocation

```
Primary: "Initiating RoundRobinPattern GroupChat for Issue #450.
Participants: security-specialist, architect, code-reviewer.
Goal: Review authentication endpoint security.
Order: security-specialist --> architect --> code-reviewer.
Max cycles: 2."
```

### Flow

**Cycle 1**:

Turn 1 --> security-specialist: Security analysis
- Reviews authentication flow
- **Recommendations**:
  - Rate limiting (5 attempts/15min)
  - bcrypt for password hashing (cost factor 12)
  - HTTPOnly cookies for refresh tokens
  - HTTPS only enforcement
- **Verifies**: No SQL injection risk (using parameterized queries)

Turn 2 --> architect: Architectural review
- Reviews integration with existing auth patterns
- **Confirms**: Follows hexagonal architecture boundaries
- **Adds**: Token rotation strategy for refresh tokens
- **Notes**: Consider token revocation endpoint for logout

Turn 3 --> code-reviewer: Implementation quality
- Reviews error handling
- **Recommends**: Generic error messages (no credential hints)
- **Verifies**: Proper input validation
- **Confirms**: Secure coding practices followed

**Cycle 2**:

- security-specialist: All recommendations addressed. **Approve.**
- architect: Integration confirmed. **Approve.**
- code-reviewer: Quality standards met. **Approve.**

**Termination**: All specialists approved. Ready for implementation.

### Success Criteria

- OWASP Top 10 considerations documented
- Authentication mechanisms validated
- Input validation verified
- Secure coding practices confirmed

---

## Example 6: ADR Creation Workflow (DefaultPattern)

**Scenario**: Creating ADR for database selection (PostgreSQL vs MySQL vs SQLite).

**Pattern**: DefaultPattern (formal ADR workflow)

**Participants**: architect, {{SPECIALIST_A}}, code-reviewer, documenter

### State Machine

```
architect (draft ADR with alternatives)
  |
{{SPECIALIST_A}} (technical perspective)
  |
code-reviewer (technical soundness)
  |
documenter (format, clarity)
  |
user approval (HALT)
  |
DECISION (approved/needs-revision)
```

### Invocation

```
Primary: "Initiating DefaultPattern GroupChat for ADR: Database Selection.
Following ADR creation workflow.
Goal: High-quality ADR approved by specialists and user.
Max turns: 8."
```

### Flow

**State 1 [architect]**: Drafts ADR
- **Context**: Need persistent storage for business data
- **Alternatives**:
  1. PostgreSQL: Robust, full-featured, team expertise
  2. MySQL: Widely used, simpler replication
  3. SQLite: Embedded, zero config, limited concurrency
- **Decision**: PostgreSQL
- **Rationale**: Best fit for complex queries, team experience, production readiness

**State 2 [{{SPECIALIST_A}}]**: Technical review
- Validates query performance claims
- Confirms indexing strategies available
- Notes connection pooling requirements

**State 3 [code-reviewer]**: Technical soundness
- Reviews migration strategy feasibility
- Confirms backup/restore procedures
- Validates development workflow impact

**State 4 [documenter]**: Format and clarity
- Adjusts formatting to ADR template
- Clarifies consequences section
- Adds "Related Decisions" references

**HALT - Present to user for approval**

**User**: "Approved with minor edits to consequences."

**Termination**: ADR approved, assigned number ADR-0015.

### Success Criteria

- Context and problem clearly documented
- Alternatives analyzed with pros/cons
- Decision rationale clear
- Consequences identified
- Format compliant
- User approved

---

## Pattern Selection Guide

### Use DefaultPattern When:

- Task has repeatable steps (API design, ADR creation, migration planning)
- Need audit trail of each specialist's contribution
- Same workflow applies across multiple similar tasks
- Clear state machine with defined transitions

### Use RoundRobinPattern When:

- All specialists MUST review (security-sensitive, schema changes)
- Need systematic coverage (nothing skipped)
- Order matters but not rigidly (all must participate)
- Multi-agent approval required

### Use AutoPattern When:

- Dynamic investigation (bugs, performance issues)
- Can't predict which specialist needed next
- Findings from one specialist inform routing to next
- Exploration rather than predefined workflow

### Use ManualPattern When:

- Critical decisions with high stakes
- User wants to guide exploration
- Learning scenarios (understanding agent capabilities)
- Conflict resolution needed

---

## Memory Pattern for Examples

```markdown
Using `multi-agent-coordination` GroupChat for API design (#300).
Pattern: DefaultPattern
Participants: architect, api-documenter, performance-optimizer
Current Turn: 3/8 (State 3: performance review)
Progress:
  - architect: Designed 4 endpoints with schemas
  - api-documenter: OpenAPI spec complete, pagination added
Next Agent: performance-optimizer (query review)
Decisions: Using limit/offset pagination, customer.email unique index
```

---

## Tracking Sessions

Document all GroupChat sessions in `.claude/memory/groupchat-sessions.md`:

```markdown
## Session: 2024-01-15 - API Design #300

**Pattern**: DefaultPattern
**Goal**: Customer Management API design
**Participants**: architect, api-documenter, performance-optimizer
**Turns**: 5/8
**Outcome**: GO - All approved
**Baseline Estimate**: Sequential would have been ~8 turns
**Effectiveness**: 37.5% fewer turns, caught pagination issue early

### Key Decisions
- Limit/offset pagination for GET /customers
- Indexes on email (unique), name (search)
- 5min cache TTL for read endpoints

### Follow-up
- Delegate to python-dev for implementation
- Track implementation success
```
