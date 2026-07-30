
# Module -- Reference

Use this domain for a Magisk, KernelSU, or KernelSU-Next systemless module, or for an AnyKernel3 flashable kernel ZIP.

## Module guides

| Resource | Use it for |
|---|---|
| `references/magisk-ksu-module-guide.md` | module.prop, system/ overlays, boot hooks, Zygisk, sepolicy.rule, KernelSU WebUI |
| `references/anykernel3-guide.md` | anykernel.sh, GKI vendor_boot, slots, ramdisk edits, cmdline patches |
| `template/` | Copyable module metadata, lifecycle hooks, SELinux rule guardrails, GKI AnyKernel3 template |
| `scripts/verify_module.sh` | Structural validation for a completed module directory |

## Root-manager module decision table

| Need | Package location / hook | Notes |
|---|---|---|
| Required metadata | module.prop | Stable id, user-facing version, increasing versionCode |
| File replacement / overlay | system/<partition path>/... | Preserve exact destination partition path |
| Simple system property override | system.prop | Prefer over a long early-boot script |
| Fast pre-Zygote work | post-fs-data.sh | Blocking; keep it short |
| Usual background boot work | service.sh | Late-start, non-blocking |
| Work after overlays mount | post-mount.sh | KernelSU / KSU-Next only |
| Work after Android boot | boot-completed.sh | KernelSU / KSU-Next only |
| Native process injection | zygisk/<abi>.so | Magisk; ship only supported ABI libraries |
| Manager web interface | webroot/index.html | KernelSU / KSU-Next WebUI |
| Extra policy access | sepolicy.rule | Only narrow rule justified by real AVC denial |

## Module validation

```bash
bash scripts/verify_module.sh <module_dir>
```

The validator checks required metadata, placeholder values, id and versionCode format, shell syntax, system overlay contents, optional WebUI entry point, and flags policy/Zygisk content for review.

## AnyKernel3 GKI pattern

For a GKI device using vendor_boot, start from `template/anykernel.sh.template` and follow `references/anykernel3-guide.md`.

## Safety

- Do not use root modules or AnyKernel3 to bypass a recovery plan, hide AVC denials, or write generic SELinux permissions.
- Obtain explicit user confirmation before any physical-device installation.
