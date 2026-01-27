---
name: Multi-Agent Coordination (GroupChat)
description: Orchestrate multi-agent conversations for complex problems requiring dynamic specialist routing, collaborative design sessions, systematic reviews, and multi-agent approval processes. Use when back-and-forth dialogue between specialists is needed. NOT for simple delegation (single specialist tasks), sequential TDD cycles, documentation updates, or VC/GitHub operations - use direct delegation for those.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Task
---

# Multi-Agent Coordination (GroupChat)

Conversational multi-agent coordination pattern where specialists engage in back-and-forth dialogue to solve complex problems, make collaborative decisions, or provide systematic reviews.

## Quick Reference

| Pattern | Use Case | Flow | Termination |
|---------|----------|------|-------------|
| AutoPattern | Dynamic investigation | Primary routes based on context | Root cause found, max turns |
| RoundRobinPattern | Systematic review | Fixed order, all participate | All approve, max cycles |
| DefaultPattern | Repeatable workflows | State machine transitions | Decision state reached |
| ManualPattern | Critical decisions | User controls each step | User approval |

## Key Principle

**"GroupChat for Conversations, Delegation for Actions"**

Use GroupChat when multi-agent back-and-forth is needed. Use direct delegation for straightforward tasks.

---

## Decision Tree: Delegation vs GroupChat

```
Is this conversational (multi-agent back-and-forth needed)?
|-- NO --> Use direct delegation (3-tier model)
|   |-- Examples: git ops, docs, simple implementation, {{DEV_AGENT}} work
|
|-- YES --> Use GroupChat
    |
    |-- Well-defined repeatable workflow?
    |   |-- YES --> DefaultPattern (state machine)
    |       |-- Examples: {{DEFAULT_PATTERN_USE_CASE}}
    |
    |-- All specialists must participate?
    |   |-- YES --> RoundRobinPattern (systematic)
    |       |-- Examples: {{ROUNDROBIN_USE_CASE}}
    |
    |-- Dynamic context-dependent routing?
    |   |-- YES --> AutoPattern (LLM selection)
    |       |-- Examples: Bug investigation, performance diagnosis
    |
    |-- User approval needed at each step?
        |-- YES --> ManualPattern (user control)
            |-- Examples: Critical decisions, high-risk changes
```

---

## Pattern 1: AutoPattern (Dynamic Context-Aware Selection)

**Description**: Primary agent dynamically selects next speaker based on conversation context, using extended thinking to route to the most appropriate specialist.

**How It Works**:

1. Primary analyzes current conversation state
2. Uses extended thinking to determine which specialist needed next
3. Explicitly invokes that specialist
4. Specialist contributes, primary repeats
5. Terminates when goal met or max turns reached

**When to Use**:

- Complex bug investigation: Route between debugger, {{SPECIALIST_A}}, {{SPECIALIST_B}} based on findings
- Performance diagnosis: Dynamic selection based on bottleneck type
- Architecture design exploration: Route based on design aspect

**Invocation Template**:

```
Primary: "Initiating AutoPattern GroupChat for Issue #{{ISSUE_NUMBER}}.
Participants: {{PARTICIPANT_LIST}}.
Goal: {{SPECIFIC_GOAL}}.
Max turns: 10."
```

**Routing Logic**:

- Logs/stack traces --> debugger
- {{DOMAIN_CONCERN_A}} --> {{SPECIALIST_A}}
- Structural issues/code smells --> refactor-specialist
- Architectural concerns/design flaws --> architect

**Termination Conditions**:

- Root cause identified
- Solution approach validated
- Max turns (10 for investigation, 8 for design)
- No progress after 3 consecutive turns

---

## Pattern 2: RoundRobinPattern (Systematic Coverage)

**Description**: All participating agents speak in fixed order, ensuring every perspective is considered. Guarantees no specialist is skipped.

**How It Works**:

1. Primary defines participant list in specific order
2. Each agent speaks once (or until they signal "no concerns")
3. Cycle repeats if needed (max 2-3 cycles)
4. Terminates when all approve or issues raised

**When to Use**:

- Database schema changes: Guarantee all relevant specialists review
- Critical code review: Ensure comprehensive examination
- {{PROJECT_SPECIFIC_REVIEW}}: Systematic review before deployment

**Invocation Template**:

```
Primary: "Initiating RoundRobinPattern GroupChat for Issue #{{ISSUE_NUMBER}}.
Participants: {{PARTICIPANT_LIST}}.
Goal: {{REVIEW_GOAL}}.
Order: {{AGENT_ORDER}}.
Max cycles: 2."
```

**Review Focus by Agent**:

- **architect**: Relationships, foreign keys, business logic alignment, data integrity
- **{{SPECIALIST_A}}**: {{SPECIALIST_A_FOCUS}}
- **api-documenter**: REST/API impact, documentation, contracts
- **code-reviewer**: Quality, standards, type safety

**Termination Conditions**:

- All agents approve (no concerns)
- Critical issues identified (halt for redesign)
- Max cycles completed (2-3)

---

## Pattern 3: DefaultPattern (Explicit State Machines)

