# GKI Kernel Reference Index

Reference playbooks for building Generic Kernel Image (GKI) kernels and
integrating kernel modules or root solutions.

## Docs

- `kernelsu-next-build.md` -- workspace setup, KernelSU-Next integration via
  setup.sh, LTO configuration, and branch compatibility notes for
  build.sh-era GKI trees (android12-5.10, android13-5.10, etc.)

## How GKI domains relate

GKI kernel work frequently crosses into other domains:

- AVB/signature failures after patching: check verified boot state before
  assuming the patch itself is broken (Debug domain).
- AVC denials from a KSU-injected process or module: SELinux Repair domain.
- Vendor module KMI mismatch after updating the generic kernel: back to GKI
  build -- vendor and common trees must match KMI version.
