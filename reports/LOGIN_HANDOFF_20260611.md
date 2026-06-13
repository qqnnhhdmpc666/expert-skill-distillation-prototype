# Login Handoff 2026-06-11

This document is the primary recovery note if the Codex conversation is lost after account switching.

Use this file as the first re-entry point.

---

## 1. Project in one paragraph

This repository is currently a **controlled research-system prototype** for:

`expert material -> normalized capabilities -> Skill Package -> execution -> verifier feedback -> typed repair -> revised Skill -> qualification/promotion`

The best current framing is:

**Environment-Grounded Expert Skill Distillation and Evolution with Evidence-Qualified Promotion**

Important:

- the main project is **expert knowledge distillation + Skill evolution**
- `QGSE / QGSE-Pareto / qualification cards` are **promotion-control layers**
- this is **not** currently a general vulnerability scanner
- this is **not** a full SPARK-PDI reproduction

---

## 2. Current status in plain language

As of 2026-06-11, the system is no longer just a UI demo.

It has reached a **controlled prototype** state with:

- a shared core under `src/skill_deployment/`
- 5 controlled task families through one offline pipeline
- typed verifier feedback and typed repair actions
- local live-LLM repair loops on several controlled tasks
- Harbor-backed upload/config repair-loop evidence
- artifact-backed lifecycle evidence, qualification cards, and promotion-mechanism comparison

The right summary is:

> the controlled closed loop is now reasonably complete and auditable, but the evidence is still bounded and not yet enough to claim stable real-world open-task deployment.

So the main gap is **evidence strength and real-world breadth**, not “the whole design is obviously broken.”

---

## 3. What is most credible right now

If someone asks “what actually works,” anchor on these:

### A. Controlled offline suite

File:

- [generalization_suite.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/generalization_suite.json)

Meaning:

- same shared pipeline across 5 controlled task families
- 5 different A1 feedback types
- 5 different repair actions
- A2 passes `5/5`

This is the strongest current evidence that the pipeline is not just one hard-coded upload example.

### B. Negative controls / verifier checks

Files:

- [negative_controls.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/negative_controls.json)
- [verifier_stress_checks.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/verifier_stress_checks.json)

Meaning:

- verifier is not blindly permissive
- fabricated evidence / swapped target / clean false-positive controls can fail as expected

### C. Local live-LLM loops

Files:

- [live_llm_repair_loop_upload_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/live_llm_repair_loop_upload_001/summary.json)
- [live_llm_repair_loop_data_quality_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/live_llm_repair_loop_data_quality_001/summary.json)
- [live_llm_repair_loop_config_security_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/live_llm_repair_loop_config_security_001/summary.json)
- [live_llm_repair_loop_api_review_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/live_llm_repair_loop_api_review_001/summary.json)

Meaning:

- upload and data-quality slices close the loop
- config/API slices still fail, which is useful negative evidence and should not be hidden

### D. Harbor live-LLM loops

Files:

- [harbor_llm_repair_loop_upload_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/harbor_llm_repair_loop_upload_001/summary.json)
- [harbor_llm_repair_loop_config_001/summary.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/harbor_llm_repair_loop_config_001/summary.json)
- [harbor_llm_repeatability_upload.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/harbor_llm_repeatability_upload.json)

Meaning:

- there is already bounded Harbor evidence for A1 fail -> repair -> A2 pass
- upload repeatability smoke exists
- but Harbor is still **narrow** and not unified as a full shared live backend

---

## 4. Best “read this first” file set

If resuming after context loss, read in this order:

1. [LOGIN_HANDOFF_20260611.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/LOGIN_HANDOFF_20260611.md)
2. [MORNING_STATUS_0800.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/MORNING_STATUS_0800.md)
3. [CURRENT_SYSTEM_SNAPSHOT.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/CURRENT_SYSTEM_SNAPSHOT.md)
4. [CLAIM_BOUNDARY.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/docs/CLAIM_BOUNDARY.md)
5. [SKILL_LIFECYCLE_EVIDENCE_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SKILL_LIFECYCLE_EVIDENCE_STATUS.md)
6. [SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md)

If more time is available, then read:

- [HARBOR_LLM_REPAIR_LOOP_AUDIT.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/HARBOR_LLM_REPAIR_LOOP_AUDIT.md)
- [SKILL_QUALIFICATION_CARD_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SKILL_QUALIFICATION_CARD_STATUS.md)
- [PROMOTION_MECHANISM_EXPLORATION.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/PROMOTION_MECHANISM_EXPLORATION.md)
- [REVIEWER_READINESS_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/REVIEWER_READINESS_STATUS.md)
- [SKILL_INSTALLATION_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SKILL_INSTALLATION_STATUS.md)

---

## 5. Canonical architecture and directories

### Core code

Canonical shared implementation lives in:

- [src/skill_deployment](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment)

Most important files there:

- [task_cases.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/task_cases.py)
- [capability_registry.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/capability_registry.py)
- [verifier.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/verifier.py)
- [repair.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/repair.py)
- [runner.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/runner.py)
- [qualification.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/qualification.py)
- [validity.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/src/skill_deployment/validity.py)

### Controlled task inputs

- [data/task_cases](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/data/task_cases)

Current main controlled cases:

- `upload_security_001`
- `auth_access_control_001`
- `config_security_001`
- `api_review_001`
- `data_quality_review_001`

Negative controls also exist:

- `upload_security_negative`
- `config_security_false_positive_control`

### Main outputs

- [outputs/validation](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation)
- [outputs/skill_lifecycle_evidence](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/skill_lifecycle_evidence)
- [outputs/installed_skills](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/installed_skills)
- [outputs/reviewer_readiness](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/reviewer_readiness)
- [outputs/live_llm_repair_loop_upload_001](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/live_llm_repair_loop_upload_001)
- [outputs/harbor_llm_repair_loop_upload_001](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/harbor_llm_repair_loop_upload_001)

