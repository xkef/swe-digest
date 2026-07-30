# Apple platforms, Linux, and the kernel

## Apple platforms checks

Primary sources:

- Swift.org blog and Swift Evolution proposals.
- Apple Developer news and release notes.
- Xcode release notes, including agentic coding features.
- Foundation Models and on-device model framework documentation.
- The Eclectic Light Company for macOS and Darwin internals.

Selection rules:

- Capture version, release date, primary source, and the concrete API or
  behavior change.
- Cover Swift and SwiftUI, the Swift toolchain, Apple Silicon, and macOS
  internals.
- Keep the Swift language itself in `Languages and runtimes`. SDK, tooling, and
  platform changes go here.

## Linux and kernel checks

Primary sources:

- LWN.net.
- kernel.org release announcements and the stable tree.
- Phoronix for release coverage and benchmarks.
- Rust for Linux project updates.

Selection rules:

- Capture kernel version, release or merge-window date, primary source, and the
  concrete change.
- Cover scheduler, io_uring, eBPF, filesystems, memory management, cgroups, and
  security hardening.
- Keep Linux desktop tooling such as Wayland and shells in `Developer tools`.
