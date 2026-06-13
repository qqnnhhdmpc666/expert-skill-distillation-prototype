# Verifier / Gate Limitation Audit

## What the verifier and gate are good for

The current verifier/gate stack is useful for enforcing:

- required capability coverage
- required output fields
- obvious unsupported evidence rejection
- some false-positive rejection
- controlled promotion decisions after repair

This is already enough to support a meaningful controlled revision loop.

## What they do not prove

They do not prove:

- that a finding is semantically correct in a deep expert sense
- that a report is the most useful report for a human reviewer
- that the system generalizes to arbitrary tasks
- that a Harbor or LLM agent autonomously discovered a real novel vulnerability

## Current concrete limitations

1. verifier logic is mostly embedded in slice scripts instead of a reusable module
2. many checks are contract-oriented rather than semantics-oriented
3. unsupported-evidence checks are not uniformly exercised in every backend slice
4. gate acceptance is still closely tied to expected capability closure
5. no uncertainty bucket exists for “plausible but not confidently verified”

## Specific boundary statements

### Coverage

Good for controlled capability completeness.

Weak for open-ended findings that do not map cleanly to known capability IDs.

### Evidence binding

Good when evidence spans are absent or obviously unsupported.

Weak against subtle paraphrase drift, shallow keyword hits, or semantically misleading evidence snippets.

### Output contract

Strong on required field presence.

Weak on whether the recommended fix is actually appropriate or sufficient.

### Regression safety

Meaningful in the current clean-target and ablation slices.

Still too narrow to claim broad regression protection.

## Recommended next verifier/gate upgrades

1. split verifier output into submodules:
   - coverage
   - evidence grounding
   - output contract
   - regression safety
   - optional cost budget
2. add explicit `manual_review_required` and `uncertain` gate states
3. add more unsupported-evidence and adversarial paraphrase controls
4. add lightweight human audit sampling for accepted A2 packages
5. record why a gate accepted something beyond a single short reason string

## Safe conclusion

The verifier/gate stack is a **useful controlled acceptance mechanism**. It is not yet a trustworthy universal judge of skill quality.
