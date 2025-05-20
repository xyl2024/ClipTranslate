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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import logging
from utils import get_app_icon

logger = logging.getLogger(__name__)


class HotkeyEdit(QLineEdit):
    """自定义组件用于捕获键盘快捷键"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("点击此处按下快捷键")

    def keyPressEvent(self, event):
        # 简单处理，实际应用中可能需要更复杂的逻辑
        key_text = event.text().lower()
        if key_text:
            if event.modifiers() & Qt.ControlModifier:
                key_text = "ctrl+" + key_text
            if event.modifiers() & Qt.AltModifier:
                key_text = "alt+" + key_text
            if event.modifiers() & Qt.ShiftModifier:
                key_text = "shift+" + key_text

            # 处理功能键
            key = event.key()
            if Qt.Key_F1 <= key <= Qt.Key_F12:
                key_text = f"f{key - Qt.Key_F1 + 1}"

            self.setText(key_text)
            event.accept()


class UiSettings(QDialog):
    settings_saved = Signal(dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)

        # 设置窗口图标
        self.setWindowIcon(get_app_icon("app_icon.png"))

        # 设置为非模态窗口
        self.setWindowModality(Qt.NonModal)

        # 避免关闭窗口时退出应用程序
        self.setAttribute(Qt.WA_QuitOnClose, False)

        self.config = config
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建标签页
        tab_widget = QTabWidget()

        # 快捷键设置页
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

        # API设置页
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        api_group = QGroupBox("API设置")
        api_form = QFormLayout(api_group)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        api_form.addRow("API密钥:", self.api_key_edit)

        self.api_url_edit = QLineEdit()
        api_form.addRow("API URL:", self.api_url_edit)

        self.api_model_edit = QLineEdit()
        api_form.addRow("API模型:", self.api_model_edit)

        api_layout.addWidget(api_group)
        api_layout.addStretch()

        # 添加标签页
        tab_widget.addTab(hotkey_tab, "快捷键")
        tab_widget.addTab(api_tab, "API设置")

        layout.addWidget(tab_widget)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def load_config(self):
        self.chinese_hotkey_edit.setText(self.config.get("hotkey_to_chinese", "f2"))
        self.english_hotkey_edit.setText(self.config.get("hotkey_to_english", "f3"))
        self.api_key_edit.setText(self.config.get("api_key", ""))
        self.api_url_edit.setText(self.config.get("api_url", ""))
        self.api_model_edit.setText(self.config.get("api_model", ""))

    def save_settings(self):
        new_config = {
            "hotkey_to_chinese": self.chinese_hotkey_edit.text(),
            "hotkey_to_english": self.english_hotkey_edit.text(),
            "api_key": self.api_key_edit.text(),
            "api_url": self.api_url_edit.text(),
            "api_model": self.api_model_edit.text(),
        }

        self.settings_saved.emit(new_config)
        self.accept()
