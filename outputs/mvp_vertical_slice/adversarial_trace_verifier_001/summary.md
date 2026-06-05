# Adversarial Trace Verifier 001

## Purpose

Check whether the trace verifier rejects obvious fake or weak rule-application evidence.

| Case | Expected Reject Reason | Verifier Passed | Rejected As Expected | Key Error |
|---|---|---|---|---|
| fake_evidence_span | evidence span is unrelated to the API case and R005 trigger terms | False | True | rule_applications[4] R005 evidence_span lacks case-relevant terms |
| generic_trigger | trigger and evidence are generic rather than case/rule relevant | False | True | rule_applications[5] R006 evidence_span lacks case-relevant terms |
| mismatched_finding_id | rule_application points to a finding with a different rule_id | False | True | rule_applications[0] R001 does not match finding F2 |
| rule_id_only_trace | trace has rule_id but no real trigger/evidence | False | True | rule_applications[1] R002 has template-like trigger/evidence |

## Conservative Conclusion

- Status: partially_supported
- Finding: Trace verifier rejects the constructed obvious fake/weak evidence cases while accepting the valid control.
- Boundary: Toy adversarial sanity check only. This is not a deep semantic verifier or proof against sophisticated fake evidence.
