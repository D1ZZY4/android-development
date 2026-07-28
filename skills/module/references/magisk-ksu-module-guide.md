
# Magisk, KernelSU, and KernelSU-Next Module Guide

Use this guide for a systemless package that the root manager installs below `/data/adb/modules/<module-id>/`. The portable base format is shared by Magisk, KernelSU, and KernelSU-Next; KernelSU-family managers add a few lifecycle hooks and an optional WebUI.

## Safety boundary

A module changes the running system through manager-controlled overlays and boot-time scripts. It is not a substitute for evidence-based ROM or SELinux work:

- Do not tell an operator to install, enable, disable, or remove a module on a physical device without their explicit confirmation.
- Do not use a module to hide SELinux denials, make a production domain permissive, or apply a broad policy rule.
- Do not assume that replacing a file through an overlay removes every conflicting OEM component. Verify package paths, libraries, labels, and runtime behavior on the intended build.

## Portable module layout

The ZIP root contains `module.prop` and any optional files directly. Do not put the module inside an extra top-level folder.

```text
<module-id>/
├── module.prop                 required metadata
├── system/                     systemless overlay root
│   └── system_ext/             example overlay partition
│       ├── app/
│       ├── lib64/
│       └── priv-app/
├── system.prop                 optional property overrides
├── sepolicy.rule               optional, minimal SELinux policy additions
├── post-fs-data.sh             optional early hook
├── post-mount.sh               KernelSU / KSU-Next post-overlay hook
├── service.sh                  optional late-start service hook
├── boot-completed.sh           KernelSU / KSU-Next post-boot hook
├── uninstall.sh                optional removal hook
├── action.sh                   optional manager Action button hook
├── zygisk/                     Magisk native libraries by ABI
│   ├── arm64-v8a.so
│   └── armeabi-v7a.so
└── webroot/                    optional KernelSU/KSU-Next WebUI
    └── index.html
```

The manager creates compatibility symlinks for `vendor`, `product`, and `system_ext`; package files under the `system/` tree rather than committing those generated links.

## `module.prop`

`module.prop` is required. The fields below are required unless noted otherwise:

```properties
id=<stable_module_id>
name=<Human-readable module name>
version=<Display version>
versionCode=<monotonically increasing integer>
author=<Author or organization>
description=<One-line purpose>
updateJson=https://example.invalid/update.json
```

Remove `updateJson` when the module has no update endpoint. Keep `id` stable: the manager uses it as the installed module directory name, and changing it makes an update appear to be a separate module.

Start from `template/module/module.prop.template`, then validate the completed directory with:

```bash
bash scripts/module/verify_module.sh <module_dir>
```

## System overlays

Place overlay files below `system/` with their intended logical partition path. For example, a `system_ext` NFC-stack replacement uses paths such as:

```text
system/system_ext/app/NfcNci/
system/system_ext/lib64/<nfc-library>.so
system/system_ext/priv-app/<nfc-package>/
```

This pattern comes from the included Transsion NFC reference material: the replacement includes app, `lib64`, and privileged-app content. Treat it as a package-specific porting task, not a generic copy operation:

1. Inventory the OEM and replacement package names and shared-library
   dependencies.
2. Preserve the target partition layout exactly under `system/`.
3. Resolve any AVC denials through the SELinux Repair workflow before adding
   `sepolicy.rule`.
4. Test a recovery path and conflicts with the stock NFC implementation before
   treating the module as releasable.

A module overlay does not justify deleting files from a physical partition.

## Lifecycle hooks

All shell hooks should begin with `MODDIR="${0%/*}"` rather than a hard-coded install path.

| File | Manager support | Timing and use |
|---|---|---|
| `post-fs-data.sh` | Magisk, KernelSU, KSU-Next | Early and blocking. Use only for quick work required before Zygote. Magisk allows 40 seconds total. |
| `post-mount.sh` | KernelSU, KSU-Next | Runs after module overlays mount. Keep it short. |
| `service.sh` | Magisk, KernelSU, KSU-Next | Runs at late-start service and is non-blocking. Use for regular boot services; wait for full boot if Android framework services are needed. |
| `boot-completed.sh` | KernelSU, KSU-Next | Runs after Android boot completes. Use for post-framework work. |
| `uninstall.sh` | Magisk, KernelSU, KSU-Next | Runs when the manager removes the module. Keep cleanup narrowly scoped to the module's own data. |
| `action.sh` | Magisk, KernelSU, KSU-Next | Runs only when the user deliberately invokes the manager Action button. |

Use `template/module/post-fs-data.sh.template`, `template/module/service.sh.template`, `template/module/post-mount.sh.template`, and `template/module/boot-completed.sh.template` as starting points.

KernelSU sets `KSU=true` in module scripts. The KernelSU late-load sequence loads system properties and overlays before `post-mount.sh`, then starts `service.sh` and `boot-completed.sh` as non-blocking hooks.

## Properties, SELinux, and Zygisk

- **`system.prop`**: manager-loaded system properties. Prefer it for simple module property overrides rather than long early-boot shell logic.
- **`sepolicy.rule`**: one narrowly scoped policy statement per line. Start with an actual denial, label the target correctly, and add the smallest rule necessary. See `template/module/sepolicy.rule.template` and the SELinux Repair domain.
- **`zygisk/`**: Magisk loads native Zygisk libraries named for their ABI, such as `arm64-v8a.so` and `armeabi-v7a.so`. Ship only the ABIs the module supports. An `unloaded` marker makes the libraries incompatible by design.

## KernelSU and KSU-Next extras

KernelSU and KSU-Next recognize the portable module format plus:

- `post-mount.sh` and `boot-completed.sh` lifecycle hooks.
- A WebUI in `webroot/index.html`. Keep it local, clear about privileged actions, and do not expose unreviewed shell execution through the interface. Start from `template/module/webroot-index.html.template`.
- KSU-Next metamodules, which are a separate advanced feature. A metamodule declares `metamodule=1` and may add `metamount.sh`, `metainstall.sh`, and
  `metauninstall.sh`. Use that format only when regular module mounting cannot express the required behavior.

## Release review

Before publishing a module, confirm all of the following:

1. `module.prop` has no placeholders and `versionCode` increases from the
   previous release.
2. The ZIP has no enclosing directory and no development artifacts.
3. Script hooks are short, idempotent, and do not depend on a hard-coded module
   path.
4. Overlay paths match the destination partition exactly.
5. Every `sepolicy.rule` entry has observed evidence and least-privilege
   justification.
6. Zygisk ABIs and `webroot/index.html`, if present, match what the module
   actually supports.