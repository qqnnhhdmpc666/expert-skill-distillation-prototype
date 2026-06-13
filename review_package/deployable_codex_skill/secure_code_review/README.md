# Deployable Codex Skill Package

This package is the P0 installable surface for the controlled secure-code-review Skill.

Install/use boundary:

- Use through `skill-deploy` commands.
- Treat all claims as bounded controlled evidence.
- Do not use for unauthorized real-target testing or exploit generation.

Smoke commands:

```powershell
skill-deploy health
skill-deploy compare-variants --cases upload,data_quality
skill-deploy evolve --suite secure_code_review --budget 3 --gate qgse_pareto
```
