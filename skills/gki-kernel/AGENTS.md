# GKI Kernel Build -- AI Agent Entry Point

Build Generic Kernel Image (GKI) kernels from Google's common tree with
build/build.sh or Bazel/Kleaf. Includes KernelSU-Next integration.

Activate on: build.config, tools/bazel, common/, GKI, KMI/ABI, vendor_boot,
android-kernel, KernelSU-Next, KSU-Next, KSUN, build.sh GKI, Kleaf,
vendor_boot kernel.

Read REFERENCE.md for exact command flags before running any build command.
For legacy (non-GKI/monolithic) kernels, use the kernel skill instead.

## Hard Constraints

1. Never run destructive or mutating commands on a connected physical device
   without the user's explicit confirmation.

2. Evidence over guessing. Never state a root cause you did not actually see
   in a log, source file, or command output.

3. Do not assume the toolchain or environment is already set up. Check for
   build/build.sh, tools/bazel, or existing build.config files first.

4. Long-running builds: background the build and tail/grep the log.

## GKI Kernel Build Workflow

Full command detail and failure modes: REFERENCE.md.
Templates: template/gki-kernel/ (build.config.template, BUILD.bazel.template)
Scripts: scripts/gki-kernel/build_gki_kernel.sh, build_gki_ksun.sh

GKI kernels split the kernel into a generic core (Image) built from Google's
common tree and vendor modules built separately and loaded at runtime. Mixing
legacy single-Makefile build habits into a GKI tree is a common source of
confusion.

1. Confirm which GKI generation: GKI 1.0 vs GKI 2.0 (module signing,
   vendor_boot vs boot, KernelSU/KSU integration if present). Check
   BUILD.bazel or build.config.* files for hints.
2. Use build/build.sh (older trees) or tools/bazel run //... (newer AOSP
   kernel trees with Kleaf). Do not hand-roll make flags for these unless the
   tree explicitly still supports it.
3. Watch for ABI or symbol issues (abi_gki_*.xml/.stg files, KMI mismatches).
   These are GKI-specific failure modes not present in legacy kernels.

### KernelSU-Next integration (build.sh-era trees)

KernelSU-Next integrates into a GKI tree via the official setup.sh script.
See REFERENCE.md for the full commands and references/gki-kernel/kernelsu-next-build.md
for branch compatibility and common post-integration failures.

## File and Folder Map

```
skills/gki-kernel/
  AGENTS.md              this file -- AI agent router and workflow
  README.md              human-readable overview
  REFERENCE.md           command reference
  SKILL.md               skills.sh entry point
  template/
    gki-kernel/          build.config.template, BUILD.bazel.template
  scripts/
    gki-kernel/          build_gki_kernel.sh, build_gki_ksun.sh
  references/
    gki-kernel/          kernelsu-next-build.md
```

## Quick Decision Aid

- User mentions build.config, tools/bazel, common/, GKI, KMI/ABI, or
  vendor_boot: GKI Kernel Build workflow.
- User mentions KernelSU-Next, KSU-Next, KSUN, integrating KSU into a GKI
  tree, or build.sh with a setup.sh patch script: GKI Kernel Build workflow
  -- see references/gki-kernel/kernelsu-next-build.md.
- User mentions defconfig, Image.gz-dtb, make ARCH=arm64 (single monolithic
  kernel): see kernel skill.
- User mentions anykernel.sh, module.prop, or a flashable kernel ZIP:
  see module skill.
- User mentions avc: denied from a KSU-injected process: see selinux-repair skill.
