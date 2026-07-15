# Automate cross-platform desktop direction

## Approved product

Automate is a local-first desktop application for macOS, Windows, and Linux. It is built with Qt 6 and PySide6, uses the same analysis engine on every operating system, does not use a browser or local web server, and transfers no repository data externally in the current release.

## User workflow

1. Install and open Automate.
2. Choose a local or mounted repository with the operating-system file picker.
3. Run a read-only analysis in the background.
4. Review repository inventory, findings, confidence, and evidence.
5. Review proposed tasks and mark them accepted, rejected, or deferred.
6. Return to locally stored scan history or export a JSON report.

## Packaging

One source tree produces a macOS application, Windows executable bundle, and Linux executable bundle. Each package is built and tested on its target operating system through the included build workflow.

## Implemented build status — 15 July 2026

- Shared Qt 6/PySide6 desktop interface implemented
- Shared read-only analysis and task-planning engine implemented
- Core behavior and headless GUI smoke tests passing
- Reproducible dependency lock created for Python 3.12
- PyInstaller specification implemented for all three desktop operating systems
- Native build matrix defined for macOS, Windows, and Linux
- macOS arm64 application built, launched, ad-hoc signed, and packaged as a verified disk image
- Windows and Linux artifact definitions are ready but require their native build runners before release verification

## Safety boundary

The current release never executes repository scripts, installs repository dependencies, modifies source files, creates branches, opens pull requests, deploys software, or sends repository content to an external model.
