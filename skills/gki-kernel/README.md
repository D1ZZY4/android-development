
# gki-kernel

Agent skill and knowledge base for building Generic Kernel Image (GKI) kernels with build.sh or Bazel/Kleaf, including KernelSU-Next integration. Compatible with any AI coding agent that supports the Agent Skills convention.

## What this is

Structured instructions, command references, templates, and scripts for GKI kernel builds: build.sh flow, Bazel/Kleaf flow, KMI/ABI awareness, and KernelSU-Next integration.

## Structure

```
gki-kernel/
  AGENTS.md            AI agent entry point
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/ build.config.template, BUILD.bazel.template
  scripts/  build_gki_kernel.sh, build_gki_ksun.sh
  references/ kernelsu-next-build.md
```

## Requirements

- repo tool
- Kernel build dependencies (binutils, gcc, clang, libelf-dev, etc.)
- For Bazel/Kleaf: tools/bazel (bootstrapped automatically)

## Testing

```bash
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.md.
