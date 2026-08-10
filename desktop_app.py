"""CSV 컬럼 합계 비교 데스크톱 앱."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from compare import format_number, read_columns, sum_column


class SumWorker(QThread):
    finished_ok = Signal(float, int, int, float, int, int)
    failed = Signal(str)

    def __init__(self, path_a: Path, col_a: str, path_b: Path, col_b: str, encoding: str):
        super().__init__()
        self.path_a = path_a
        self.col_a = col_a
        self.path_b = path_b
        self.col_b = col_b
        self.encoding = encoding

    def run(self) -> None:
        try:
            sum_a, valid_a, rows_a = sum_column(self.path_a, self.col_a, encoding=self.encoding)
            sum_b, valid_b, rows_b = sum_column(self.path_b, self.col_b, encoding=self.encoding)
            self.finished_ok.emit(sum_a, valid_a, rows_a, sum_b, valid_b, rows_b)
        except Exception as exc:  # noqa: BLE001 - UI에 그대로 표시
            self.failed.emit(str(exc))


class FilePanel(QGroupBox):
    def __init__(self, title: str):
        super().__init__(title)
        self.path: Path | None = None

        self.path_label = QLabel("선택된 파일 없음")
        self.path_label.setWordWrap(True)

        self.browse_btn = QPushButton("파일 선택...")
        self.browse_btn.clicked.connect(self.choose_file)

        self.column_combo = QComboBox()
        self.column_combo.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.path_label)
        layout.addWidget(QLabel("컬럼"))
        layout.addWidget(self.column_combo)

    def choose_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "CSV 파일 선택",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not selected:
            return
        self.set_file(Path(selected))

    def set_file(self, path: Path, encoding: str = "utf-8-sig") -> None:
        try:
            columns = read_columns(path, encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "오류", f"헤더를 읽지 못했습니다.\n{exc}")
            return

        self.path = path
        self.path_label.setText(str(path))
        self.column_combo.clear()
        self.column_combo.addItems(columns)
        self.column_combo.setEnabled(True)

    def reload_columns(self, encoding: str) -> None:
        if self.path is None:
            return
        current = self.column_combo.currentText()
        try:
            columns = read_columns(self.path, encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "오류", f"헤더를 읽지 못했습니다.\n{exc}")
            return
        self.column_combo.clear()
        self.column_combo.addItems(columns)
        idx = self.column_combo.findText(current)
        if idx >= 0:
            self.column_combo.setCurrentIndex(idx)

    def selected_column(self) -> str | None:
        if self.path is None or self.column_combo.count() == 0:
            return None
        return self.column_combo.currentText()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CSV 컬럼 합계 비교")
        self.resize(900, 520)
        self.worker: SumWorker | None = None

        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8-sig", "utf-8", "cp949", "euc-kr"])
        self.encoding_combo.currentTextChanged.connect(self.on_encoding_changed)

        self.panel_a = FilePanel("파일 A")
        self.panel_b = FilePanel("파일 B")

        self.compare_btn = QPushButton("합계 비교 실행")
        self.compare_btn.clicked.connect(self.run_compare)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        self.result_label = QLabel("파일을 선택하고 컬럼을 고른 뒤 비교하세요.")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.result_label.setWordWrap(True)
        self.result_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        top = QHBoxLayout()
        top.addWidget(QLabel("인코딩"))
        top.addWidget(self.encoding_combo)
        top.addStretch(1)

        files = QHBoxLayout()
        files.addWidget(self.panel_a)
        files.addWidget(self.panel_b)

        root = QVBoxLayout()
        root.addLayout(top)
        root.addLayout(files)
        root.addWidget(self.compare_btn)
        root.addWidget(self.progress)
        root.addWidget(self.result_label, stretch=1)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def encoding(self) -> str:
        return self.encoding_combo.currentText()

    def on_encoding_changed(self, _value: str) -> None:
        enc = self.encoding()
        self.panel_a.reload_columns(enc)
        self.panel_b.reload_columns(enc)

    def run_compare(self) -> None:
        path_a = self.panel_a.path
        path_b = self.panel_b.path
        col_a = self.panel_a.selected_column()
        col_b = self.panel_b.selected_column()

        if path_a is None or path_b is None or col_a is None or col_b is None:
            QMessageBox.warning(self, "안내", "파일 A/B와 컬럼을 모두 선택하세요.")
            return

        # 같은 이름이 있으면 B도 맞춰 주기 (이미 선택돼 있으면 유지)
        if col_a in [
            self.panel_b.column_combo.itemText(i) for i in range(self.panel_b.column_combo.count())
        ]:
            pass

        self.compare_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.result_label.setText("계산 중...")

        self.worker = SumWorker(path_a, col_a, path_b, col_b, self.encoding())
        self.worker.finished_ok.connect(self.on_success)
        self.worker.failed.connect(self.on_failure)
        self.worker.start()

    def on_success(
        self,
        sum_a: float,
        valid_a: int,
        rows_a: int,
        sum_b: float,
        valid_b: int,
        rows_b: int,
    ) -> None:
        self.progress.setVisible(False)
        self.compare_btn.setEnabled(True)

        diff = sum_a - sum_b
        if sum_b != 0:
            diff_pct_text = f"{(diff / sum_b) * 100:.6f}%"
        elif sum_a == 0:
            diff_pct_text = "0%"
        else:
            diff_pct_text = "N/A (B 합계 0)"

        matched = abs(diff) < 1e-9
        status = "합계가 일치합니다." if matched else "합계가 일치하지 않습니다."

        path_a = self.panel_a.path
        path_b = self.panel_b.path
        assert path_a is not None and path_b is not None

        self.result_label.setText(
            f"{status}\n\n"
            f"[A] {path_a.name} / {self.panel_a.selected_column()}\n"
            f"    합계: {format_number(sum_a)}\n"
            f"    행 수: {rows_a:,} (숫자 {valid_a:,})\n\n"
            f"[B] {path_b.name} / {self.panel_b.selected_column()}\n"
            f"    합계: {format_number(sum_b)}\n"
            f"    행 수: {rows_b:,} (숫자 {valid_b:,})\n\n"
            f"차이 (A − B): {format_number(diff)}\n"
            f"차이율 (대비 B): {diff_pct_text}"
        )

    def on_failure(self, message: str) -> None:
        self.progress.setVisible(False)
        self.compare_btn.setEnabled(True)
        self.result_label.setText("비교 실패")
        QMessageBox.critical(self, "오류", message)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
