# Repo-Level Dependency-Use Triage Expert Material

This material defines a bounded repo-level dependency-use triage Skill. It is
not a vulnerability discovery procedure and it does not decide exploitability.

## Stable workflow

1. Identify dependency declaration evidence from repository dependency files.
2. Identify resolved version or lock/version evidence from the same declared
   dependency source when available.
3. Identify import or use-site evidence in repository source files.
4. Consult only the allowed advisory snapshot supplied to the task.
5. Compare the resolved version against the advisory affected range.
6. Choose exactly one decision:
   - `dependency_used_and_affected`
   - `dependency_used_not_affected`
   - `dependency_present_not_used`
   - `dependency_not_declared`
   - `unresolved`
7. Abstain or fail safe when required repository evidence is insufficient.
8. Never decide affectedness from advisory evidence alone.
9. Preserve evidence references for declaration, version, use site, advisory
   range, and final decision.

## Skill and knowledge boundary

The Skill owns stable procedures, decision constraints, evidence requirements,
and abstention policy. The Knowledge side owns concrete advisory facts, package
names, affected ranges, repository evidence sources, resolved versions, and
source file evidence.

## Scope limits

This Skill is for dependency-use triage over declared repository evidence. It
does not claim reachability, exploitability, broad vulnerability discovery, or
production scanner completeness.
