# kernel-build

Agent skill and knowledge base for building legacy/monolithic device kernels
(non-GKI). Compatible with any AI coding agent that supports the Agent Skills
convention.

## What this is

Structured instructions, command references, templates, and scripts for legacy
kernel builds: defconfig, make, boot image packaging, and AnyKernel3 packaging
for non-GKI devices.

## Structure

```
kernel/
  AGENTS.md            AI agent entry point
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/kernel/     defconfig_fragment.md, anykernel_notes.md
  scripts/kernel/      build_kernel.sh
```

## Requirements

- Cross-compiler toolchain (aarch64-linux-android- or aarch64-linux-gnu-)
- Standard kernel build dependencies

## Testing

```bash
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.md.
