# Automate Desktop

UniversalL2 Automate is local-first desktop software for repository analysis, development-gap detection, human-reviewed suggestions, and controlled developer-agent handoff. The official application uses Qt 6/PySide6 and one shared source codebase for macOS, Windows, and Linux. It is not a browser application and does not start a local web server.

## Current capabilities

- Native desktop window and operating-system file picker
- Read-only local repository analysis
- Python, TypeScript, and JavaScript inventory and initial analyzers
- Evidence, severity, confidence, and analyzer provenance
- Deterministic proposed tasks with acceptance criteria
- Human decisions: proposed, accepted, rejected, or deferred
- Professional suggestion workspace with objectives, affected files, and required actions
- Controlled handoff of accepted suggestions to a dedicated developer-agent queue
- Developer work stages: queued, in progress, validation, awaiting approval, complete, or blocked
- Locally recorded developer workflow activity and mandatory approval gates
- Local scan history and JSON export
- External AI and network transfer disabled

The developer panel is currently an orchestration and status foundation. Its execution adapter is intentionally disconnected: this version does not claim to edit code or run an AI developer. A future adapter can connect a self-hosted developer agent without changing the approval and persistence model.

## Development

```bash
uv sync --extra build
uv run python -m unittest discover -s tests -v
uv run automate-desktop
```

## Build an operating-system package

Run this command on the operating system being packaged:

```bash
uv run python scripts/build_release.py
```

Outputs:

- macOS: `.dmg` containing `Automate.app`
- Windows: `.zip` containing the standalone `Automate.exe` application folder
- Linux: `.tar.gz` containing the standalone Automate application folder

GitHub Actions is configured to compile and test all three packages on their native operating systems. Production public releases additionally require platform signing: Apple Developer ID/notarization, Windows Authenticode, and optional Linux repository signing.
