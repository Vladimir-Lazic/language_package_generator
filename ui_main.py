#!/usr/bin/env python3
"""
ui_main.py

PySide6 UI for the subtitle language package generator.

- Controls at top (file picker, input language, output language add, clear)
- Middle: scrollable list of output languages/files
- Bottom: big animated run button (stateful)
- Runs language_package_generator.py as a subprocess (worker thread)
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QObject, QTimer, Property
)
from PySide6.QtGui import QPainter, QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication, QWidget, QFileDialog, QComboBox, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy, QScrollArea, QMessageBox
)


# ---------------------------
# Config: languages list
# ---------------------------
LANGUAGES = [
    "en", "fr", "de", "it", "es", "pt", "nl", "sv", "no", "da", "fi",
    "ru", "pl", "cs", "hu", "ro", "tr", "ja", "zh", "ko"
]


# ---------------------------
# Small utility functions
# ---------------------------
def human_path(p: str) -> str:
    if not p:
        return ""
    return str(Path(p).expanduser())


# ---------------------------
# Worker: runs generator subprocess
# ---------------------------
class GeneratorWorker(QThread):
    # signals: progress events parsed from subprocess output
    progress = Signal(int, str)  # percent, message
    log = Signal(str)  # raw log line
    finished_ok = Signal()
    finished_err = Signal(str)  # error message

    def __init__(self, input_file: str, input_lang: str, output_langs: List[str], python_exe="python3"):
        super().__init__()
        self.input_file = input_file
        self.input_lang = input_lang
        self.output_langs = output_langs[:]
        self._kill = False
        self.python_exe = python_exe

    def run(self):
        # Build command that calls your script. We expect language_package_generator.py to be in cwd
        cmd = [
            self.python_exe,
            "language_package_generator.py",
            "--input_file", self.input_file,
            "--input_language", self.input_lang,
            "--output_languages", *self.output_langs
        ]
        # run the command and stream stdout
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            self.finished_err.emit(f"Failed to start process: {e}")
            return

        # Progress heuristics:
        # We expect N languages translated + 1 docx step => total_steps = N + 1
        total_steps = max(1, len(self.output_langs) + 1)
        completed_steps = 0

        # Read stdout line by line and parse
        if not proc.stdout:
            self.finished_err.emit("No output from process.")
            return

        for raw_line in proc.stdout:
            if self._kill:
                proc.kill()
                break
            line = raw_line.strip()
            self.log.emit(line)

            # parse expected messages from your generator (as implemented earlier)
            # e.g., "✅ Generated SRT: filename" or "📄 DOCX generated: file"
            if "Generated SRT" in line or "Generated SRT:" in line or "Generated SRT" in line:
                completed_steps += 1
                percent = int(100 * completed_steps / total_steps * 0.9)  # up to 90% before final docx
                self.progress.emit(percent, f"Completed {completed_steps}/{total_steps - 1} translations")
            elif "DOCX generated" in line or "DOCX generated:" in line or "📄 DOCX generated" in line:
                completed_steps += 1
                percent = 100
                self.progress.emit(percent, "DOCX created")
            else:
                # some generic progress update: just emit log text
                self.progress.emit(int(100 * completed_steps / total_steps * 0.6), line)

        proc.wait()
        if proc.returncode == 0 and not self._kill:
            self.finished_ok.emit()
        elif self._kill:
            self.finished_err.emit("Cancelled by user")
        else:
            self.finished_err.emit(f"Process ended with code {proc.returncode}")

    def kill(self):
        self._kill = True


# ---------------------------
# Animated State Button: custom big button painted with color interpolation
# ---------------------------
class StateRunButton(QPushButton):
    """
    Big run button with states and smooth color transitions.
    States:
        idle (gray), ready (blue), running (red), almost (orange), done (green)
    """

    STATES = {
        "idle": QColor("#BDBDBD"),
        "ready": QColor("#4DA6FF"),   # blue
        "running": QColor("#E74C3C"), # red
        "almost": QColor("#F39C12"),  # orange
        "done": QColor("#2ECC71"),    # green
    }

    def __init__(self, text="Not configured"):
        super().__init__(text)
        self._color = StateRunButton.STATES["idle"]
        self._target_color = self._color
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFont(QFont("Sans", 14, QFont.Bold))
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60fps
        self._anim_timer.timeout.connect(self._animate_step)
        self._steps = 0
        self._step_index = 0
        self._start_rgb = (self._color.red(), self._color.green(), self._color.blue())

        # default style tweaks
        self.setCursor(Qt.PointingHandCursor)

    def set_state(self, state_name: str, label: str = None):
        """Change target color; start animation."""
        target = StateRunButton.STATES.get(state_name, StateRunButton.STATES["idle"])
        self._start_rgb = (self._color.red(), self._color.green(), self._color.blue())
        self._target_color = target
        self._steps = 12  # frames to animate
        self._step_index = 0
        self._anim_timer.start()
        if label is not None:
            self.setText(label)

    def _animate_step(self):
        if self._step_index >= self._steps:
            self._anim_timer.stop()
            self._color = self._target_color
            self.update()
            return
        frac = (self._step_index + 1) / self._steps
        sr, sg, sb = self._start_rgb
        tr, tg, tb = self._target_color.red(), self._target_color.green(), self._target_color.blue()
        new_r = int(sr + (tr - sr) * frac)
        new_g = int(sg + (tg - sg) * frac)
        new_b = int(sb + (tb - sb) * frac)
        self._color = QColor(new_r, new_g, new_b)
        self._step_index += 1
        self.update()

    def paintEvent(self, event):
        # Paint rounded rect filled with current color and centered label
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 12, 12)

        # Draw text
        painter.setPen(Qt.white)
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())


# ---------------------------
# Main UI
# ---------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Language Package Generator - GUI")
        self.resize(760, 600)
        self._worker = None

        # Layout: vertical groups top-to-bottom
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # 1) CONTROL SECTION (top)
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_frame.setFixedHeight(160)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(12, 12, 12, 12)
        control_layout.setSpacing(10)

        # input file area
        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("Input file:"))
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #666;")
        left_col.addWidget(self.file_label)

        file_btn_row = QHBoxLayout()
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.on_browse)
        file_btn_row.addWidget(btn_browse)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.on_clear_all)
        file_btn_row.addWidget(btn_clear)
        left_col.addLayout(file_btn_row)

        # center: language selectors
        mid_col = QVBoxLayout()
        mid_col.addWidget(QLabel("Input language:"))
        self.input_lang_cb = QComboBox()
        self.input_lang_cb.addItems(LANGUAGES)
        mid_col.addWidget(self.input_lang_cb)

        mid_col.addSpacing(8)
        mid_col.addWidget(QLabel("Add output language:"))
        add_row = QHBoxLayout()
        self.output_lang_cb = QComboBox()
        self.output_lang_cb.addItems(LANGUAGES)
        add_row.addWidget(self.output_lang_cb)
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.on_add_language)
        add_row.addWidget(btn_add)
        mid_col.addLayout(add_row)

        # right: quick hints
        right_col = QVBoxLayout()
        hint = QLabel("Selected output languages will be shown below.\nRemove any with the Delete key or context menu.")
        hint.setWordWrap(True)
        right_col.addWidget(hint)
        right_col.addStretch()

        control_layout.addLayout(left_col, 3)
        control_layout.addLayout(mid_col, 3)
        control_layout.addLayout(right_col, 4)

        main_layout.addWidget(control_frame)

        # 2) OUTPUT LIST (middle) - scrollable
        list_frame = QFrame()
        list_frame.setFrameShape(QFrame.StyledPanel)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_layout.setSpacing(6)
        list_layout.addWidget(QLabel("Files to be generated:"))

        self.output_list = QListWidget()
        self.output_list.setSelectionMode(QListWidget.SingleSelection)
        self.output_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_list.customContextMenuRequested.connect(self._on_list_context)
        list_layout.addWidget(self.output_list)

        main_layout.addWidget(list_frame, 1)

        # 3) RUN BUTTON AREA (bottom)
        run_frame = QFrame()
        run_frame.setFrameShape(QFrame.StyledPanel)
        run_layout = QVBoxLayout(run_frame)
        run_layout.setContentsMargins(12, 12, 12, 12)

        self.state_button = StateRunButton("Not configured")
        self.state_button.setEnabled(False)  # main button not clickable directly for generation
        run_layout.addWidget(self.state_button)

        # small control buttons below big button
        controls_row = QHBoxLayout()
        self.btn_generate = QPushButton("Generate")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.on_generate)
        controls_row.addWidget(self.btn_generate)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.on_cancel)
        controls_row.addWidget(self.btn_cancel)

        run_layout.addLayout(controls_row)
        main_layout.addWidget(run_frame)

        # internal state
        self.selected_file = ""
        self._update_ui_state()

    # ---------------------------
    # Control handlers
    # ---------------------------
    def on_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select input file", "", "SRT Files (*.srt);;All files (*)")
        if file_path:
            self.selected_file = human_path(file_path)
            self.file_label.setText(self.selected_file)
            self._update_ui_state()

    def on_clear_all(self):
        self.selected_file = ""
        self.file_label.setText("No file selected")
        self.output_list.clear()
        self._update_ui_state()
        # after clearing, button goes idle gray
        self.state_button.set_state("idle", "Not configured")

    def on_add_language(self):
        lang = self.output_lang_cb.currentText()
        # Do not add duplicates
        if not any(self.output_list.item(i).text() == lang for i in range(self.output_list.count())):
            item = QListWidgetItem(lang)
            self.output_list.addItem(item)
        self._update_ui_state()

    def _on_list_context(self, pos):
        # Simple remove on right-click context -> remove selected item
        item = self.output_list.itemAt(pos)
        if item:
            self.output_list.takeItem(self.output_list.row(item))
        self._update_ui_state()

    def _update_ui_state(self):
        # Determine readiness: file selected + at least one output lang
        ready = bool(self.selected_file) and (self.output_list.count() > 0)
        self.btn_generate.setEnabled(ready)
        # Also change the big state button to ready if configured
        if ready:
            self.state_button.set_state("ready", "Ready to generate")
            self.state_button.setEnabled(True)
        else:
            self.state_button.set_state("idle", "Not configured")
            self.state_button.setEnabled(False)

    # ---------------------------
    # Generation logic
    # ---------------------------
    def on_generate(self):
        if not self.btn_generate.isEnabled():
            return
        # prepare args
        input_lang = self.input_lang_cb.currentText()
        output_langs = [self.output_list.item(i).text() for i in range(self.output_list.count())]
        # confirm existence of generator script
        generator_path = Path("language_package_generator.py")
        if not generator_path.exists():
            QMessageBox.critical(self, "Error", "language_package_generator.py not found in working directory.")
            return

        # Set UI into running state
        self.btn_generate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.state_button.set_state("running", "Running...")
        self.state_button.setEnabled(False)

        # start worker thread
        python_exe = sys.executable or "python3"
        self._worker = GeneratorWorker(self.selected_file, input_lang, output_langs, python_exe=python_exe)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.log.connect(self._on_worker_log)
        self._worker.finished_ok.connect(self._on_worker_done)
        self._worker.finished_err.connect(self._on_worker_error)
        self._worker.start()

    def on_cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.kill()
            self.btn_cancel.setEnabled(False)

    # ---------------------------
    # Worker signals
    # ---------------------------
    @Slot(int, str)
    def _on_worker_progress(self, percent: int, message: str):
        # percent 0..100 -> map to state changes
        if percent >= 100:
            self.state_button.set_state("done", "Done")
        elif percent >= 85:
            self.state_button.set_state("almost", "Almost")
        elif percent > 0:
            # while running but not near finish, keep red running
            self.state_button.set_state("running", "Running...")
        # we could also show message somewhere; use window title briefly
        self.setWindowTitle(f"Language Package Generator - {message}")

    @Slot(str)
    def _on_worker_log(self, line: str):
        # parse lines mentioning generated files and add them to the bottom list for visibility
        # e.g., "✅ Generated SRT: filename"
        if "Generated SRT" in line or "Generated SRT:" in line:
            # try to extract filename text after colon
            parts = line.split(":")
            if len(parts) > 1:
                fn = parts[-1].strip()
                self.output_list.addItem(QListWidgetItem(fn))
        elif "DOCX generated" in line or "DOCX generated:" in line:
            parts = line.split(":")
            if len(parts) > 1:
                fn = parts[-1].strip()
                self.output_list.addItem(QListWidgetItem(fn))
        # you may also print or show logs in a dedicated area

    @Slot()
    def _on_worker_done(self):
        self.btn_cancel.setEnabled(False)
        self.btn_generate.setEnabled(True)
        # show done state for a while, then remain green until user changes inputs
        self.state_button.set_state("done", "Done")
        QMessageBox.information(self, "Completed", "Language package generation finished successfully.")
        self._worker = None
        self._update_ui_state()

    @Slot(str)
    def _on_worker_error(self, err_msg: str):
        self.btn_cancel.setEnabled(False)
        self.btn_generate.setEnabled(True)
        self._worker = None
        QMessageBox.critical(self, "Generator Error", f"Generation failed: {err_msg}")
        self.state_button.set_state("idle", "Not configured")
        self._update_ui_state()


# ---------------------------
# Run app
# ---------------------------
def main():
    app = QApplication(sys.argv)

    # Gentle, soft theme using stylesheet
    app.setStyleSheet("""
    QWidget { background: #FBFBFD; font-family: "Segoe UI", "Helvetica Neue", Arial; color: #222; }
    QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #EEE; }
    QPushButton { padding: 8px 12px; border-radius: 8px; background: #F0F2F5; }
    QPushButton:pressed { background: #E8EEF8; }
    QListWidget { background: #FCFCFE; border-radius: 6px; border: 1px solid #EEE; }
    QLabel { color: #444; }
    QComboBox { padding: 6px; }
    """)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
