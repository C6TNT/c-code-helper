from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from core.ai_client import (
        AIClientError,
        build_ai_cards,
        run_ai_explanation,
        test_ai_connection,
    )
    from core.config_store import (
        DEFAULT_BASE_URL,
        DEFAULT_MODEL,
        load_ai_config,
        mask_api_key,
        save_ai_config,
    )
    from core.engine import analyze_code
except ModuleNotFoundError:
    from ..core.ai_client import (
        AIClientError,
        build_ai_cards,
        run_ai_explanation,
        test_ai_connection,
    )
    from ..core.config_store import (
        DEFAULT_BASE_URL,
        DEFAULT_MODEL,
        load_ai_config,
        mask_api_key,
        save_ai_config,
    )
    from ..core.engine import analyze_code


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
    "参数保存函数": """static void App_SaveParam(void)
{
    AT24C02_WriteByte(0x00, (u8)(g_param.temp_limit_x10 / 10));
    AT24C02_WriteByte(0x01, (u8)(g_param.temp_limit_x10 % 10));
    AT24C02_WriteByte(0x02, (u8)g_param.dist_limit);
    AT24C02_WriteByte(0x03, g_param.adc_limit);
}""",
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
}


def _load_app_version() -> str:
    version_path = Path(__file__).resolve().parents[2] / "VERSION"
    try:
        return version_path.read_text(encoding="utf-8").strip() or "V0.x"
    except Exception:
        return "V0.x"


class AIExplainWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, payload_json: str) -> None:
        super().__init__()
        self.payload_json = payload_json

    def run(self) -> None:
        try:
            text = run_ai_explanation(self.payload_json)
            self.succeeded.emit(text)
        except AIClientError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"AI 讲解过程中发生未预期异常：{exc}")


class AITestWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def run(self) -> None:
        try:
            text = test_ai_connection()
            self.succeeded.emit(text)
        except AIClientError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"连接测试过程中发生未预期异常：{exc}")


class AISettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI 设置")
        self.resize(560, 240)

        config = load_ai_config()

        self.api_key_edit = QLineEdit(config.get("api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("在这里粘贴 API Key")

        self.base_url_edit = QLineEdit(config.get("base_url", DEFAULT_BASE_URL))
        self.base_url_edit.setPlaceholderText(DEFAULT_BASE_URL)

        self.model_edit = QLineEdit(config.get("model", DEFAULT_MODEL))
        self.model_edit.setPlaceholderText(DEFAULT_MODEL)

        form = QFormLayout()
        form.addRow("API Key", self.api_key_edit)
        form.addRow("Base URL", self.base_url_edit)
        form.addRow("Model", self.model_edit)

        tip = QLabel(
            "说明：配置会保存在当前应用目录下的 config.json。\n"
            "推荐直接在这里设置，不需要再打开 PowerShell。"
        )
        tip.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.handle_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(tip)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def handle_save(self) -> None:
        save_ai_config(
            self.api_key_edit.text(),
            self.base_url_edit.text(),
            self.model_edit.text(),
        )
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.app_version = _load_app_version()
        self.setWindowTitle("C 语言代码理解助手")
        self.resize(1760, 1080)
        self._last_result = ""
        self._last_ai_text = ""
        self._last_ai_payload_json = ""
        self.ai_worker = None
        self.ai_test_worker = None
        self._build_ui()
        self.refresh_ai_status()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        left_layout = QVBoxLayout()
        center_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(center_layout, 6)
        main_layout.addLayout(right_layout, 4)

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
        self.sample_combo.setStyleSheet(self._combo_style())
        self.load_sample_button = QPushButton("载入示例")
        self.load_sample_button.setStyleSheet(self._button_style())
        sample_row.addWidget(self.sample_combo, 1)
        sample_row.addWidget(self.load_sample_button)
        left_layout.addLayout(sample_row)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText(
            "例如：粘贴 app.c 里的某个页面函数、按键函数、参数结构体、保存函数或判断逻辑。"
        )
        self.code_input.setStyleSheet(self._text_style())
        left_layout.addWidget(self.code_input, 1)

        left_button_row = QHBoxLayout()
        self.analyze_button = QPushButton("开始讲解")
        self.clear_button = QPushButton("清空")
        self.copy_button = QPushButton("复制讲解结果")
        for button in (self.analyze_button, self.clear_button, self.copy_button):
            button.setStyleSheet(self._button_style())
            left_button_row.addWidget(button)
        left_layout.addLayout(left_button_row)

        title_center = QLabel("本地规则讲解")
        title_center.setStyleSheet("font-size: 26px; font-weight: 700; color: #123b66;")
        center_layout.addWidget(title_center)

        self.scene_card = self._make_top_card("#fff5eb", "#6d3d11", "#f3d1ac")
        center_layout.addLayout(self._wrap_section("这段代码更像哪类逻辑", self.scene_card))

        self.requirement_card = self._make_top_card("#eef9f1", "#22543d", "#b9e5c7")
        center_layout.addLayout(self._wrap_section("这段代码更像对应哪类赛题要求", self.requirement_card))

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()
        row4 = QHBoxLayout()
        row5 = QHBoxLayout()
        row6 = QHBoxLayout()
        row7 = QHBoxLayout()
        center_layout.addLayout(row1)
        center_layout.addLayout(row2)
        center_layout.addLayout(row3)
        center_layout.addLayout(row4)
        center_layout.addLayout(row5)
        center_layout.addLayout(row6)
        center_layout.addLayout(row7)

        self.syntax_card = self._make_card("这段代码用了什么语法")
        self.feature_card = self._make_card("这段代码里识别到了什么")
        self.action_card = self._make_card("这段代码具体做了哪些动作")
        self.dependency_card = self._make_card("这段代码依赖谁")
        self.related_function_card = self._make_card("这段代码和模板里哪几个函数最相关")
        self.linked_variable_card = self._make_card("这段代码常和哪些变量一起联动")
        self.sync_check_card = self._make_card("改完这里后还要同步检查哪几处")
        self.call_context_card = self._make_card("这段代码大概会在哪里被调用")
        self.file_link_card = self._make_card("这段代码更可能在哪些 .c/.h 文件里成套出现")
        self.impact_card = self._make_card("改这里会影响哪里")
        self.steps_card = self._make_card("建议按什么顺序看")
        self.execution_card = self._make_card("代码执行链")
        self.term_card = self._make_card("术语怎么理解")
        self.modify_card = self._make_card("如果你要改这段代码，先看哪里")

        row1.addLayout(self.syntax_card["layout"])
        row1.addLayout(self.feature_card["layout"])
        row2.addLayout(self.action_card["layout"])
        row2.addLayout(self.dependency_card["layout"])
        row3.addLayout(self.related_function_card["layout"])
        row3.addLayout(self.linked_variable_card["layout"])
        row4.addLayout(self.sync_check_card["layout"])
        row4.addLayout(self.call_context_card["layout"])
        row5.addLayout(self.file_link_card["layout"])
        row5.addLayout(self.impact_card["layout"])
        row6.addLayout(self.steps_card["layout"])
        row6.addLayout(self.execution_card["layout"])
        row7.addLayout(self.term_card["layout"])
        row7.addLayout(self.modify_card["layout"])

        title_right = QLabel("AI 深入讲解")
        title_right.setStyleSheet("font-size: 26px; font-weight: 700; color: #123b66;")
        right_layout.addWidget(title_right)

        self.ai_status_label = QLabel()
        self.ai_status_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #335b82;")
        right_layout.addWidget(self.ai_status_label)

        self.ai_card_what = self._make_top_card("#f3f0ff", "#4a2e7a", "#d8c9ff")
        right_layout.addLayout(self._wrap_section("这段代码更像在干什么", self.ai_card_what))

        self.ai_card_focus = self._make_top_card("#eef6ff", "#1d4f91", "#c7dcfb")
        right_layout.addLayout(self._wrap_section("你应该先盯住哪几个点", self.ai_card_focus))

        self.ai_card_risk = self._make_top_card("#fff7ec", "#7a4a15", "#efcf99")
        right_layout.addLayout(self._wrap_section("如果你准备改它，最容易漏掉哪里", self.ai_card_risk))

        self.ai_edit = QTextEdit()
        self.ai_edit.setReadOnly(True)
        self.ai_edit.setPlaceholderText("这里会显示 AI 深入讲解结果。")
        self.ai_edit.setStyleSheet(self._ai_box_style())
        right_layout.addWidget(self.ai_edit, 1)

        ai_button_row1 = QHBoxLayout()
        ai_button_row2 = QHBoxLayout()
        self.ai_button = QPushButton("AI 深入讲解")
        self.ai_settings_button = QPushButton("AI 设置")
        self.ai_test_button = QPushButton("测试连接")
        self.copy_ai_button = QPushButton("复制 AI 内容")
        self.copy_ai_summary_button = QPushButton("复制 AI 摘要")
        self.about_button = QPushButton("关于 / 版本")
        self.copy_ai_what_button = QPushButton("复制作用卡")
        self.copy_ai_focus_button = QPushButton("复制重点卡")
        self.copy_ai_risk_button = QPushButton("复制漏改卡")
        for button in (
            self.ai_button,
            self.ai_settings_button,
            self.ai_test_button,
            self.copy_ai_button,
            self.copy_ai_summary_button,
            self.about_button,
            self.copy_ai_what_button,
            self.copy_ai_focus_button,
            self.copy_ai_risk_button,
        ):
            button.setStyleSheet(self._button_style())

        ai_button_row1.addWidget(self.ai_button)
        ai_button_row1.addWidget(self.ai_settings_button)
        ai_button_row1.addWidget(self.ai_test_button)
        ai_button_row1.addWidget(self.about_button)
        ai_button_row2.addWidget(self.copy_ai_button)
        ai_button_row2.addWidget(self.copy_ai_summary_button)
        ai_button_row2.addWidget(self.copy_ai_what_button)
        ai_button_row2.addWidget(self.copy_ai_focus_button)
        ai_button_row2.addWidget(self.copy_ai_risk_button)
        right_layout.addLayout(ai_button_row1)
        right_layout.addLayout(ai_button_row2)

        tip_title = QLabel("使用提示")
        tip_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #123b66;")
        right_layout.addWidget(tip_title)
        self.tip_edit = QTextEdit()
        self.tip_edit.setReadOnly(True)
        self.tip_edit.setStyleSheet(self._tip_box_style())
        self.tip_edit.setPlainText(
            "使用建议：\n"
            "1. 先用本地规则讲解看清这段代码属于哪类逻辑\n"
            "2. 再看联动变量、同步检查点和文件联动提示\n"
            "3. 如果还觉得抽象，再点“AI 深入讲解”\n"
            "4. AI 设置建议直接在应用里配置，不需要打开终端\n"
            "5. 如果不确定配置对不对，先点“测试连接”"
        )
        right_layout.addWidget(self.tip_edit)

        self.load_sample_button.clicked.connect(self.handle_load_sample)
        self.analyze_button.clicked.connect(self.handle_analyze)
        self.clear_button.clicked.connect(self.handle_clear)
        self.copy_button.clicked.connect(self.handle_copy)
        self.ai_button.clicked.connect(self.handle_ai_explain)
        self.ai_settings_button.clicked.connect(self.handle_open_ai_settings)
        self.ai_test_button.clicked.connect(self.handle_test_ai_connection)
        self.copy_ai_button.clicked.connect(self.handle_copy_ai)
        self.copy_ai_summary_button.clicked.connect(self.handle_copy_ai_summary)
        self.copy_ai_what_button.clicked.connect(lambda: self.handle_copy_ai_card(self.ai_card_what, "作用卡片"))
        self.copy_ai_focus_button.clicked.connect(lambda: self.handle_copy_ai_card(self.ai_card_focus, "重点卡片"))
        self.copy_ai_risk_button.clicked.connect(lambda: self.handle_copy_ai_card(self.ai_card_risk, "漏改卡片"))
        self.about_button.clicked.connect(self.handle_show_about)

    def _button_style(self) -> str:
        return (
            "QPushButton {background:#2f80ed; color:white; font-size:16px; font-weight:700; "
            "border:none; border-radius:12px; padding:14px 18px;}"
            "QPushButton:hover {background:#276fd0;}"
        )

    def _combo_style(self) -> str:
        return (
            "QComboBox {background:#ffffff; color:#1d2b38; border:2px solid #d8e6f4; "
            "border-radius:12px; font-size:15px; padding:8px;}"
        )

    def _text_style(self) -> str:
        return (
            "QTextEdit {background:#ffffff; color:#1d2b38; border:2px solid #d8e6f4; "
            "border-radius:14px; font-size:16px; padding:10px;}"
        )

    def _card_style(self) -> str:
        return (
            "QTextEdit {background:#eef6ff; color:#1d2b38; border:2px solid #d7e8fb; "
            "border-radius:14px; font-size:15px; padding:10px;}"
        )

    def _ai_box_style(self) -> str:
        return (
            "QTextEdit {background:#eef8f2; color:#1d2b38; border:2px solid #cfe8d7; "
            "border-radius:14px; font-size:15px; padding:10px;}"
        )

    def _tip_box_style(self) -> str:
        return (
            "QTextEdit {background:#fff9e8; color:#5c4510; border:2px solid #f3dc9a; "
            "border-radius:14px; font-size:15px; padding:10px;}"
        )

    def _make_top_card(self, bg: str, fg: str, border: str) -> QTextEdit:
        box = QTextEdit()
        box.setReadOnly(True)
        box.setMaximumHeight(100)
        box.setStyleSheet(
            f"QTextEdit {{background:{bg}; color:{fg}; border:2px solid {border}; "
            "border-radius:14px; font-size:16px; padding:10px;}"
        )
        return box

    def _wrap_section(self, title: str, widget: QTextEdit) -> QVBoxLayout:
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size: 18px; font-weight: 700; color: #123b66;")
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def _make_card(self, title: str) -> dict:
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size: 18px; font-weight: 700; color: #123b66;")
        box = QTextEdit()
        box.setReadOnly(True)
        box.setMinimumHeight(165)
        box.setStyleSheet(self._card_style())
        layout.addWidget(label)
        layout.addWidget(box)
        return {"layout": layout, "box": box}

    def refresh_ai_status(self) -> None:
        config = load_ai_config()
        masked = mask_api_key(config.get("api_key", ""))
        self.ai_status_label.setText(
            f"当前 AI 配置：Key-{masked} | Model-{config.get('model', DEFAULT_MODEL) or DEFAULT_MODEL}"
        )

    def build_ai_payload_json(self) -> str:
        if not self._last_result:
            return ""

        payload = {
            "task": "解释一段蓝桥杯单片机模板代码",
            "code": self.code_input.toPlainText().strip(),
            "local_analysis": self._last_result,
            "app_version": self.app_version,
        }
        return json_dump(payload)

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
        self.dependency_card["box"].setPlainText(result["dependency_text"])
        self.related_function_card["box"].setPlainText(result["related_function_text"])
        self.linked_variable_card["box"].setPlainText(result["linked_variable_text"])
        self.sync_check_card["box"].setPlainText(result["sync_check_text"])
        self.call_context_card["box"].setPlainText(result["call_context_text"])
        self.file_link_card["box"].setPlainText(result["file_link_text"])
        self.impact_card["box"].setPlainText(result["impact_text"])
        self.steps_card["box"].setPlainText(result["reading_steps_text"])
        self.execution_card["box"].setPlainText(result["execution_chain_text"])
        self.term_card["box"].setPlainText(result["term_text"])
        self.modify_card["box"].setPlainText(result["modify_hint_text"])

        self._last_result = (
            f"代码归类：{result['scene']}\n\n"
            f"这段代码更像对应哪类赛题要求：\n{result['requirement_text']}\n\n"
            f"这段代码用了什么语法：\n{result['summary_text']}\n\n"
            f"这段代码里识别到了什么：\n{result['feature_text']}\n\n"
            f"这段代码具体做了哪些动作：\n{result['action_text']}\n\n"
            f"这段代码依赖谁：\n{result['dependency_text']}\n\n"
            f"这段代码和模板里哪几个函数最相关：\n{result['related_function_text']}\n\n"
            f"这段代码常和哪些变量一起联动：\n{result['linked_variable_text']}\n\n"
            f"改完这里后还要同步检查哪几处：\n{result['sync_check_text']}\n\n"
            f"这段代码大概会在哪里被调用：\n{result['call_context_text']}\n\n"
            f"这段代码更可能在哪些 .c/.h 文件里成套出现：\n{result['file_link_text']}\n\n"
            f"改这里会影响哪里：\n{result['impact_text']}\n\n"
            f"建议按什么顺序看：\n{result['reading_steps_text']}\n\n"
            f"代码执行链：\n{result['execution_chain_text']}\n\n"
            f"术语怎么理解：\n{result['term_text']}\n\n"
            f"如果你要改这段代码，先看哪里：\n{result['modify_hint_text']}"
        )
        self._last_ai_payload_json = self.build_ai_payload_json()
        self.ai_card_what.clear()
        self.ai_card_focus.clear()
        self.ai_card_risk.clear()
        self.ai_edit.clear()
        self._last_ai_text = ""

    def handle_ai_explain(self) -> None:
        if not self._last_ai_payload_json:
            QMessageBox.information(self, "提示", "先点击“开始讲解”，再做 AI 深入讲解。")
            return

        self.ai_button.setEnabled(False)
        self.ai_button.setText("AI 讲解中...")
        self.ai_edit.setPlainText("正在请求 AI，请稍等...")
        self.ai_worker = AIExplainWorker(self._last_ai_payload_json)
        self.ai_worker.succeeded.connect(self.on_ai_explain_success)
        self.ai_worker.failed.connect(self.on_ai_explain_failed)
        self.ai_worker.finished.connect(self.on_ai_explain_finished)
        self.ai_worker.start()

    def on_ai_explain_success(self, text: str) -> None:
        self._last_ai_text = text
        self.ai_edit.setPlainText(text)
        cards = build_ai_cards(text)
        self.ai_card_what.setPlainText(cards["what"])
        self.ai_card_focus.setPlainText(cards["focus"])
        self.ai_card_risk.setPlainText(cards["risk"])

    def on_ai_explain_failed(self, text: str) -> None:
        self.ai_edit.setPlainText(text)
        self.ai_card_what.setPlainText("")
        self.ai_card_focus.setPlainText("")
        self.ai_card_risk.setPlainText("")

    def on_ai_explain_finished(self) -> None:
        self.ai_button.setEnabled(True)
        self.ai_button.setText("AI 深入讲解")

    def handle_open_ai_settings(self) -> None:
        dialog = AISettingsDialog(self)
        if dialog.exec():
            self.refresh_ai_status()
            QMessageBox.information(self, "提示", "AI 配置已保存。")

    def handle_test_ai_connection(self) -> None:
        self.ai_test_button.setEnabled(False)
        self.ai_test_button.setText("测试中...")
        self.ai_test_worker = AITestWorker()
        self.ai_test_worker.succeeded.connect(self.on_ai_test_success)
        self.ai_test_worker.failed.connect(self.on_ai_test_failed)
        self.ai_test_worker.finished.connect(self.on_ai_test_finished)
        self.ai_test_worker.start()

    def on_ai_test_success(self, text: str) -> None:
        QMessageBox.information(self, "测试连接", text)

    def on_ai_test_failed(self, text: str) -> None:
        QMessageBox.warning(self, "测试连接", text)

    def on_ai_test_finished(self) -> None:
        self.ai_test_button.setEnabled(True)
        self.ai_test_button.setText("测试连接")

    def handle_copy(self) -> None:
        if not self._last_result:
            QMessageBox.information(self, "提示", "现在还没有讲解结果，先点击“开始讲解”。")
            return
        QApplication.clipboard().setText(self._last_result)
        QMessageBox.information(self, "提示", "讲解结果已经复制到剪贴板。")

    def handle_copy_ai(self) -> None:
        if not self.ai_edit.toPlainText().strip():
            QMessageBox.information(self, "提示", "现在还没有 AI 内容，先点击“AI 深入讲解”。")
            return
        QApplication.clipboard().setText(self.ai_edit.toPlainText())
        QMessageBox.information(self, "提示", "AI 内容已经复制到剪贴板。")

    def handle_copy_ai_summary(self) -> None:
        if not self.ai_edit.toPlainText().strip():
            QMessageBox.information(self, "提示", "现在还没有 AI 内容，先点击“AI 深入讲解”。")
            return
        summary = (
            "AI 摘要\n\n"
            f"1. 这段代码更像在干什么\n{self.ai_card_what.toPlainText().strip() or '暂未生成'}\n\n"
            f"2. 你应该先盯住哪几个点\n{self.ai_card_focus.toPlainText().strip() or '暂未生成'}\n\n"
            f"3. 如果你准备改它，最容易漏掉哪里\n{self.ai_card_risk.toPlainText().strip() or '暂未生成'}"
        )
        QApplication.clipboard().setText(summary)
        QMessageBox.information(self, "提示", "AI 摘要已经复制到剪贴板。")

    def handle_copy_ai_card(self, widget: QTextEdit, card_name: str) -> None:
        text = widget.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", f"{card_name}现在还没有内容。")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "提示", f"{card_name}已经复制到剪贴板。")

    def handle_show_about(self) -> None:
        QMessageBox.information(
            self,
            "关于 / 版本",
            "C 语言代码理解助手\n\n"
            f"当前版本：{self.app_version}\n"
            "定位：面向蓝桥杯单片机新生的模板代码理解与改题辅助工具。\n\n"
            "仓库地址：\n"
            "https://github.com/C6TNT/c-code-helper",
        )

    def handle_clear(self) -> None:
        self.code_input.clear()
        self.scene_card.clear()
        self.requirement_card.clear()
        self.syntax_card["box"].clear()
        self.feature_card["box"].clear()
        self.action_card["box"].clear()
        self.dependency_card["box"].clear()
        self.related_function_card["box"].clear()
        self.linked_variable_card["box"].clear()
        self.sync_check_card["box"].clear()
        self.call_context_card["box"].clear()
        self.file_link_card["box"].clear()
        self.impact_card["box"].clear()
        self.steps_card["box"].clear()
        self.execution_card["box"].clear()
        self.term_card["box"].clear()
        self.modify_card["box"].clear()
        self.ai_card_what.clear()
        self.ai_card_focus.clear()
        self.ai_card_risk.clear()
        self.ai_edit.clear()
        self._last_result = ""
        self._last_ai_text = ""
        self._last_ai_payload_json = ""


def json_dump(payload: dict) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_app() -> None:
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
