# module

Agent skill and knowledge base for building Magisk, KernelSU/KSU-Next
system-modification modules and AnyKernel3 flashable kernel ZIPs. Compatible
with any AI coding agent that supports the Agent Skills convention.

## What this is

Structured instructions, command references, templates, and guides for
system-modification packages: module.prop, lifecycle hooks, system overlays,
SELinux rules, Zygisk, WebUI, and AnyKernel3 kernel ZIPs.

## Structure

```
module/
  AGENTS.md            AI agent entry point
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/     module.prop, lifecycle hooks, sepolicy.rule,
                       AnyKernel3 templates, webroot-index.html
  scripts/      verify_module.sh
  references/   magisk-ksu-module-guide.md, anykernel3-guide.md
```

## Requirements

- Basic shell scripting knowledge (for custom hooks)
- For AnyKernel3: familiarity with target partition layout and boot image format

## Testing

```bash
bash scripts/verify_module.sh <module_dir>
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.md.
