"""Native desktop direction selector. Reverse direction remains read-only."""
from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget)
from arc2zen.desktop import MainWindow as UpstreamWindow
from arc2zen.profile_paths import discover_zen_profiles
from .zen2arc.reader import inspect_zen
from .zen2arc.report import write_report
from .zen2arc.capabilities import ZEN_TO_ARC

class MigratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arc ↔ Zen Migrator")
        self.resize(880, 650)
        self.upstream = None
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        heading = QLabel("Arc ↔ Zen Migrator")
        heading.setStyleSheet("font-size: 23px; font-weight: 700;")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Choose a direction. Reverse Arc sidebar writes are disabled until verified."))
        self.direction = QComboBox()
        self.direction.addItems(["Arc → Zen (upstream)", "Zen → Arc (preview only)"])
        layout.addWidget(self.direction)
        row = QHBoxLayout()
        self.profile = QComboBox()
        self.profile.setEditable(True)
        row.addWidget(self.profile, 1)
        browse = QPushButton("Browse Zen profile…")
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        layout.addLayout(row)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 1)
        actions = QHBoxLayout()
        self.preview_button = QPushButton("Preview Zen")
        self.preview_button.clicked.connect(self.preview)
        actions.addWidget(self.preview_button)
        self.export_button = QPushButton('Save privacy-safe preview…')
        self.export_button.clicked.connect(self.export_preview)
        actions.addWidget(self.export_button)
        self.arc_button = QPushButton("Open upstream Arc → Zen GUI")
        self.arc_button.clicked.connect(self.open_upstream)
        actions.addWidget(self.arc_button)
        layout.addLayout(actions)
        self.direction.currentIndexChanged.connect(self.refresh)
        for path in discover_zen_profiles():
            self.profile.addItem(str(path))
        self.refresh()

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Zen profile")
        if path:
            self.profile.setEditText(path)

    def refresh(self):
        reverse = self.direction.currentIndex() == 1
        self.preview_button.setEnabled(reverse)
        self.export_button.setEnabled(reverse)
        self.arc_button.setEnabled(not reverse)
        self.output.setPlainText(
            "Zen → Arc currently supports read-only discovery.\n\n"
            + "\n".join(f"{name}: {status.value}" for name, status in ZEN_TO_ARC.items())
            if reverse else
            "Arc → Zen uses the preserved upstream migration window.\n"
            "Back up your profile and close Zen before applying changes."
        )

    def preview(self):
        try:
            inv = inspect_zen(Path(self.profile.currentText()))
        except (OSError, ValueError, RuntimeError, ImportError) as exc:
            QMessageBox.warning(self, "Preview unavailable", f"{type(exc).__name__}: {exc}")
            return
        lines = [f"Spaces: {len(inv.spaces)}", f"Tabs: {inv.tab_count}",
                 f"Pinned: {inv.pinned_count}", f"Essentials: {inv.essential_count}",
                 f"Groups: {inv.groups}", f"Orphan tabs: {len(inv.orphan_tabs)}", ""]
        for space in inv.spaces:
            lines.append(f"{space.name}: {len(space.tabs)} tabs, {len(space.folders)} folders")
        lines.extend(["", "Unsupported: Arc sidebar writing, CloudKit, cookies, passwords"])
        lines.extend(f"Warning: {warning}" for warning in inv.warnings)
        self.output.setPlainText("\n".join(lines))

    def export_preview(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Zen preview report", "zen-preview.json", "JSON (*.json)")
        if not path:
            return
        try:
            report = write_report(Path(self.profile.currentText()), Path(path))
        except (OSError, ValueError, RuntimeError, ImportError) as exc:
            QMessageBox.warning(self, "Export unavailable", f"{type(exc).__name__}: {exc}")
            return
        QMessageBox.information(self, "Preview saved", "Privacy-safe report saved. {} tabs counted.".format(report["counts"]["tabs"]))

    def open_upstream(self):
        self.upstream = UpstreamWindow()
        self.upstream.show()

def main():
    from arc2zen.migration import use_utf8_output
    use_utf8_output()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Arc Zen Migrator")
    window = MigratorWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