### Review/export deliverables

- [review_package](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/review_package)
- [review_package_export.zip](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/review_package_export.zip)

---

## 6. What was added in the latest phase

The latest work after the earlier “Morning Status” base was:

### A. Standardized lifecycle evidence

Files:

- [outputs/skill_lifecycle_evidence/index.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/skill_lifecycle_evidence/index.json)
- [reports/SKILL_LIFECYCLE_EVIDENCE_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SKILL_LIFECYCLE_EVIDENCE_STATUS.md)

This added:

- per-case distillation bundles
- per-case trajectory bundles
- normalized A1/A2 trace summaries
- lifecycle artifacts that are easier to export and explain

### B. Net-effect matrix

File:

- [skill_net_effect_matrix.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/skill_net_effect_matrix.json)

This compares:

- no skill
- skill v1
- skill v2

Current meaning:

- controlled verifier-scored gain exists
- still not the same thing as open-world utility

### C. Gap ledger

File:

- [SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SPARK_COLLEAGUE_SKILLGEN_SKILLGRAD_GAP_LEDGER.md)

This is the best file for “what are we still missing relative to adjacent work.”

### D. Install / rollback surface

Files:

- [registry.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/installed_skills/registry.json)
- [SKILL_INSTALLATION_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/SKILL_INSTALLATION_STATUS.md)

This is a controlled install/version/rollback surface over lifecycle artifacts.

Important boundary:

- it is a prototype operationalization surface
- not a production package manager

### E. Reviewer-prep layer

Files:

- [reviewer_assessment.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/reviewer_readiness/reviewer_assessment.json)
- [REVIEWER_READINESS_STATUS.md](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/reports/REVIEWER_READINESS_STATUS.md)

This tells us which cases are clean enough to show first.

Current recommendation:

- show first: `upload_security_001`, `data_quality_review_001`
- hold / internal first: `api_review_001`, `auth_access_control_001`, `config_security_001`

---

## 7. Current safe external wording

Use something like:

> This is a controlled prototype for expert knowledge distillation into Skill Packages. It supports execution, typed verifier feedback, typed repair, revised-skill reruns, lifecycle evidence, and bounded local/Harbor execution evidence.

Shorter version:

> The controlled closed loop is basically formed, but the current evidence is still bounded and not enough yet for broad real-world deployment claims.

Do **not** say:

- “general vulnerability scanner”
- “full SPARK reproduction”
- “already stable for arbitrary real tasks”
- “broad Harbor LLM generalization”
- “mature open-source platform”

---

## 8. If the teacher asks “what is the current status?”

Natural short answer:

> 现在这个工作已经从上周的 demo 往前推进成一个受控原型了，闭环、验证和证据链都比较完整了；但目前还是受控证据，离真实场景下稳定泛化使用还有距离，下一步主要还是补真实任务、真实执行环境和更强的验证。

If asked whether the gap is design or evidence:

> 目前更像是证据还不够强，不是主线设计已经被证明有问题。受控任务里它是能跑通的，但要走到真实场景可用，还需要更广泛任务和更强真实环境验证。

---

## 9. Immediate next best steps

If resuming development, do these next:

1. **Turn Harbor from replay-style shared access into a true live shared backend**
   - current Harbor integration is still partially replay/read-existing
   - this is one of the biggest remaining architectural gaps

2. **Add at least one more Harbor live family beyond upload/config**
   - current Harbor evidence is still too narrow

3. **Attach one real human/external usefulness review**
   - reviewer-prep packets already exist
   - but there is still no actual external/human scored review

4. **Strengthen live-LLM evidence beyond upload/data_quality**
   - config and API loops currently fail
   - useful negative evidence, but they should eventually either improve or be clearly demoted

5. **Upgrade provenance from keyword projection toward stronger distillation evidence**
   - current lifecycle provenance is useful and exportable
   - but still controlled and weaker than a more semantic distiller

6. **Add larger-sample repeatability / prompt sensitivity**
   - currently only a small Harbor upload smoke exists

---

## 10. What to run first after resuming

From the project root:

```powershell
python -m pytest -q
python scripts\build_skill_lifecycle_artifacts.py
python scripts\build_skill_operationalization_artifacts.py
python scripts\export_review_package.py
python scripts\validate_review_package.py
```

If the goal is to re-check the main controlled suite:

```powershell
python scripts\run_generalization_suite.py --backend offline_deterministic --scenarios upload,auth,config,api_review,data_quality
```

If the goal is to re-check the main current artifacts:

- [generalization_suite.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/generalization_suite.json)
- [skill_qualification_cards.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/validation/skill_qualification_cards.json)
- [index.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/skill_lifecycle_evidence/index.json)
- [registry.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/installed_skills/registry.json)
- [reviewer_assessment.json](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/outputs/reviewer_readiness/reviewer_assessment.json)

---

## 11. UI / demo note

The UI is **not** the most important truth source.

Use these as the main deliverables:

- review package
- lifecycle evidence bundles
- validation outputs
- qualification / validity cards
- Harbor/local run summaries

The Streamlit app is useful for narration and screenshots, but the credible core is the artifact chain.

Main app file:

- [streamlit_app.py](/C:/Users/31552/Documents/New%20project/expert-skill-distillation-prototype-main/demo/streamlit_app.py)

---

## 12. Final one-screen takeaway

If you reopen this project later and remember only one thing, remember this:

> The repo is currently in a **controlled prototype** state where the expert-material -> skill -> execution -> feedback -> repair -> qualification loop is already formed and well-instrumented, but the main remaining gap is still **real-world breadth and evidence strength**, not yet a fully broken design.

