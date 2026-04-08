import sys

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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


SAMPLE_SNIPPETS = {
    "页面显示函数": """void App_ShowDataPage(void)
{
    SEG_Clear();
    SEG_SetCode(0, SEG_C);
    SEG_SetDigit(1, g_data.temp10 / 10);
    SEG_SetDigitDp(2, g_data.temp10 % 10);
    SEG_SetDigit(6, g_data.adc_value / 100);
    SEG_SetDigit(7, (g_data.adc_value / 10) % 10);
}""",
    "按键处理函数": """void App_HandleKey(void)
{
    u8 key;
    key = Key_GetEvent();
    if(key == 1)
    {
        g_page++;
        if(g_page > PAGE_RECORD)
        {
            g_page = PAGE_DATA;
        }
    }
}""",
    "参数结构体": """typedef struct
{
    int temp_limit_x10;
    u16 dist_limit;
    u8 adc_limit;
} app_param_t;

static app_param_t g_param = {300, 30, 200};""",
    "报警判断逻辑": """void App_UpdateAlarm(void)
{
    g_alarm = 0;
    if(g_data.temp10 > g_param.temp_limit_x10)
    {
        g_alarm = 1;
    }
    if(g_data.distance_cm < g_param.dist_limit)
    {
        g_alarm = 1;
    }
}""",
    "状态枚举": """typedef enum
{
    PAGE_DATA = 0,
    PAGE_PARAM,
    PAGE_TIME,
    PAGE_FREQ,
    PAGE_RECORD
} app_page_t;""",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("C 语言代码理解助手")
        self.resize(1420, 900)
        self._last_result = ""
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

        sample_title = QLabel("内置示例")
        sample_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #123b66;")
        left_layout.addWidget(sample_title)

        sample_row = QHBoxLayout()
        self.sample_combo = QComboBox()
        self.sample_combo.addItems(SAMPLE_SNIPPETS.keys())
        self.sample_combo.setStyleSheet(
            "QComboBox {background:#ffffff; color:#1d2b38; border:2px solid #d8e6f4; border-radius:12px; font-size:15px; padding:8px;}"
        )
        self.load_sample_button = QPushButton("载入示例")
        self.load_sample_button.setStyleSheet(
            "QPushButton {background:#2f80ed; color:white; font-size:15px; font-weight:700; border:none; border-radius:12px; padding:12px 16px;}"
            "QPushButton:hover {background:#276fd0;}"
        )
        sample_row.addWidget(self.sample_combo, 1)
        sample_row.addWidget(self.load_sample_button)
        left_layout.addLayout(sample_row)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText(
            "例如：粘贴 app.c 里的某个页面函数、按键函数、参数结构体或判断逻辑。"
        )
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

        self.requirement_card = QTextEdit()
        self.requirement_card.setReadOnly(True)
        self.requirement_card.setMaximumHeight(110)
        self.requirement_card.setStyleSheet(
            "QTextEdit {background:#eef9f1; color:#22543d; border:2px solid #b9e5c7; border-radius:14px; font-size:16px; padding:10px;}"
        )
        right_layout.addWidget(self.requirement_card)

        row_top = QHBoxLayout()
        row_bottom = QHBoxLayout()
        row_bottom2 = QHBoxLayout()
        row_bottom3 = QHBoxLayout()
        right_layout.addLayout(row_top)
        right_layout.addLayout(row_bottom)
        right_layout.addLayout(row_bottom2)
        right_layout.addLayout(row_bottom3)

        self.syntax_card = self._make_card("这段代码用了什么语法")
        self.feature_card = self._make_card("这段代码里识别到了什么")
        self.action_card = self._make_card("这段代码具体做了哪些动作")
        self.steps_card = self._make_card("建议按什么顺序看")
        self.explain_card = self._make_card("这段代码大概在做什么")
        self.term_card = self._make_card("这段代码里的术语怎么理解")
        self.modify_card = self._make_card("如果你要改这段代码，先看哪里")

        row_top.addLayout(self.syntax_card["layout"])
        row_top.addLayout(self.feature_card["layout"])
        row_bottom.addLayout(self.steps_card["layout"])
        row_bottom.addLayout(self.explain_card["layout"])
        row_bottom2.addLayout(self.action_card["layout"])
        row_bottom2.addLayout(self.term_card["layout"])
        row_bottom3.addLayout(self.modify_card["layout"])

        self.copy_button = QPushButton("复制讲解结果")
        self.copy_button.setStyleSheet(
            "QPushButton {background:#2f80ed; color:white; font-size:16px; font-weight:700; border:none; border-radius:12px; padding:14px 18px;}"
            "QPushButton:hover {background:#276fd0;}"
        )
        right_layout.addWidget(self.copy_button)

        self.load_sample_button.clicked.connect(self.handle_load_sample)
        self.analyze_button.clicked.connect(self.handle_analyze)
        self.clear_button.clicked.connect(self.handle_clear)
        self.copy_button.clicked.connect(self.handle_copy)

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

    def handle_load_sample(self) -> None:
        sample_name = self.sample_combo.currentText()
        self.code_input.setPlainText(SAMPLE_SNIPPETS.get(sample_name, ""))

    def handle_analyze(self) -> None:
        try:
            result = analyze_code(self.code_input.toPlainText())
        except Exception as exc:
            QMessageBox.warning(self, "讲解失败", str(exc))
            return

        self.scene_card.setPlainText(result["scene"])
        self.requirement_card.setPlainText(result["requirement_text"])
        self.syntax_card["box"].setPlainText(result["summary_text"])
        self.feature_card["box"].setPlainText(result["feature_text"])
        self.action_card["box"].setPlainText(result["action_text"])
        self.steps_card["box"].setPlainText(result["reading_steps_text"])
        self.explain_card["box"].setPlainText(result["explanation_text"])
        self.term_card["box"].setPlainText(result["term_text"])
        self.modify_card["box"].setPlainText(result["modify_hint_text"])

        self._last_result = (
            f"代码归类：{result['scene']}\n\n"
            f"这段代码更像对应哪类赛题要求：\n{result['requirement_text']}\n\n"
            f"这段代码用了什么语法：\n{result['summary_text']}\n\n"
            f"这段代码里的术语怎么理解：\n{result['term_text']}\n\n"
            f"如果你要改这段代码，先看哪里：\n{result['modify_hint_text']}\n\n"
            f"这段代码里识别到了什么：\n{result['feature_text']}\n\n"
            f"这段代码具体做了哪些动作：\n{result['action_text']}\n\n"
            f"建议按什么顺序看：\n{result['reading_steps_text']}\n\n"
            f"这段代码大概在做什么：\n{result['explanation_text']}"
        )

    def handle_clear(self) -> None:
        self.code_input.clear()
        self.scene_card.clear()
        self.requirement_card.clear()
        self.syntax_card["box"].clear()
        self.feature_card["box"].clear()
        self.action_card["box"].clear()
        self.steps_card["box"].clear()
        self.explain_card["box"].clear()
        self.term_card["box"].clear()
        self.modify_card["box"].clear()
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
