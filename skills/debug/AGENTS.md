# Debug -- AI Agent Entry Point

Evidence-first diagnosis of a misbehaving device or failed build. No
diagnosis without a log line, source reference, and live ADB output to
back it up.

Activate on: crashes, bootloops, misbehaves, live device, tombstones,
logcat, dmesg, kernel panic, ANR, HAL issues, service death, "doesn't boot",
"app keeps crashing", "X isn't working", adb commands.

Read REFERENCE.md for exact debug commands.
Templates: template/debug/ (diagnosis_report.md, log_capture_manifest.md)
Scripts: scripts/debug/capture_logs.sh, verify_device.sh

## Hard Constraints

1. Never run destructive or mutating commands on a connected physical device
   without the user's explicit confirmation. This is especially critical in
   debug -- read-only inspection only.

2. Zero guesswork. Every claim in the diagnosis must be backed by a direct
   quote from a log, device tree or kernel source file, or an adb output
   actually retrieved in this session.

3. No generic advice. Never say "check your manifest" or "make sure
   permissions are correct." Give the exact file path, exact line or snippet,
   and exact command output.

4. Do not assume the environment is already set up.

## Debug Workflow (evidence-first)

### Anti-hallucination rules (non-negotiable)

1. Zero guesswork. Every claim in the diagnosis must be backed by a direct quote
   from a log, device tree or kernel source file, or an adb output actually
   retrieved in this session.
2. No generic advice. Never say "check your manifest" or "make sure permissions
   are correct." Give the exact file path, exact line or snippet, and exact
   command output.
3. Self-audit before diagnosing. Before writing a diagnosis, ask: "Did I actually
   see this, or am I assuming it based on common issues?" If assumed, do not
   include it -- go get more data.
4. If any part of the final diagnosis cannot be backed by hard evidence gathered
   in this session, do not output a soft or partial diagnosis. Output:
   INSUFFICIENT DATA. EXECUTING DEEPER EXPLORATION.
   and repeat the steps below with different parameters.

### Steps (in order)

1. Log acquisition -- scripts/debug/capture_logs.sh (or run commands manually per
   REFERENCE.md): adb logcat -d -b all, adb shell dmesg, tombstones in
   /data/tombstones/. Find the exact error: FATAL EXCEPTION, kernel panic,
   avc: denied, service crash, ANR.

2. Source cross-reference -- locate the failing component in the device tree or
   kernel source: .rc (init), .te (SELinux), .mk/.bp (build), overlay XMLs, or
   kernel driver source. Use grep -rn for the exact name; do not guess the file.

3. Live verification (read-only only) -- confirm the hypothesis on-device using
   adb shell ls -lZ, adb shell getprop | grep, adb shell dumpsys \<service\>,
   adb shell ps -A, adb shell lshal, adb shell cat /sys/...
   Use scripts/debug/verify_device.sh for these.
   Never run a mutating command in this step.

4. Diagnosis -- only once steps 1 through 3 produced real evidence. Output format:
   1. Symptom: [exact log line]
   2. Root Cause: [explanation grounded in evidence]
   3. Evidence from Device: [exact adb output from step 3]
   4. Evidence from Source: [exact file path + line/snippet from step 2]
   5. Proposed Fix: [specific change -- file, line, diff]
   See template/debug/diagnosis_report.md for the full template.

## File and Folder Map

```
skills/debug/
  AGENTS.md              this file -- AI agent router and workflow
  README.md              human-readable overview
  REFERENCE.md           command reference
  SKILL.md               skills.sh entry point
  template/
    debug/               diagnosis_report.md, log_capture_manifest.md
  scripts/
    debug/               capture_logs.sh, verify_device.sh (read-only ADB helper)
  references/
    debug/               (reserved for future guides)
```

## Quick Decision Aid

- User mentions a device that is already flashed and misbehaving (bootloop,
  crash, "doesn't boot", "app keeps crashing", "X isn't working"):
  Debug Workflow -- do not jump to rebuilding until evidence points there.
- User mentions avc: denied, neverallow, sepolicy: see selinux-repair skill.
- User mentions a build failure: route to the relevant build skill
  (rom-build, kernel, gki-kernel) based on the build type.
