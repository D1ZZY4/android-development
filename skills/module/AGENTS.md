
# Module -- AI Agent Entry Point

Build Magisk, KernelSU/KSU-Next system-modification modules and AnyKernel3 flashable kernel ZIPs. Includes lifecycle hooks, Zygisk, WebUI, SELinux rules, and GKI vendor_boot cmdline patches.

Activate on: module.prop, Magisk module, KernelSU module, KSU-Next module, Zygisk, systemless overlay, sepolicy.rule, post-fs-data.sh, service.sh, post-mount.sh, boot-completed.sh, webroot, WebUI, AnyKernel3 ZIP.

Read REFERENCE.md for package layouts and manager-specific behavior.

## Hard Constraints

1. No module installation, enabling, disabling, removal, or AnyKernel3 ZIP installation on a physical device without explicit user confirmation.

2. Do not use a module to hide SELinux denials, make a production domain permissive, or apply a broad policy rule. SELinux rules in sepolicy.rule must be justified by real AVC denials.

3. Evidence over guessing. Verify package paths, labels, and runtime behavior.

## Module Workflow

Full package layouts and manager-specific behavior: REFERENCE.md. Templates: template/ (module metadata, lifecycle hooks, SELinux rules, and AnyKernel3 configuration) Validator: scripts/verify_module.sh Deep dives: references/

1. Identify the delivery format before creating files:
   - Magisk / KernelSU / KSU-Next module for systemless overlay, service, property change, Zygisk library, or WebUI.
   - AnyKernel3 ZIP for kernel image, vendor_boot ramdisk adjustment, or boot command-line change.

2. Start from the matching template. A root-manager module needs a valid module.prop at the ZIP root; an AnyKernel3 package needs an accurately configured anykernel.sh, target partition, and slot behavior.

3. Preserve the exact logical destination under a module's system/ overlay. For example, a system_ext NFC replacement keeps its app, lib64, and priv-app paths beneath system/system_ext/. Do not delete physical-partition files to make an overlay work.

4. Choose lifecycle hooks by manager and timing: post-fs-data.sh only for short, early work; service.sh for normal late-start work; post-mount.sh and boot-completed.sh only for KernelSU/KSU-Next behavior.

5. Treat a module sepolicy.rule as a SELinux repair task: collect a real denial, label the object correctly, then add the smallest justified rule.

6. Validate package structure and scripts in the workspace before release. Use scripts/verify_module.sh.

7. Ask for explicit confirmation before any instruction that installs, enables, disables, removes, or applies the finished package on a physical device.

## File and Folder Map

```
skills/module/
  AGENTS.md   AI agent router and workflow
  README.md   human-readable overview
  REFERENCE.md command reference
  SKILL.md    skills.sh entry point
  template/   module.prop.template, lifecycle hook templates, sepolicy.rule.template, anykernel.sh.template, webroot-index.html.template
  scripts/    verify_module.sh
  references/ magisk-ksu-module-guide.md, anykernel3-guide.md, flashable-zip-guide.md
```