**Description**: Predefined transition rules specify which agent speaks next. Creates repeatable workflows with clear audit trails.

**How It Works**:

1. Primary defines state machine: agent A --> agent B --> agent C --> decision
2. Explicit transition triggers (e.g., "after architect designs, api-documenter specs")
3. Each state completes before transition
4. Terminates at final decision state

**When to Use**:

- {{DEFAULT_PATTERN_USE_CASE}}: Repeatable workflow for each new instance
- ADR creation: Formal workflow (architect --> reviewers --> documenter --> approval)
- {{PROJECT_WORKFLOW}}: Standard steps for domain-specific work

**State Machine Template**:

```
START
  |
architect (design {{ARTIFACT}}, define structure)
  |
api-documenter (create specs, documentation)
  |
{{SPECIALIST_A}} (validate {{DOMAIN_CONCERN_A}})
  |
architect (incorporate feedback, final approval)
  |
DECISION (approved/needs-revision)
```

**Invocation Template**:

```
Primary: "Initiating DefaultPattern GroupChat for Issue #{{ISSUE_NUMBER}}: {{TASK_NAME}}.
Following {{WORKFLOW_NAME}} state machine.
Goal: Production-ready design approved by all specialists.
Max turns: 8."
```

**Termination Conditions**:

- Reach DECISION state
- All required transitions complete
- Max turns reached (escalate to user)

---

## Pattern 4: ManualPattern (User-Controlled Steps)

**Description**: Returns control to user after each agent speaks. Maximum oversight and transparency.

**How It Works**:

1. Primary invokes agent
2. Agent contributes
3. Primary HALTS, presents to user
4. User decides next agent or approves
5. Repeat until user satisfied

**When to Use**:

- Critical decisions: User wants to guide exploration
- Learning/training scenarios: Understanding agent capabilities
- High-risk changes: User approval at each step
- Conflict resolution: User arbitrates between agent recommendations

**Invocation Template**:

```
Primary: "Initiating ManualPattern GroupChat for Issue #{{ISSUE_NUMBER}}: {{DECISION_TOPIC}}.
User will guide conversation."
```

**Conversation Flow**:

```
Turn 1 --> {{AGENT_A}}: Presents options with trade-offs.
[HALT - Present to user]

User: "Ask {{AGENT_B}} about {{CONCERN}}."

Turn 2 --> {{AGENT_B}}: Provides perspective on {{CONCERN}}.
[HALT - Present to user]

User: "Decision: {{CHOICE}}. {{AGENT_A}}, document this."

Turn 3 --> {{AGENT_A}}: Documents decision with rationale.
[HALT - Present to user]

User: "Approved. Proceed."
```

**Termination Conditions**:

- User explicitly approves
- User cancels conversation
- Decision documented and accepted

---

## Session Management

### Initiating a GroupChat

**Step 1**: Identify conversational scenario (use decision tree)

**Step 2**: Select appropriate pattern:

- DefaultPattern: Repeatable workflows, standard processes
- RoundRobinPattern: Systematic reviews, multi-agent approval
- AutoPattern: Investigations, complex analysis
- ManualPattern: Critical decisions, high-risk changes

**Step 3**: Define parameters:

- Participants (which agents)
- Goal (specific objective)
- Max turns (10 for investigation, 8 for design, 5 for review)
- Termination condition (goal met, max turns, consensus, user approval)

**Step 4**: Announce initiation:

```
"Initiating [Pattern] GroupChat for [Issue/Task].
Participants: [agents].
Goal: [objective].
Max turns: [N].
Termination: [condition]."
```

**Step 5**: Manage conversation per pattern rules

**Step 6**: Document in `.claude/memory/groupchat-sessions.md`

### During GroupChat

**Primary's Role**:

- **Orchestrate** conversation flow (select speakers, manage turns)
- **Synthesize** agent contributions (identify consensus or conflicts)
- **Monitor** progress toward goal (are we getting closer?)
- **Enforce** termination conditions (max turns, goal met)
- **Track** conversation in memory (preserve context)

**Agent Contributions**:

- **Build on previous**: Reference other agents' findings
- **Challenge when needed**: Identify flaws or risks
- **Be specific**: Provide concrete recommendations, not vague
- **Signal completion**: "No concerns" or "Approved" when satisfied
- **Escalate**: Request additional specialists if needed

**Context Management**:

- **Preserve**: Each agent has full conversation history
- **Summarize**: Primary provides brief summaries between turns
- **Reference**: Agents cite each other ("As {{AGENT}} noted...")
- **Document**: All key decisions/findings captured in session log

### Terminating GroupChat

**Goal-Based Termination**:

- Root cause identified (investigation)
- Design approved by all (planning)
- All specialists reviewed (systematic review)
- Decision reached and documented (ADR)

**Turn-Based Termination**:

- Max turns reached (10 for investigation, 8 for design, 5 for review)
- If goal not met, summarize progress and escalate to user
- Document why goal wasn't reached, what's needed next

**Consensus Termination**:

- All participants approve/signal "no concerns"
- No blocking issues remain
- Implementation path clear

**Post-Termination**:

