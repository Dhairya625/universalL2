from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QComboBox, QDialog, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QStackedWidget, QStatusBar, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)

from automate_core import (
    AgentWorkState, ScanReport, TaskReviewState, WorkflowError, handoff_to_developer,
    next_agent_actions, scan_repository, transition_agent_work,
)
from automate_core.models import Finding, ProposedTask
from automate_desktop.storage import HistoryStore


SEVERITY_COLORS = {
    "critical": "#DC2626", "high": "#EA580C", "medium": "#CA8A04",
    "low": "#2563EB", "informational": "#64748B",
}


class ScanWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, repository: str) -> None:
        super().__init__()
        self.repository = repository

    def run(self) -> None:
        try:
            self.completed.emit(scan_repository(self.repository))
        except Exception as exc:  # surfaced to the user rather than crashing the UI
            self.failed.emit(str(exc))


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(9)
    return frame, layout


def title_block(title: str, subtitle: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    heading = QLabel(title)
    heading.setObjectName("PageTitle")
    body = QLabel(subtitle)
    body.setObjectName("PageSubtitle")
    body.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(body)
    return widget


class OverviewPage(QWidget):
    choose_requested = Signal()
    scan_requested = Signal()
    export_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(18)

        top = QHBoxLayout()
        top.addWidget(title_block("Repository intelligence", "Understand development gaps and convert evidence into reviewable engineering work."), 1)
        self.export_button = QPushButton("Export report")
        self.export_button.setObjectName("Secondary")
        self.export_button.clicked.connect(self.export_requested)
        self.export_button.hide()
        top.addWidget(self.export_button, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top)

        repository_card, repository_layout = card()
        row = QHBoxLayout()
        icon = QLabel("◈")
        icon.setStyleSheet("font-size: 32px; color: #4F46E5; padding-right: 8px;")
        row.addWidget(icon)
        repo_text = QVBoxLayout()
        self.repo_name = QLabel("No repository selected")
        self.repo_name.setObjectName("SectionTitle")
        self.repo_path = QLabel("Choose a local repository to begin a read-only analysis.")
        self.repo_path.setObjectName("Muted")
        self.repo_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        repo_text.addWidget(self.repo_name)
        repo_text.addWidget(self.repo_path)
        row.addLayout(repo_text, 1)
        choose = QPushButton("Choose…")
        choose.setObjectName("Secondary")
        choose.clicked.connect(self.choose_requested)
        self.scan_button = QPushButton("Start analysis")
        self.scan_button.setObjectName("Primary")
        self.scan_button.setEnabled(False)
        self.scan_button.clicked.connect(self.scan_requested)
        row.addWidget(choose)
        row.addWidget(self.scan_button)
        repository_layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        repository_layout.addWidget(self.progress)
        outer.addWidget(repository_card)

        self.metrics = QGridLayout()
        self.metric_labels: dict[str, QLabel] = {}
        for index, (key, label, color) in enumerate((
            ("files", "Files analyzed", "#4F46E5"),
            ("findings", "Findings", "#EA580C"),
            ("tasks", "Proposed tasks", "#2563EB"),
            ("accepted", "Accepted", "#16A34A"),
        )):
            metric_card, metric_layout = card()
            caption = QLabel(label)
            caption.setObjectName("CardLabel")
            value = QLabel("—")
            value.setObjectName("MetricValue")
            value.setStyleSheet(f"color: {color};")
            self.metric_labels[key] = value
            metric_layout.addWidget(caption)
            metric_layout.addWidget(value)
            self.metrics.addWidget(metric_card, 0, index)
        outer.addLayout(self.metrics)

        details = QHBoxLayout()
        self.languages_card, self.languages_layout = card()
        self.severity_card, self.severity_layout = card()
        details.addWidget(self.languages_card, 1)
        details.addWidget(self.severity_card, 1)
        outer.addLayout(details, 1)
        self._show_empty_details()

    def set_repository(self, path: str) -> None:
        self.repo_name.setText(Path(path).name)
        self.repo_path.setText(path)
        self.scan_button.setEnabled(True)

    def set_scanning(self, scanning: bool) -> None:
        self.progress.setVisible(scanning)
        self.scan_button.setEnabled(not scanning)
        self.scan_button.setText("Analyzing…" if scanning else "Start analysis")

    def show_report(self, report: ScanReport) -> None:
        self.export_button.show()
        self.metric_labels["files"].setText(str(report.inventory.file_count))
        self.metric_labels["findings"].setText(str(len(report.findings)))
        self.metric_labels["tasks"].setText(str(len(report.proposed_tasks)))
        self.metric_labels["accepted"].setText(str(sum(task.review_state == TaskReviewState.ACCEPTED for task in report.proposed_tasks)))
        self._clear_layout(self.languages_layout)
        self._clear_layout(self.severity_layout)
        heading = QLabel("Repository languages")
        heading.setObjectName("SectionTitle")
        self.languages_layout.addWidget(heading)
        for language, count in sorted(report.inventory.languages.items(), key=lambda item: item[1], reverse=True):
            row = QLabel(f"{html.escape(language)}  ·  {count}")
            row.setObjectName("Muted")
            self.languages_layout.addWidget(row)
        self.languages_layout.addStretch()
        heading = QLabel("Finding severity")
        heading.setObjectName("SectionTitle")
        self.severity_layout.addWidget(heading)
        for severity in ("critical", "high", "medium", "low", "informational"):
            count = sum(finding.severity == severity for finding in report.findings)
            row = QLabel(f"●  {severity.capitalize()}  ·  {count}")
            row.setStyleSheet(f"color: {SEVERITY_COLORS[severity]};")
            self.severity_layout.addWidget(row)
        self.severity_layout.addStretch()

    def _show_empty_details(self) -> None:
        for layout, title in ((self.languages_layout, "Repository languages"), (self.severity_layout, "Finding severity")):
            heading = QLabel(title)
            heading.setObjectName("SectionTitle")
            layout.addWidget(heading)
            body = QLabel("Run an analysis to see this information.")
            body.setObjectName("Muted")
            layout.addWidget(body)
            layout.addStretch()

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class FindingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(16)
        outer.addWidget(title_block("Findings", "Inspect repository evidence, confidence, and remediation guidance."))
        filter_row = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(["All severities", "Critical", "High", "Medium", "Low", "Informational"])
        self.filter.currentTextChanged.connect(self._apply_filter)
        self.count = QLabel("0 findings")
        self.count.setObjectName("Muted")
        filter_row.addWidget(self.filter)
        filter_row.addStretch()
        filter_row.addWidget(self.count)
        outer.addLayout(filter_row)
        splitter = QSplitter()
        self.list = QListWidget()
        self.list.setMinimumWidth(350)
        self.list.currentItemChanged.connect(self._show_finding)
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(False)
        self.detail.setHtml(self._empty_html())
        splitter.addWidget(self.list)
        splitter.addWidget(self.detail)
        splitter.setSizes([380, 620])
        outer.addWidget(splitter, 1)
        self.findings: tuple[Finding, ...] = ()

    def show_report(self, report: ScanReport) -> None:
        self.findings = report.findings
        self._apply_filter()

    def _apply_filter(self) -> None:
        selected = self.filter.currentText().lower()
        filtered = self.findings if selected == "all severities" else tuple(finding for finding in self.findings if finding.severity == selected)
        self.list.clear()
        for finding in filtered:
            item = QListWidgetItem(f"{finding.severity.upper()}    {finding.title}\n{finding.evidence[0].location}")
            item.setData(Qt.ItemDataRole.UserRole, finding.id)
            item.setForeground(QColor(SEVERITY_COLORS[finding.severity]))
            self.list.addItem(item)
        self.count.setText(f"{len(filtered)} findings")
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.detail.setHtml(self._empty_html())

    def _show_finding(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if not current:
            return
        finding_id = current.data(Qt.ItemDataRole.UserRole)
        finding = next((item for item in self.findings if item.id == finding_id), None)
        if not finding:
            return
        evidence = "".join(
            f"<div class='evidence'><b><code>{html.escape(item.location)}</code></b><p>{html.escape(item.detail)}</p>"
            + (f"<pre>{html.escape(item.excerpt)}</pre>" if item.excerpt else "") + "</div>"
            for item in finding.evidence
        )
        self.detail.setHtml(f"""
        <style>
          body {{ font-family: -apple-system, Segoe UI, sans-serif; color: #172033; padding: 18px; }}
          h1 {{ font-size: 25px; margin-bottom: 4px; }} h2 {{ font-size: 15px; margin-top: 24px; }}
          .badge {{ color: {SEVERITY_COLORS[finding.severity]}; font-weight: 700; font-size: 11px; }}
          .muted {{ color: #64748B; }} .evidence {{ border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin: 9px 0; }}
          pre {{ background: #F1F5F9; border-radius: 6px; padding: 10px; white-space: pre-wrap; }} code {{ font-family: monospace; }}
        </style>
        <div class='badge'>{finding.severity.upper()} · {finding.confidence:.0%} CONFIDENCE</div>
        <h1>{html.escape(finding.title)}</h1><div class='muted'><code>{finding.id}</code></div>
        <h2>Why this matters</h2><p>{html.escape(finding.why_it_matters)}</p>
        <h2>Suggested direction</h2><p>{html.escape(finding.remediation)}</p>
        <h2>Confidence</h2><p>{html.escape(finding.confidence_explanation)}</p>
        <h2>Evidence</h2>{evidence}
        """)

    @staticmethod
    def _empty_html() -> str:
        return "<div style='font-family:sans-serif;color:#64748B;padding:30px'><h2>No finding selected</h2><p>Analyze a repository or select a finding from the list.</p></div>"


class TasksPage(QWidget):
    decision_changed = Signal(str, str)
    handoff_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(16)
        outer.addWidget(title_block("Suggestion workspace", "Review analysis-backed suggestions and explicitly approve work before it reaches the developer agent."))
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Priority", "Suggestion", "Affected paths", "Complexity", "Review", "Developer"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._show_selected)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        detail_frame, detail_layout = card()
        detail_top = QHBoxLayout()
        detail_title = QLabel("Suggestion details")
        detail_title.setObjectName("SectionTitle")
        detail_top.addWidget(detail_title)
        detail_top.addStretch()
        self.handoff_button = QPushButton("Send to developer agent")
        self.handoff_button.setObjectName("Primary")
        self.handoff_button.setEnabled(False)
        self.handoff_button.clicked.connect(self._request_handoff)
        detail_top.addWidget(self.handoff_button)
        detail_layout.addLayout(detail_top)
        self.detail = QTextBrowser()
        self.detail.setObjectName("DetailPanel")
        self.detail.setHtml("<p style='color:#64748B'>Select a suggestion to inspect its objective and required actions.</p>")
        detail_layout.addWidget(self.detail)
        splitter.addWidget(detail_frame)
        splitter.setSizes([430, 240])
        outer.addWidget(splitter, 1)
        self.tasks: list[ProposedTask] = []
        self.current_task_id: str | None = None

    def show_report(self, report: ScanReport) -> None:
        selected_id = self.current_task_id
        self.tasks = report.proposed_tasks
        self.table.setRowCount(len(report.proposed_tasks))
        for row, task in enumerate(report.proposed_tasks):
            priority = QTableWidgetItem(task.priority.upper())
            priority.setForeground(QColor("#4F46E5"))
            task_item = QTableWidgetItem(f"{task.title}\n{task.objective}")
            task_item.setData(Qt.ItemDataRole.UserRole, task.id)
            paths = QTableWidgetItem("\n".join(task.affected_paths))
            complexity = QTableWidgetItem(task.complexity)
            self.table.setItem(row, 0, priority)
            self.table.setItem(row, 1, task_item)
            self.table.setItem(row, 2, paths)
            self.table.setItem(row, 3, complexity)
            decision = QComboBox()
            values = [state.value for state in TaskReviewState]
            decision.addItems([value.capitalize() for value in values])
            decision.setCurrentIndex(values.index(str(task.review_state)))
            decision.setEnabled(str(task.agent_state) == AgentWorkState.UNASSIGNED)
            decision.currentTextChanged.connect(lambda text, task_id=task.id: self.decision_changed.emit(task_id, text.lower()))
            self.table.setCellWidget(row, 4, decision)
            agent_state = QTableWidgetItem(str(task.agent_state).replace("_", " ").title())
            agent_state.setForeground(QColor("#0F766E" if str(task.agent_state) != AgentWorkState.UNASSIGNED else "#94A3B8"))
            self.table.setItem(row, 5, agent_state)
            self.table.setRowHeight(row, 70)
            if task.id == selected_id:
                self.table.selectRow(row)
        if self.table.rowCount() and not self.table.selectedItems():
            self.table.selectRow(0)

    def _selected_task(self) -> ProposedTask | None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 1)
        task_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next((task for task in self.tasks if task.id == task_id), None)

    def _show_selected(self) -> None:
        task = self._selected_task()
        if not task:
            self.current_task_id = None
            self.handoff_button.setEnabled(False)
            return
        self.current_task_id = task.id
        paths = "".join(f"<li><code>{html.escape(path)}</code></li>" for path in task.affected_paths)
        criteria = "".join(f"<li>{html.escape(item)}</li>" for item in task.acceptance_criteria)
        self.detail.setHtml(f"""
        <style>body {{ font-family: -apple-system, Segoe UI, sans-serif; color:#172033; }}
        h2 {{ font-size:14px; margin-top:16px; }} .meta {{ color:#64748B; }}
        code {{ background:#F1F5F9; padding:2px 5px; border-radius:4px; }}</style>
        <b>{html.escape(task.title)}</b><p class='meta'>{html.escape(task.objective)}</p>
        <h2>Required actions</h2><ol>{criteria}</ol><h2>Affected paths</h2><ul>{paths}</ul>
        """)
        can_handoff = str(task.review_state) == TaskReviewState.ACCEPTED and str(task.agent_state) == AgentWorkState.UNASSIGNED
        self.handoff_button.setEnabled(can_handoff)
        self.handoff_button.setText("Send to developer agent" if str(task.agent_state) == AgentWorkState.UNASSIGNED else "Already in developer workflow")

    def _request_handoff(self) -> None:
        task = self._selected_task()
        if task:
            self.handoff_requested.emit(task.id)


class DeveloperAgentPage(QWidget):
    state_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(16)
        outer.addWidget(title_block("Developer agent", "Track approved work, required actions, validation, and human approval in one operational panel."))

        notice = QLabel("Execution adapter: not connected  ·  This panel tracks controlled handoffs and status; it does not modify repository files.")
        notice.setObjectName("Notice")
        notice.setWordWrap(True)
        outer.addWidget(notice)

        metrics = QHBoxLayout()
        self.metric_labels: dict[str, QLabel] = {}
        for key, label in (("queued", "Queued"), ("active", "Active work"), ("approval", "Awaiting approval"), ("complete", "Complete")):
            metric, metric_layout = card()
            caption = QLabel(label)
            caption.setObjectName("CardLabel")
            value = QLabel("0")
            value.setObjectName("MetricValue")
            self.metric_labels[key] = value
            metric_layout.addWidget(caption)
            metric_layout.addWidget(value)
            metrics.addWidget(metric)
        outer.addLayout(metrics)

        splitter = QSplitter()
        self.queue = QListWidget()
        self.queue.setMinimumWidth(330)
        self.queue.setWordWrap(True)
        self.queue.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue.currentItemChanged.connect(self._show_work)
        splitter.addWidget(self.queue)
        right, right_layout = card()
        self.detail = QTextBrowser()
        self.detail.setObjectName("DetailPanel")
        right_layout.addWidget(self.detail, 1)
        self.action_bar = QWidget()
        self.action_layout = QHBoxLayout(self.action_bar)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.action_bar)
        splitter.addWidget(right)
        splitter.setSizes([360, 700])
        outer.addWidget(splitter, 1)
        self.tasks: list[ProposedTask] = []
        self.current_task_id: str | None = None
        self._show_empty()

    def show_report(self, report: ScanReport) -> None:
        selected_id = self.current_task_id
        self.tasks = [task for task in report.proposed_tasks if str(task.agent_state) != AgentWorkState.UNASSIGNED]
        self.queue.clear()
        for task in self.tasks:
            state = str(task.agent_state).replace("_", " ").upper()
            item = QListWidgetItem(f"{state}\n{task.title}")
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.queue.addItem(item)
            if task.id == selected_id:
                self.queue.setCurrentItem(item)
        self.metric_labels["queued"].setText(str(sum(str(task.agent_state) == AgentWorkState.QUEUED for task in self.tasks)))
        self.metric_labels["active"].setText(str(sum(str(task.agent_state) in {AgentWorkState.IN_PROGRESS, AgentWorkState.VALIDATION, AgentWorkState.BLOCKED} for task in self.tasks)))
        self.metric_labels["approval"].setText(str(sum(str(task.agent_state) == AgentWorkState.AWAITING_APPROVAL for task in self.tasks)))
        self.metric_labels["complete"].setText(str(sum(str(task.agent_state) == AgentWorkState.COMPLETE for task in self.tasks)))
        if self.queue.count() and self.queue.currentRow() < 0:
            self.queue.setCurrentRow(0)
        elif not self.queue.count():
            self._show_empty()

    def _show_work(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if not current:
            self._show_empty()
            return
        task_id = current.data(Qt.ItemDataRole.UserRole)
        task = next((entry for entry in self.tasks if entry.id == task_id), None)
        if not task:
            return
        self.current_task_id = task.id
        criteria = "".join(f"<li>{html.escape(item)}</li>" for item in task.acceptance_criteria)
        paths = "".join(f"<li><code>{html.escape(path)}</code></li>" for path in task.affected_paths)
        activity = "".join(f"<li>{html.escape(self._format_activity(event))}</li>" for event in reversed(task.agent_activity)) or "<li>No activity recorded.</li>"
        state = str(task.agent_state).replace("_", " ").title()
        self.detail.setHtml(f"""
        <style>body {{ font-family:-apple-system, Segoe UI, sans-serif; color:#172033; padding:8px; }}
        .state {{ color:#0F766E; font-weight:700; font-size:11px; letter-spacing:1px; }}
        h1 {{ font-size:23px; margin:5px 0; }} h2 {{ font-size:14px; margin-top:20px; }}
        .muted {{ color:#64748B; }} code {{ background:#F1F5F9; padding:2px 5px; border-radius:4px; }}</style>
        <div class='state'>{html.escape(state.upper())}</div><h1>{html.escape(task.title)}</h1>
        <p class='muted'>{html.escape(task.objective)}</p><h2>Required actions</h2><ol>{criteria}</ol>
        <h2>Affected files</h2><ul>{paths}</ul><h2>Activity</h2><ul>{activity}</ul>
        """)
        self._set_actions(task)

    def _set_actions(self, task: ProposedTask) -> None:
        self._clear_actions()
        self.action_layout.addStretch()
        for label, target in next_agent_actions(task):
            button = QPushButton(label)
            button.setObjectName("Primary" if target in {AgentWorkState.IN_PROGRESS, AgentWorkState.VALIDATION, AgentWorkState.AWAITING_APPROVAL, AgentWorkState.COMPLETE} else "Secondary")
            button.clicked.connect(lambda checked=False, task_id=task.id, state=str(target): self.state_requested.emit(task_id, state))
            self.action_layout.addWidget(button)

    def _clear_actions(self) -> None:
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self) -> None:
        self.current_task_id = None
        self.detail.setHtml("<div style='font-family:sans-serif;color:#64748B;padding:30px'><h2>Developer queue is empty</h2><p>Accept a suggestion and send it here when it is ready for controlled development.</p></div>")
        self._clear_actions()

    @staticmethod
    def _format_activity(event: str) -> str:
        timestamp, separator, message = event.partition(" | ")
        if not separator:
            return event
        try:
            rendered = datetime.fromisoformat(timestamp).astimezone().strftime("%d %b %Y, %H:%M")
        except ValueError:
            rendered = timestamp
        return f"{rendered} — {message}"


