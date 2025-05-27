import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QGroupBox,
    QTabWidget,
    QComboBox,
    QLabel,
)
from PySide6.QtCore import Qt, Signal

from utils import get_app_icon

logger = logging.getLogger(__name__)


class HotkeyEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("点击此处按下快捷键")

    def keyPressEvent(self, event):
        # 简单处理，实际应用中可能需要更复杂的逻辑
        # todo
        key_text = event.text().lower()
        if key_text:
            if event.modifiers() & Qt.ControlModifier:
                key_text = "ctrl+" + key_text
            if event.modifiers() & Qt.AltModifier:
                key_text = "alt+" + key_text
            if event.modifiers() & Qt.ShiftModifier:
                key_text = "shift+" + key_text

            key = event.key()
            if Qt.Key_F1 <= key <= Qt.Key_F12:
                key_text = f"f{key - Qt.Key_F1 + 1}"

            self.setText(key_text)
            event.accept()


class UiSettings(QDialog):
    settings_saved = Signal(dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ClipTranslate - 设置")
        self.setMinimumWidth(450)

        self.setWindowIcon(get_app_icon("app_icon.png"))
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_QuitOnClose, False)

        self.config = config
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()

        # 快捷键设置标签页
        hotkey_tab = QWidget()
        hotkey_layout = QVBoxLayout(hotkey_tab)

        hotkey_group = QGroupBox("快捷键设置")
        hotkey_form = QFormLayout(hotkey_group)

        self.chinese_hotkey_edit = HotkeyEdit()
        hotkey_form.addRow("翻译为中文:", self.chinese_hotkey_edit)

        self.english_hotkey_edit = HotkeyEdit()
        hotkey_form.addRow("翻译为英文:", self.english_hotkey_edit)

        hotkey_layout.addWidget(hotkey_group)
        hotkey_layout.addStretch()

        # API设置标签页
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # 翻译器类型选择
        translator_group = QGroupBox("翻译器类型")
        translator_form = QFormLayout(translator_group)

        self.translator_type_combo = QComboBox()
        self.translator_type_combo.addItem("Qwen专用翻译模型", "qwen")
        self.translator_type_combo.addItem("通用聊天模型", "chat")
        self.translator_type_combo.currentTextChanged.connect(
            self.on_translator_type_changed
        )
        translator_form.addRow("翻译器类型:", self.translator_type_combo)

        # 添加说明标签
        self.translator_help_label = QLabel()
        self.translator_help_label.setWordWrap(True)
        self.translator_help_label.setStyleSheet(
            "color: #666; font-size: 11px; margin: 5px;"
        )
        translator_form.addRow("", self.translator_help_label)

        # 添加当前配置状态提示
        self.config_status_label = QLabel()
        self.config_status_label.setWordWrap(True)
        self.config_status_label.setStyleSheet(
            "color: #2E86AB; font-size: 10px; margin: 5px; font-weight: bold;"
        )
        translator_form.addRow("", self.config_status_label)

        api_layout.addWidget(translator_group)

        # API配置
        api_group = QGroupBox("API设置")
        api_form = QFormLayout(api_group)

        # Qwen API配置
        qwen_label = QLabel("Qwen专用翻译模型配置")
        qwen_label.setStyleSheet("font-weight: bold; color: #2E86AB; margin-top: 10px;")
        api_form.addRow(qwen_label)

        self.qwen_api_key_edit = QLineEdit()
        self.qwen_api_key_edit.setEchoMode(QLineEdit.Password)
        api_form.addRow("Qwen API密钥:", self.qwen_api_key_edit)

        self.qwen_api_url_edit = QLineEdit()
        api_form.addRow("Qwen API URL:", self.qwen_api_url_edit)

        self.qwen_api_model_edit = QLineEdit()
        api_form.addRow("Qwen API模型:", self.qwen_api_model_edit)

        # 添加分隔线
        separator_label = QLabel()
        separator_label.setStyleSheet("border-bottom: 1px solid #ccc; margin: 10px 0;")
        api_form.addRow(separator_label)

        # Chat API配置
        chat_label = QLabel("通用聊天模型配置")
        chat_label.setStyleSheet("font-weight: bold; color: #A23B72; margin-top: 10px;")
        api_form.addRow(chat_label)

        self.chat_api_key_edit = QLineEdit()
        self.chat_api_key_edit.setEchoMode(QLineEdit.Password)
        api_form.addRow("Chat API密钥:", self.chat_api_key_edit)

        self.chat_api_url_edit = QLineEdit()
        api_form.addRow("Chat API URL:", self.chat_api_url_edit)

        self.chat_api_model_edit = QLineEdit()
        api_form.addRow("Chat API模型:", self.chat_api_model_edit)

        api_layout.addWidget(api_group)
        api_layout.addStretch()

        tab_widget.addTab(hotkey_tab, "快捷键")
        tab_widget.addTab(api_tab, "API设置")

        layout.addWidget(tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def on_translator_type_changed(self):
        current_data = self.translator_type_combo.currentData()
        if current_data == "qwen":
            help_text = (
                "Qwen专用翻译模型：使用阿里云的Qwen-MT模型，专门为翻译任务优化，"
                "翻译质量高，速度快。适合使用阿里云DashScope API。"
            )
        else:
            help_text = (
                "通用聊天模型：使用标准的聊天API格式，通过提示词进行翻译。"
                "兼容OpenAI API格式，支持更多模型选择（如GPT、Claude、本地模型等）。"
            )

        self.translator_help_label.setText(help_text)
        self._update_config_status()

    def _update_config_status(self):
        current_type = self.translator_type_combo.currentData()
        if current_type == "qwen":
            has_key = bool(self.qwen_api_key_edit.text().strip())
            has_url = bool(self.qwen_api_url_edit.text().strip())
            has_model = bool(self.qwen_api_model_edit.text().strip())
            status_text = f"Qwen配置状态：API密钥 {'✓' if has_key else '✗'} | API URL {'✓' if has_url else '✗'} | 模型 {'✓' if has_model else '✗'}"
        else:
            has_key = bool(self.chat_api_key_edit.text().strip())
            has_url = bool(self.chat_api_url_edit.text().strip())
            has_model = bool(self.chat_api_model_edit.text().strip())
            status_text = f"Chat配置状态：API密钥 {'✓' if has_key else '✗'} | API URL {'✓' if has_url else '✗'} | 模型 {'✓' if has_model else '✗'}"

        self.config_status_label.setText(status_text)

    def load_config(self):
        self.chinese_hotkey_edit.setText(self.config.get("hotkey_to_chinese", "f2"))
        self.english_hotkey_edit.setText(self.config.get("hotkey_to_english", "f3"))

        # 加载Qwen配置
        self.qwen_api_key_edit.setText(self.config.get("qwen_api_key", ""))
        self.qwen_api_url_edit.setText(self.config.get("qwen_api_url", ""))
        self.qwen_api_model_edit.setText(self.config.get("qwen_api_model", ""))

        # 加载Chat配置
        self.chat_api_key_edit.setText(self.config.get("chat_api_key", ""))
        self.chat_api_url_edit.setText(self.config.get("chat_api_url", ""))
        self.chat_api_model_edit.setText(self.config.get("chat_api_model", ""))

        # 设置翻译器类型
        translator_type = self.config.get("translator_type", "qwen")
        index = self.translator_type_combo.findData(translator_type)
        if index >= 0:
            self.translator_type_combo.setCurrentIndex(index)

        # 触发帮助文本更新
        self.on_translator_type_changed()

        # 连接文本变化事件以实时更新状态
        self.qwen_api_key_edit.textChanged.connect(self._update_config_status)
        self.qwen_api_url_edit.textChanged.connect(self._update_config_status)
        self.qwen_api_model_edit.textChanged.connect(self._update_config_status)
        self.chat_api_key_edit.textChanged.connect(self._update_config_status)
        self.chat_api_url_edit.textChanged.connect(self._update_config_status)
        self.chat_api_model_edit.textChanged.connect(self._update_config_status)

    def save_settings(self):
        new_config = {
            "hotkey_to_chinese": self.chinese_hotkey_edit.text(),
            "hotkey_to_english": self.english_hotkey_edit.text(),
            "translator_type": self.translator_type_combo.currentData(),
            # Qwen配置
            "qwen_api_key": self.qwen_api_key_edit.text(),
            "qwen_api_url": self.qwen_api_url_edit.text(),
            "qwen_api_model": self.qwen_api_model_edit.text(),
            # Chat配置
            "chat_api_key": self.chat_api_key_edit.text(),
            "chat_api_url": self.chat_api_url_edit.text(),
            "chat_api_model": self.chat_api_model_edit.text(),
        }

        self.settings_saved.emit(new_config)
        self.accept()
