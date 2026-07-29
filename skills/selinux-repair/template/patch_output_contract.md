
# SELinux patch output contract

When proposing a SELinux fix, the response must include all 8 fields below. Don't skip straight to a patch without them — this mirrors the evidence-first discipline used in the general Debug Workflow (`template/debug/diagnosis_report.md`), adapted for policy-specific repairs.

---

**1. Failure class** [One of: build/verifier failure, labeling failure, domain transition failure, partition ownership failure, missing public API/private symbol boundary failure, real permission gap, debug-only/test-only access that shouldn't be in production policy]

**2. First evidence line** [Exact log line or file/line — the *first* deterministic failure, not the last cascading one]

**3. Root cause hypothesis** [Concise and falsifiable — must be checkable against the evidence above]

**4. Files to edit** [Exact candidate paths, resolved via the policy source map — see references/policy-source-map.md]

**5. Patch shape** [Labels / types / macros / allow rules / init / property changes — reference template/safe_policy_patterns.md for the shape]

**6. Why this is safe** [Label-first reasoning, least-privilege, partition-correct — confirm it doesn't match anything in template/dangerous_patterns_to_reject.md]

**7. Validation commands** [Exact rebuild and runtime checks — e.g. `m sepolicy_tests`, `scripts/verify_policy_artifacts.sh out/target/product/<device>`]

**8. What not to do** [Explicitly name the broad-allow/permissive/dontaudit shortcut that was considered and rejected, and why]

---

Never output a naked `audit2allow` blob as the final answer — convert it into a reviewed patch plan using this contract.