class HistoryPage(QWidget):
    report_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(16)
        outer.addWidget(title_block("Scan history", "Completed analyses are stored locally on this device."))
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open)
        outer.addWidget(self.list, 1)
        self.reports: list[ScanReport] = []

    def set_reports(self, reports: list[ScanReport]) -> None:
        self.reports = reports
        self.list.clear()
        for report in reports:
            try:
                timestamp = datetime.fromisoformat(report.created_at).astimezone().strftime("%d %b %Y, %H:%M")
            except ValueError:
                timestamp = report.created_at
            item = QListWidgetItem(f"{report.repository_name}\n{timestamp}  ·  {len(report.findings)} findings")
            item.setData(Qt.ItemDataRole.UserRole, report.scan_id)
            self.list.addItem(item)

    def _open(self, item: QListWidgetItem) -> None:
        scan_id = item.data(Qt.ItemDataRole.UserRole)
        report = next((entry for entry in self.reports if entry.scan_id == scan_id), None)
        if report:
            self.report_requested.emit(report)


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Automate settings")
        self.setMinimumSize(520, 300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        title = QLabel("Privacy and storage")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        for heading, body in (
            ("✓ Local repository analysis", "Repository contents are processed on this device."),
            ("✓ External AI disabled", "No repository data is sent to a model or external service."),
            ("✓ Local scan history", "Reports and review decisions are saved in your operating system's application-data directory."),
        ):
            frame, frame_layout = card()
            label = QLabel(heading)
            label.setObjectName("SectionTitle")
            description = QLabel(body)
            description.setWordWrap(True)
            description.setObjectName("Muted")
            frame_layout.addWidget(label)
            frame_layout.addWidget(description)
            layout.addWidget(frame)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Automate")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self.repository_path: str | None = None
        self.current_report: ScanReport | None = None
        self.worker: ScanWorker | None = None
        self.store = HistoryStore()
        self.history = self.store.load()
        self._build_ui()
        self._build_menu()
        self.history_page.set_reports(self.history)
        self.statusBar().showMessage("Ready — local analysis only")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(244)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 22, 16, 18)
        side.setSpacing(8)
        brand = QLabel("UniversalL2")
        brand.setObjectName("Brand")
        subtitle = QLabel("ENGINEERING CONTROL ROOM")
        subtitle.setObjectName("BrandSub")
        side.addWidget(brand)
        side.addWidget(subtitle)
        side.addSpacing(24)

        self.pages = QStackedWidget()
        self.overview = OverviewPage()
        self.findings_page = FindingsPage()
        self.tasks_page = TasksPage()
        self.developer_page = DeveloperAgentPage()
        self.history_page = HistoryPage()
        for page in (self.overview, self.findings_page, self.tasks_page, self.developer_page, self.history_page):
            self.pages.addWidget(page)

        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []
        for index, (label, symbol) in enumerate((("Repository", "▦"), ("Analysis evidence", "◇"), ("Suggestions", "☑"), ("Developer agent", "⌘"), ("Activity", "◴"))):
            button = QPushButton(f"{symbol}   {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            if index == 0:
                button.setChecked(True)
            button.clicked.connect(lambda checked=False, page_index=index: self._navigate(page_index))
            group.addButton(button)
            self.nav_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        settings = QPushButton("⚙   Settings")
        settings.setObjectName("NavButton")
        settings.clicked.connect(lambda: SettingsDialog(self).exec())
        side.addWidget(settings)
        privacy = QFrame()
        privacy.setObjectName("PrivacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_title = QLabel("●  Local analysis")
        privacy_title.setObjectName("PrivacyTitle")
        privacy_body = QLabel("No repository data leaves this device")
        privacy_body.setObjectName("PrivacyBody")
        privacy_body.setWordWrap(True)
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_body)
        side.addWidget(privacy)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)

        self.overview.choose_requested.connect(self.choose_repository)
        self.overview.scan_requested.connect(self.start_scan)
        self.overview.export_requested.connect(self.export_report)
        self.tasks_page.decision_changed.connect(self.update_task_decision)
        self.tasks_page.handoff_requested.connect(self.handoff_task)
        self.developer_page.state_requested.connect(self.update_agent_state)
        self.history_page.report_requested.connect(self.open_history_report)
        self.setStatusBar(QStatusBar())

    def _navigate(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        choose_action = QAction("Choose repository…", self)
        choose_action.setShortcut("Ctrl+O")
        choose_action.triggered.connect(self.choose_repository)
        export_action = QAction("Export report…", self)
        export_action.setShortcut("Ctrl+Shift+E")
        export_action.triggered.connect(self.export_report)
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(choose_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def choose_repository(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose a repository", self.repository_path or str(Path.home()))
        if directory:
            self.repository_path = directory
            self.current_report = None
            self.overview.set_repository(directory)
            self._navigate(0)
            self.statusBar().showMessage(f"Selected {directory}")

    def start_scan(self) -> None:
        if not self.repository_path or self.worker:
            return
        self.overview.set_scanning(True)
        self.statusBar().showMessage("Analyzing repository without executing or modifying code…")
        self.worker = ScanWorker(self.repository_path)
        self.worker.completed.connect(self._scan_completed)
        self.worker.failed.connect(self._scan_failed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _scan_completed(self, report: ScanReport) -> None:
        self.current_report = report
        self.history = [entry for entry in self.history if entry.scan_id != report.scan_id]
        self.history.insert(0, report)
        self.store.save(report)
        self._show_report(report)
        self.statusBar().showMessage(f"Analysis complete — {len(report.findings)} findings and {len(report.proposed_tasks)} proposed tasks")

    def _scan_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Analysis failed", message)
        self.statusBar().showMessage("Analysis failed")

    def _worker_finished(self) -> None:
        self.overview.set_scanning(False)
        self.worker = None

    def _show_report(self, report: ScanReport) -> None:
        self.repository_path = report.repository_path
        self.overview.set_repository(report.repository_path)
        self.overview.show_report(report)
        self.findings_page.show_report(report)
        self.tasks_page.show_report(report)
        self.developer_page.show_report(report)
        self.history_page.set_reports(self.history)

    def update_task_decision(self, task_id: str, state: str) -> None:
        if not self.current_report:
            return
        task = next((item for item in self.current_report.proposed_tasks if item.id == task_id), None)
        if not task:
            return
        task.review_state = state
        self._persist_current_report()
        self.overview.show_report(self.current_report)
        self.tasks_page.show_report(self.current_report)
        self.statusBar().showMessage(f"Task decision updated to {state}")

    def handoff_task(self, task_id: str) -> None:
        if not self.current_report:
            return
        task = next((item for item in self.current_report.proposed_tasks if item.id == task_id), None)
        if not task:
            return
        try:
            handoff_to_developer(task)
        except WorkflowError as exc:
            QMessageBox.warning(self, "Handoff unavailable", str(exc))
            return
        self._persist_current_report()
        self.tasks_page.show_report(self.current_report)
        self.developer_page.show_report(self.current_report)
        self._navigate(3)
        self.statusBar().showMessage("Approved suggestion added to the developer queue")

    def update_agent_state(self, task_id: str, state: str) -> None:
        if not self.current_report:
            return
        task = next((item for item in self.current_report.proposed_tasks if item.id == task_id), None)
        if not task:
            return
        try:
            transition_agent_work(task, state)
        except WorkflowError as exc:
            QMessageBox.warning(self, "Workflow transition unavailable", str(exc))
            return
        self._persist_current_report()
        self.tasks_page.show_report(self.current_report)
        self.developer_page.show_report(self.current_report)
        self.statusBar().showMessage(f"Developer workflow updated to {state.replace('_', ' ')}")

    def _persist_current_report(self) -> None:
        if not self.current_report:
            return
        self.store.save(self.current_report)
        for index, report in enumerate(self.history):
            if report.scan_id == self.current_report.scan_id:
                self.history[index] = self.current_report
                break

    def open_history_report(self, report: ScanReport) -> None:
        self.current_report = report
        self._show_report(report)
        self._navigate(0)

    def export_report(self) -> None:
        if not self.current_report:
            QMessageBox.information(self, "No report", "Analyze a repository before exporting a report.")
            return
        suggested = f"automate-{self.current_report.repository_name}-report.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export Automate report", suggested, "JSON files (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.current_report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Report exported to {path}")
