# port-rom

Agent skill and knowledge base for adapting stock or OEM firmware (Transsion/
XOS and others) to a custom ROM base. Compatible with any AI coding agent that
supports the Agent Skills convention.

## What this is

Structured instructions, command references, templates, and playbooks for ROM
porting: image extraction, partition strategy, vendor 64-bit conversion, OEM
file removals, and boot fixes.

## Structure

```
port-rom/
  AGENTS.md            AI agent entry point
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/port-rom/   port_checklist.md, props_fragment.md
  scripts/port-rom/    check_port_images.sh
  references/port-rom/ partition-strategy.md, transsion-xos-boot-fixes.md
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

GPL v3. See repository root LICENSE.md.
