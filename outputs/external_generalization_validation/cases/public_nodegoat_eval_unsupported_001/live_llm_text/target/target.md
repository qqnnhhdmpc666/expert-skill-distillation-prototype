Task: Read-only defensive review of a public OWASP NodeGoat code excerpt. This task family is outside the current secure_code_review capability set.

Snippet:
/*jslint evil: true */
        // Insecure use of eval() to parse inputs
        const preTax = eval(req.body.preTax);
        const afterTax = eval(req.body.afterTax);
        const roth = eval(req.body.roth);

Requested output schema: capability_id, evidence_span, recommended_fix