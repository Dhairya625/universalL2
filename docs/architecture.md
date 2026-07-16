# UniversalL2 professional mission-control architecture

## Approved product

Automate is a local-first desktop application for macOS, Windows, and Linux. It is built with Qt 6 and PySide6, uses the same analysis engine on every operating system, does not use a browser or local web server, and transfers no repository data externally in the current release.

## Product workflow

1. Install and open Automate.
2. Choose a local or mounted repository with the operating-system file picker.
3. Run a read-only analysis in the background.
4. Review repository inventory, findings, confidence, and evidence in Analysis Evidence.
5. Inspect generated work in the Suggestion Workspace, including objective, affected files, and required actions.
6. Accept, reject, or defer each suggestion. Only accepted suggestions can be handed to the Developer Agent.
7. Track approved work through queued, in-progress, validation, awaiting-approval, complete, or blocked states.
8. Return to locally stored activity or export the complete JSON report.

## Component boundaries

| Component | Responsibility | Current implementation |
| --- | --- | --- |
| Repository connector | Selects a local or mounted repository without executing it | Native operating-system folder picker |
| Analysis engine | Inventories files and produces evidence-backed findings | Deterministic Python engine in `automate_core.engine` |
| Suggestion planner | Converts findings into reviewable engineering work | Proposed tasks embedded in each scan report |
| Approval gateway | Prevents unapproved work from reaching development | `TaskReviewState` plus guarded handoff |
| Developer orchestration | Maintains queue, stage transitions, actions, files, and activity | `automate_core.workflow` and Developer Agent panel |
| Execution adapter | Will connect approved work to a self-hosted coding agent | Deliberately disconnected in this version |
| Local persistence | Retains scans, decisions, handoffs, and activity | Versioned JSON reports in OS application data |

## State model

Suggestions begin as `proposed` and require an explicit human decision. An `accepted` suggestion can move to `queued`; developer work then follows validated transitions through `in_progress`, `validation`, `awaiting_approval`, and `complete`. `blocked` and return-to-development transitions are explicit. Invalid transitions raise a workflow error rather than silently changing state.

## Interface structure

- **Workspace shell** — compact dark sidebar, breadcrumb command bar, `Cmd/Ctrl+K` command menu, and `Alt+1…5` direct navigation.
- **Repository** — connection, scan controls, repository health, and summary metrics.
- **Analysis Evidence** — finding severity, confidence, remediation, and source evidence.
- **Suggestions** — human review, required actions, affected paths, and developer handoff.
- **Developer Agent** — queue, current work details, operational state, validation, approval, and activity.
- **Activity** — locally retained scan and workflow history.

The visual system is Linear-inspired rather than a branded clone: it uses UniversalL2 naming, original symbols, native Qt controls, compact issue-style rows, restrained borders, and a distinct violet accent.

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

The current release never executes repository scripts, installs repository dependencies, modifies source files, creates branches, opens pull requests, deploys software, or sends repository content to an external model. The developer panel records controlled workflow state only; the execution adapter is visibly marked as disconnected.