1. **Summarize** outcome in current-session.md
2. **Document** full session in groupchat-sessions.md
3. **Delegate** implementation (usually to {{DEV_AGENT}})
4. **Track** success (did implementation work as designed?)

---

## Best Practices

### Do's

- **Use decision tree**: Always check if conversational vs action-oriented
- **Be explicit**: Announce pattern, participants, goal, max turns
- **Document everything**: Track in groupchat-sessions.md for learning
- **Set turn limits**: Prevent runaway conversations (10 max for investigation)
- **Synthesize**: Primary summarizes between turns for clarity
- **Measure**: Compare to baseline, track effectiveness
- **Learn**: Monthly review, refine patterns over time

### Don'ts

- **Don't force usage**: GroupChat for appropriate scenarios only
- **Don't skip delegation**: Simple tasks still use 3-tier model
- **Don't exceed turn limits**: Escalate to user if stuck
- **Don't lose context**: Document as you go, not after
- **Don't ignore patterns**: Use appropriate pattern for scenario
- **Don't skip termination conditions**: Define upfront, enforce
- **Don't abandon tracking**: Measure effectiveness to improve

### Anti-Patterns

**Over-Engineering**: Using GroupChat for simple tasks that need single agent

- **Solution**: Follow decision tree strictly, bias toward delegation

**Runaway Conversations**: No termination condition, conversation goes on indefinitely

- **Solution**: Set max turns upfront (10/8/5), enforce strictly

**Passive Orchestration**: Primary not managing flow, agents confused about turns

- **Solution**: Primary explicitly selects next agent, synthesizes progress

**Lost Context**: Information from early turns forgotten by later agents

- **Solution**: Primary summarizes key points, agents reference each other

**Wrong Pattern**: Using AutoPattern for systematic review (should be RoundRobin)

- **Solution**: Match pattern to scenario type (use workflow examples)

**No Measurement**: Can't assess if GroupChat is better than baseline

- **Solution**: Always estimate baseline, track metrics in session log

---

## Measuring Effectiveness

### Key Metrics

**Efficiency**:

- **Turns to solution**: Fewer than sequential baseline?
- **Duration**: Faster than baseline?
- **Primary overhead**: Reduced orchestration effort?

**Quality**:

- **Solution completeness**: All concerns addressed?
- **Issues caught**: More than sequential review?
- **Implementation success**: First-time pass rate?

**Context**:

- **Information preservation**: All decisions captured?
- **Clarity**: Conversation flow logical?
- **Consensus**: Agreement vs conflict?

### Target Improvements

- **20-30% fewer turns** (efficiency)
- **20% more issues caught** (quality)
- **90% less information loss** (context)
- **30% less primary overhead** (orchestration)

### Monthly Review

1. Review all groupchat-sessions.md entries
2. Calculate averages per pattern (turns, success rate, effectiveness)
3. Identify most/least effective patterns and scenarios
4. Update agent-performance.md with findings
5. Refine decision tree if needed
6. Archive sessions with summary

---

## Memory Pattern

Memory tracks position and decisions, NOT workflow details:

```markdown
Using `multi-agent-coordination` GroupChat for [task] (#issue).
Pattern: {{PATTERN_NAME}}
Participants: {{PARTICIPANT_LIST}}
Current Turn: 3/8
Progress: [key findings so far]
Next Agent: {{NEXT_AGENT}}
```

Keep memory lean by referencing the skill, not duplicating it.

---

## Handoff Protocol

When delegating after GroupChat completion:

1. **Compressed Context** (summary, not full history):
   - "GroupChat completed for [task]. Approved design: [summary]. Key decisions: [list]."

2. **Specific Task Scope** (clear boundaries):
   - "Implement approved design. [Specific implementation details from GroupChat outcome]."

3. **Success Criteria**:
   - "Implementation should match approved design. All specialists approved [X, Y, Z]."

4. **Expected Return Format**:
   - "Return implementation file paths and confirmation tests pass."

---

## Configuration Placeholders

Replace these placeholders when applying to your project:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{DEV_AGENT}}` | Primary implementation agent | `python-dev`, `go-dev`, `svelte-dev` |
| `{{SPECIALIST_A}}` | Domain-specific specialist | `performance-optimizer`, `security-specialist` |
| `{{SPECIALIST_B}}` | Additional specialist | `dx-optimizer`, `refactor-specialist` |
| `{{DEFAULT_PATTERN_USE_CASE}}` | Primary DefaultPattern use case | `REST API design`, `FastAPI migration` |
| `{{ROUNDROBIN_USE_CASE}}` | Primary RoundRobin use case | `Database schema changes`, `Security reviews` |
| `{{PROJECT_SPECIFIC_REVIEW}}` | Project-specific review type | `FastAPI endpoint validation`, `Security feature review` |
| `{{DOMAIN_CONCERN_A}}` | Domain-specific concern | `Security concerns`, `Performance issues` |
| `{{SPECIALIST_A_FOCUS}}` | What specialist A reviews | `Query patterns, indexes`, `Authentication, input validation` |
| `{{PROJECT_WORKFLOW}}` | Project-specific workflow | `FastAPI migration`, `REST endpoint design` |
