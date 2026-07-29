
# ROM Build -- AI Agent Entry Point

Build custom AOSP/LineageOS-derived ROMs from a device tree and manifest.

Activate on: device tree, repo sync/manifest, lunch/breakfast, mka/mka bacon, AndroidProducts.mk, BoardConfig.mk, .mk/.bp files, ROM build failures, build-environment setup, local_manifest.xml, roomservice.xml, device tree won't compile.

Read REFERENCE.md for exact command flags and paths before running any build command. Prefer this skill over general coding help whenever AOSP, a device tree, or ROM build failure is involved.

## Hard Constraints

1. Never run destructive or mutating commands on a connected physical device without the user's explicit confirmation. This includes: fastboot flash, fastboot erase, adb reboot bootloader, dd to any device node, mkfs, or anything that writes to a partition. Building an image and writing files inside the workspace (device tree, kernel source, out/ directory) is fine and expected.

2. Evidence over guessing. Never state a root cause you did not actually see in a log, source file, or command output.

3. Do not assume the toolchain or environment is already set up. Check for build/envsetup.sh, .repo/, existing out/ dirs before assuming a repo is initialized. Ask or check rather than guessing paths.

4. Long-running builds: repo sync and full ROM builds can take a long time and produce huge logs. Run them in the background where the environment supports it, and tail or grep the log rather than dumping it all into the response.

## ROM Build Workflow

Full command detail and common failure patterns: REFERENCE.md. Templates: template/ (local_manifest.xml, roomservice.xml, BoardConfig.mk skeleton) Script: scripts/build_rom.sh

1. Confirm workspace: is .repo/ present (already synced) or does this need repo init first?
2. Set up manifest (main + local_manifests for device, vendor, and kernel trees). See template/local_manifest.xml.
3. source build/envsetup.sh, then lunch \<target\> (or breakfast \<codename\> for LineageOS).
4. Build with mka bacon / brunch (LineageOS) or mka \<target\> (AOSP). Background the build and monitor for the first error rather than waiting for full completion.
5. On build failure: grep the log for the first error:/FAILED: line, not the last -- later errors are usually cascades from the first real failure.

## File and Folder Map

```
skills/rom/
  AGENTS.md   AI agent router and workflow
  README.md   human-readable overview
  REFERENCE.md command reference
  SKILL.md    skills.sh entry point
  template/   local_manifest.xml, roomservice.xml, BoardConfig.mk skeleton
  scripts/    build_rom.sh
  references/ reserved for future guides
```

## Quick Decision Aid

- User mentions repo sync, lunch, breakfast, mka, or "ROM won't compile": ROM Build workflow.
- User mentions porting a ROM, extracting images from stock firmware: see port-rom skill.
- User mentions a device that is already flashed and misbehaving: see debug skill.
- User mentions avc: denied, neverallow, sepolicy: see selinux-repair skill.
