# selinux-repair

Agent skill and knowledge base for repairing SELinux policy build failures
and runtime AVC denials on Android devices. Compatible with any AI coding
agent that supports the Agent Skills convention.

## What this is

Structured instructions, command references, Python/shell tooling, templates,
and deep-dive playbooks for SELinux policy repair: source-map resolution,
build error triage, property context collision diagnosis, runtime denial
capture and summarization, and least-privilege patch shapes.

## Structure

```
selinux-repair/
  AGENTS.md            AI agent entry point (workflow, evidence hierarchy)
  SKILL.md             skills.sh entry point
  REFERENCE.md         tool index and evidence hierarchy
  template/  safe_policy_patterns.md, dangerous_patterns_to_reject.md,
                            patch_output_contract.md
  scripts/   Python and shell tools (see REFERENCE.md)
    tests/                  selftest.sh and sample fixture logs
      fixtures/             BoardConfig.mk, property_contexts, .te files
  references/ deep-dive playbooks (start with README.md)
```

## Requirements

- Python 3.8 or later for the SELinux repair tooling
- AOSP build environment for building and verifying policy changes

## Testing

```bash
bash scripts/tests/selftest.sh
find scripts -name "*.py" -exec python3 -m py_compile {} \;
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.md.
