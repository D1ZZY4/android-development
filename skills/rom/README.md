# rom-build

Agent skill and knowledge base for building custom AOSP/LineageOS ROMs from a
device tree and manifest. Compatible with any AI coding agent that supports the
Agent Skills convention.

## What this is

Structured instructions, command references, templates, and scripts for
ROM builds: repo sync, lunch/breakfast, mka, reading build failures, and
device tree setup.

## Structure

```
rom/
  AGENTS.md            AI agent entry point
  SKILL.md             skills.sh entry point
  REFERENCE.md         command reference
  template/rom/        local_manifest.xml, roomservice.xml, BoardConfig.mk skeleton
  scripts/rom/         build_rom.sh
```

## Requirements

- repo tool
- Standard AOSP host build dependencies for the branch being targeted
- Sufficient disk space (100 GB+ for a full build with ccache)

## Testing

```bash
find scripts -name "*.sh" -exec bash -n {} \;
```

## License

GPL v3. See repository root LICENSE.md.
