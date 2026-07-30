# Flashable ZIP Creation Guide

This skill does not replace upstream packaging tools. It documents how to build a flashable ZIP for kernels, modules, or system modifications on Transsion/XOS-derived devices.

## Preferred upstream tools

| Tool | Use for | Source |
|---|---|---|
| `AnyKernel3` (osm0sis) | Kernel / vendor_boot / ramdisk flashable ZIPs | https://github.com/osm0sis/AnyKernel3 |
| `ramabondanp/AnyKernel3` | Transsion-focused fork of AnyKernel3 | https://github.com/ramabondanp/AnyKernel3 |
| `ramabondanp/android_tools` | Repo of scripts for building flashable packages | https://github.com/ramabondanp/android_tools |
| Magisk APK | Module ZIPs via Magisk Manager | Built-in to Magisk |
| KernelSU APK | Module ZIPs via KernelSU Manager | Built-in to KernelSU |

When the user asks "how to make a flashable", start from one of the upstream repos above rather than inventing a packaging format.

## mkota pattern

The `android_tools` repo contains `bin/mkota`, a helper script that assembles a flashable recovery package from partition images. The general pattern is:

1. Prepare the payload directory with the expected layout (`anykernel.sh`, `Image.gz-dtb`, `ramdisk/`, `patch/`, etc.).
2. Run `bin/mkota` with device metadata flags or a config file.
3. The output is a flashable ZIP signed with the test/development key.

Do not copy-paste script content from the upstream repo into this skill. Always point to the upstream source, because packaging tools change frequently and the skill would go stale.

## Zipping a release

```bash
zip -r9 UPDATE-<name>.zip * -x .git README.md *placeholder
```

Keep `LICENSE` in the final ZIP. Exclude repo metadata, upstream README, and placeholder files. A filename ending in `-debugging` enables AnyKernel3 diagnostic archive creation during install; use it only for controlled troubleshooting.

## When the user needs a tutorial

If the user asks for a step-by-step tutorial, the correct answer is:

- Point to the upstream repo and README.
- Do not author a new tutorial inside this skill unless the user explicitly provides the content to integrate.
