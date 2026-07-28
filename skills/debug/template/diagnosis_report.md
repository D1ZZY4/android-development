# Diagnosis report template

Fill this in only after completing Steps 1-3 of the Debug Workflow in
AGENTS.md with real evidence. Every bracketed field must come from an
actual log line, source file, or adb command output gathered in this
session — never fill a field with a plausible-sounding guess.

---

**1. Symptom**
[Exact log line showing the crash/error — copy verbatim from logcat/dmesg/tombstone output]

**2. Root Cause**
[Explanation of why it failed, grounded only in what was found in steps 1-2]

**3. Evidence from Device**
[Exact output from the read-only live verification command run in step 3 — e.g. `adb shell dumpsys ...` output, `adb shell getprop | grep ...` output]

**4. Evidence from Source**
[Exact file path + line number/snippet from the device tree or kernel source that causes the mismatch/issue]

**5. Proposed Fix**
[Specific code/config change — file, line, and the actual diff or replacement snippet]

---

If any field above cannot be filled with real evidence gathered this
session, do not submit this report. Output instead:

```
INSUFFICIENT DATA. EXECUTING DEEPER EXPLORATION.
```

and go back to log acquisition / source cross-reference / live
verification with different parameters.
