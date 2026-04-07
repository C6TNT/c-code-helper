import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.engine import analyze_code


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("C 语言代码理解助手")
        self.resize(1380, 860)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 5)

        title_left = QLabel("代码输入区")
        title_left.setStyleSheet("font-size: 26px; font-weight: 700; color: #123b66;")
        left_layout.addWidget(title_left)

        hint = QLabel("把你看不懂的模板代码、示例代码，或者自己刚改过的代码片段粘贴进来。")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 15px; color: #335b82;")
        left_layout.addWidget(hint)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("例如：粘贴 app.c 里某个页面函数、按键函数、参数结构体或判断逻辑。")
        self.code_input.setStyleSheet(
            "QTextEdit {background:#ffffff; color:#1d2b38; border:2px solid #d8e6f4; border-radius:14px; font-size:16px; padding:10px;}"
        )
        left_layout.addWidget(self.code_input, 1)

        button_row = QHBoxLayout()
        self.analyze_button = QPushButton("开始讲解")
        self.clear_button = QPushButton("清空")
        for button in (self.analyze_button, self.clear_button):
            button.setStyleSheet(
                "QPushButton {background:#2f80ed; color:white; font-size:16px; font-weight:700; border:none; border-radius:12px; padding:14px 18px;}"
                "QPushButton:hover {background:#276fd0;}"
            )
            button_row.addWidget(button)
        left_layout.addLayout(button_row)

        title_right = QLabel("讲解结果")
        title_right.setStyleSheet("font-size: 26px; font-weight: 700; color: #123b66;")
        right_layout.addWidget(title_right)

        self.scene_card = QTextEdit()
        self.scene_card.setReadOnly(True)
        self.scene_card.setMaximumHeight(110)
        self.scene_card.setStyleSheet(
            "QTextEdit {background:#fff5eb; color:#6d3d11; border:2px solid #f3d1ac; border-radius:14px; font-size:16px; padding:10px;}"
        )
        right_layout.addWidget(self.scene_card)

        row_top = QHBoxLayout()
        row_bottom = QHBoxLayout()
        right_layout.addLayout(row_top)
        right_layout.addLayout(row_bottom)

        self.syntax_card = self._make_card("这段代码用了什么语法")
        self.feature_card = self._make_card("这段代码里识别到了什么")
        self.steps_card = self._make_card("建议按什么顺序看")
        self.explain_card = self._make_card("这段代码大概在做什么")

        row_top.addLayout(self.syntax_card["layout"])
        row_top.addLayout(self.feature_card["layout"])
        row_bottom.addLayout(self.steps_card["layout"])
        row_bottom.addLayout(self.explain_card["layout"])

        self.copy_button = QPushButton("复制讲解结果")
        self.copy_button.setStyleSheet(
            "QPushButton {background:#2f80ed; color:white; font-size:16px; font-weight:700; border:none; border-radius:12px; padding:14px 18px;}"
            "QPushButton:hover {background:#276fd0;}"
        )
        right_layout.addWidget(self.copy_button)

        self.analyze_button.clicked.connect(self.handle_analyze)
        self.clear_button.clicked.connect(self.handle_clear)
        self.copy_button.clicked.connect(self.handle_copy)

        self._last_result = ""

    def _make_card(self, title: str) -> dict:
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size: 18px; font-weight: 700; color: #123b66;")
        box = QTextEdit()
        box.setReadOnly(True)
        box.setMinimumHeight(180)
        box.setStyleSheet(
            "QTextEdit {background:#eef6ff; color:#1d2b38; border:2px solid #d7e8fb; border-radius:14px; font-size:15px; padding:10px;}"
        )
        layout.addWidget(label)
        layout.addWidget(box)
        return {"layout": layout, "box": box}

    def handle_analyze(self) -> None:
        try:
            result = analyze_code(self.code_input.toPlainText())
        except Exception as exc:
            QMessageBox.warning(self, "讲解失败", str(exc))
            return

        self.scene_card.setPlainText(result["scene"])
        self.syntax_card["box"].setPlainText(result["summary_text"])
        self.feature_card["box"].setPlainText(result["feature_text"])
        self.steps_card["box"].setPlainText(result["reading_steps_text"])
        self.explain_card["box"].setPlainText(result["explanation_text"])

        self._last_result = (
            f"代码归类：{result['scene']}\n\n"
            f"这段代码用了什么语法：\n{result['summary_text']}\n\n"
            f"这段代码里识别到了什么：\n{result['feature_text']}\n\n"
            f"建议按什么顺序看：\n{result['reading_steps_text']}\n\n"
            f"这段代码大概在做什么：\n{result['explanation_text']}"
        )

    def handle_clear(self) -> None:
        self.code_input.clear()
        self.scene_card.clear()
        self.syntax_card["box"].clear()
        self.feature_card["box"].clear()
        self.steps_card["box"].clear()
        self.explain_card["box"].clear()
        self._last_result = ""

    def handle_copy(self) -> None:
        if not self._last_result:
            QMessageBox.information(self, "提示", "现在还没有讲解结果，先点击“开始讲解”。")
            return
        QApplication.clipboard().setText(self._last_result)
        QMessageBox.information(self, "提示", "讲解结果已经复制到剪贴板。")


def run_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
