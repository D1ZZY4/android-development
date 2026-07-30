
# port-rom

Agent skill and knowledge base for adapting stock or OEM firmware (Transsion/XOS and others) to a custom ROM base. Compatible with any AI coding agent that supports the Agent Skills convention.

## What this is

Structured instructions, command references, templates, and playbooks for ROM porting: image extraction, partition strategy, vendor 64-bit conversion, OEM file removals, and boot fixes.

## Structure

```
port-rom/
  AGENTS.md      AI agent entry point
  SKILL.md       skills.sh entry point
  REFERENCE.md   command reference
  template/      port_checklist.md, props_fragment.md
  scripts/       check_port_images.sh
  references/    partition-strategy.md, transsion-xos-boot-fixes.md,
                 nfc-oos-post-port.md, dolby-atmos-fix.md,
                 misound-dolby-replacement.md, signing-guide.md,
                 gsi-port-guide.md
  assets/        bundled porting artifacts
    apps/        APK packages
      faceid/    XOS 15 FaceID fix for Flamescion Project on X15
    libs/        .so blobs / HAL libraries (empty by default)
```

## Requirements

- adb and fastboot on PATH
- erofs-utils (for erofs images on Android 12+)
- Standard image inspection tools (mount, loop devices)

## Testing

```bash
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.
