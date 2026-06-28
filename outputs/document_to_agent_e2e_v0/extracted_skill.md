# Extracted Dependency-Use Triage Skill

1. Inspect dependency declarations first. Accept direct pinned declarations from `requirements.txt`, lock files, or equivalent project metadata.
2. Resolve the declared package version before deciding whether an advisory applies.
3. Inspect import or runtime use sites. A declared dependency with no import/use evidence must not be reported as used and affected.
4. Compare the resolved version against the advisory affected range. A fixed or outside-range version must be reported as used but not affected.
5. A valid `dependency_used_and_affected` decision requires declaration evidence, resolved version evidence, import/use evidence, advisory affected-range evidence, and decision evidence.
6. If required evidence is missing, choose `dependency_present_not_used` or `unresolved`; do not force an affected decision.
7. Produce a schema-valid decision with evidence references containing file path, evidence type, and line/span when available.

## Scope
- Local repo-level dependency-use triage only.
