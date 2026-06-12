# Handoff For Next Chat

Read this first in a new Codex chat.

## Current Positioning

The project is a Contract-Grounded / Evidence-Grounded Skill Evolution Runtime for live agents. It is not a production vulnerability scanner, not a full SPARK reproduction, not a SWE-bench agent, and not an official external security benchmark result.

Current strongest claim:

```text
The repository implements a research-grade installed Skill runtime with evidence bundles, live contract normalization, bounded external/semiexternal validation, ablation evidence, and strict candidate rejection/promotion gates.
```

Current caveat:

```text
External official benchmark effectiveness is still not demonstrated. Evolution improvement is demonstrated only as staged promotion proposals, not automatic deployment.
```

## Latest New Work

The latest sprint added:

- `src/skill_deployment/live_contract.py`
- `skill-deploy live-contract-validation`
- `skill-deploy external-generalization`
- `skill-deploy live-mechanism-ablation`
- `skill-deploy contract-improvement-demo`
- `skill-deploy iterative-contract-improvement`
- public/GitHub-facing docs and reproduction docs

## Latest Key Results

- `controlled_internal`: pass
- `security_depth`: pass_local_bounded
- `live_contract_effectiveness`: pass
- `external_generalization`: partial
- `mechanism_ablation`: supports_mechanism
- `evolution_improvement`: demonstrated as staged promotion proposal
- `external_harness`: infra_blocked
- `public_release_readiness`: pass
- `academic_claim_readiness`: strong_candidate_with_external_gap

## Reports To Read First

1. `reports/GRAND_AUTONOMOUS_SPRINT_STATUS.md`
2. `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`
3. `reports/LIVE_CONTRACT_VALIDATION_STATUS.md`
4. `reports/EXTERNAL_GENERALIZATION_VALIDATION_STATUS.md`
5. `reports/LIVE_MECHANISM_ABLATION_STATUS.md`
6. `reports/CONTRACT_IMPROVEMENT_DEMO_STATUS.md`
7. `reports/ITERATIVE_CONTRACT_IMPROVEMENT_STATUS.md`
8. `docs/ARCHITECTURE_AND_DESIGN.md`
9. `docs/USER_GUIDE.md`

## Commands To Reproduce Latest Evidence

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2

$env:OPENAI_API_KEY = "<your key>"
skill-deploy live-contract-validation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy external-generalization --installed secure_code_review --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy live-mechanism-ablation --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy contract-improvement-demo --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash
skill-deploy iterative-contract-improvement --installed secure_code_review --base-url https://api.deepseek.com --model deepseek-v4-flash --budget 5

skill-deploy representative-matrix
skill-deploy grand-maturity-report
python scripts\build_review_package_manifest.py

python -m pytest -q
python scripts\validate_task_cases.py
skill-deploy validate-review-package
```

## Secret / API Key Notes

Do not write API keys to files. The key should only be set in the current process environment. Before finalizing, run a secret scan for the literal key and for `OPENAI_API_KEY`.

The user provided a DeepSeek API key in chat. Because it appeared in chat, rotating it later is recommended.

## What Is Still Not Proven

- Official external security benchmark performance.
- SWE-bench gold-patch resolved execution; official harness remains infra-blocked.
- Live LLM behavior is still variable outside the representative contract set.
- Evolution has a staged promotion proposal on the declared validation slice, but it is not auto-installed and not externally benchmarked.
- Public release is prototype-pass, not production support.

## Best Next Steps

1. Human-review the staged candidate proposal and decide whether to install as a v3 experimental package.
2. Try a smaller, stable official external security subset if available.
3. Resolve SWE-bench conda/Docker image build blocker.
4. Add human/third-party authored hidden cases.
5. Run multi-seed/live-repeat stability on the staged candidate before making a stronger evolution claim.
