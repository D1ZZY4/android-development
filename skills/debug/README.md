
# debug

Agent skill and knowledge base for evidence-first diagnosis of Android devices, ROMs, and builds. Compatible with any AI coding agent that supports the Agent Skills convention.

## What this is

Structured instructions, command references, templates, and scripts for debugging Android devices: log acquisition, source cross-reference, read-only live verification, and structured diagnosis reporting -- all grounded in evidence gathered in the current session.

## Structure

```
debug/
  AGENTS.md            AI agent entry point (anti-hallucination rules, workflow)
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/      diagnosis_report.md, log_capture_manifest.md
  scripts/       capture_logs.sh, verify_device.sh (read-only ADB helper)
  references/    reserved for future guides
```

## Requirements

- adb on PATH
- A connected Android device (for live diagnosis)

## Testing

```bash
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.
