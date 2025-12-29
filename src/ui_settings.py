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
    QSlider,
)
from PySide6.QtCore import Qt, Signal

from utils import get_app_icon
import constants

logger = logging.getLogger(__name__)


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

        self.chinese_hotkey_edit = QLineEdit()
        hotkey_form.addRow("翻译为中文:", self.chinese_hotkey_edit)

        self.english_hotkey_edit = QLineEdit()
        hotkey_form.addRow("翻译为英文:", self.english_hotkey_edit)

        self.emoji_hotkey_edit = QLineEdit()
        hotkey_form.addRow("生成Emoji:", self.emoji_hotkey_edit)

        self.explanation_label = QLabel("详细格式参考 python keyboard 库格式要求")
        hotkey_form.addRow(self.explanation_label)

        self.example_label = QLabel("示例: Ctrl+Shift+F2 或 alt+t 或 F2 或 space+2 等")
        hotkey_form.addRow(self.example_label)

        hotkey_layout.addWidget(hotkey_group)
        hotkey_layout.addStretch()

        # 窗口设置标签页
        window_tab = QWidget()
        window_layout = QVBoxLayout(window_tab)

        window_group = QGroupBox("窗口设置")
        window_form = QFormLayout(window_group)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(95)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_label = QLabel("95%")
        self.opacity_label.setFixedWidth(40)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        window_form.addRow("窗口透明度:", opacity_layout)

        window_layout.addWidget(window_group)
        window_layout.addStretch()

        # API设置标签页
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # API配置
        api_group = QGroupBox("API设置")
        api_form = QFormLayout(api_group)

        # Chat API配置
        chat_label = QLabel("通用聊天模型配置")
        chat_label.setStyleSheet("font-weight: bold; color: #A23B72; margin-top: 10px;")
        api_form.addRow(chat_label)

        self.chat_api_key_edit = QLineEdit()
        self.chat_api_key_edit.setEchoMode(QLineEdit.Password)
        api_form.addRow("API密钥:", self.chat_api_key_edit)

        self.chat_api_url_edit = QLineEdit()
        api_form.addRow("API URL:", self.chat_api_url_edit)

        self.chat_api_model_edit = QLineEdit()
        api_form.addRow("API模型:", self.chat_api_model_edit)

        api_layout.addWidget(api_group)
        api_layout.addStretch()

        tab_widget.addTab(hotkey_tab, "快捷键")
        tab_widget.addTab(window_tab, "窗口")
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

    def load_config(self):
        self.chinese_hotkey_edit.setText(self.config.get("hotkey_to_chinese", "f2"))
        self.english_hotkey_edit.setText(self.config.get("hotkey_to_english", "f4"))
        self.emoji_hotkey_edit.setText(self.config.get("hotkey_to_emoji", constants.DEFAULT_HOTKEY_TO_EMOJI))

        opacity = int(self.config.get("window_opacity", 95))
        self.opacity_slider.setValue(opacity)
        self.opacity_label.setText(f"{opacity}%")

        # 加载Chat配置
        self.chat_api_key_edit.setText(self.config.get("chat_api_key", ""))
        self.chat_api_url_edit.setText(self.config.get("chat_api_url", ""))
        self.chat_api_model_edit.setText(self.config.get("chat_api_model", ""))

    def update_opacity_label(self):
        value = self.opacity_slider.value()
        self.opacity_label.setText(f"{value}%")

    def save_settings(self):
        new_config = {
            "hotkey_to_chinese": self.chinese_hotkey_edit.text(),
            "hotkey_to_english": self.english_hotkey_edit.text(),
            "hotkey_to_emoji": self.emoji_hotkey_edit.text(),
            "window_opacity": self.opacity_slider.value() / 100.0,
            # Chat配置
            "chat_api_key": self.chat_api_key_edit.text(),
            "chat_api_url": self.chat_api_url_edit.text(),
            "chat_api_model": self.chat_api_model_edit.text(),
        }

        self.settings_saved.emit(new_config)
        self.accept()