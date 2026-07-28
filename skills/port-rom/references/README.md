
# Port ROM Reference Index

Reference playbooks for porting an existing Android ROM build to a new device, or adapting a closed/device-specific ROM (such as a stock Transsion/XOS build) into a custom-ROM-compatible base.

## First-read docs

1. `partition-strategy.md` -- which images to extract, how to handle extra
   vendor partitions, and the vendor 64-bit conversion approach.
2. `transsion-xos-boot-fixes.md` -- known boot blockers and prop fixes for XOS 16
   (Transsion) ROM ports: required file removals, init.rc edits, and prop table.

## How port-rom relates to the other domains

A ROM port almost always crosses multiple domains before it boots cleanly. Use these references for the port-specific extraction and adaptation steps, then hand off to the relevant skill domain:

- Build failures after integrating extracted blobs or props: ROM Build domain.
- Kernel not booting or missing drivers: Kernel Build (legacy) or GKI domain.
- AVC denials from ported vendor blobs: SELinux Repair domain.
- Device misbehaving after first boot: Debug domain.
