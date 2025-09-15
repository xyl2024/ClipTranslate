import logging
import pyperclip
from PySide6.QtWidgets import (
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QProgressBar,
    QHBoxLayout,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Slot, QTimer

logger = logging.getLogger(__name__)

TEXT_AREA_CSS = """
    QTextEdit {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #ffffff, /* 白色 */
                                    stop:0.2 #d5f4e6, /* 淡绿色 */
                                    stop:0.4 #bee3f8, /* 淡蓝色 */
                                    stop:0.6 #f0e6f6, /* 淡紫色 */
                                    stop:0.8 #ffe9c7, /* 淡橙色 */
                                    stop:1 #ffffff); /* 白色 */
        border-radius: 8px;
        padding: 10px;
    }
    
    /* 滚动条整体样式 */
    QScrollBar:vertical {
        border: none;
        background: #f0f0f0;
        width: 10px;
        margin: 0px 0px 0px 0px;
        border-radius: 5px;
    }
    
    /* 滚动条滑块 */
    QScrollBar::handle:vertical {
        background: #c0c0c0;
        min-height: 30px;
        border-radius: 5px;
    }
    
    /* 鼠标悬停在滑块上的样式 */
    QScrollBar::handle:vertical:hover {
        background: #a0a0a0;
    }
    
    /* 滑块按下的样式 */
    QScrollBar::handle:vertical:pressed {
        background: #808080;
    }
    
    /* 上箭头区域 */
    QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    
    /* 下箭头区域 */
    QScrollBar::add-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    
    /* 滚动条上方和下方区域 */
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""

COPY_BUTTON_CSS = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""

COPYED_BUTTON_CSS = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        border-radius: 4px;
        padding: 5px 10px;
    }
"""

CLOSE_BUTTON_CSS = """
    QPushButton {
        background-color: #f44336;
        color: white;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #d32f2f;
    }
"""

PROGRESS_BAR_CSS = """
    QProgressBar {
        border: 2px solid #CCCCCC;
        border-radius: 10px;
        background-color: #FFFFFF;
        text-align: center;
        font-weight: bold;
        color: #FFFFFF;
        height: 8px;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #FF6B6B, stop:0.2 #FFE66D,
                                   stop:0.4 #4ECDC4, stop:0.6 #45B7D1,
                                   stop:0.8 #96CEB4, stop:1 #FFEAA7);
        border-radius: 8px;
        margin: 1px;
    }
"""

UITRANSLATION_CSS = """
    QMainWindow {
        /* 从左到右的明亮彩虹渐变 */
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #ffffff, /* 白色 */
                                    stop:0.2 #d5f4e6, /* 淡绿色 */
                                    stop:0.4 #bee3f8, /* 淡蓝色 */
                                    stop:0.6 #f0e6f6, /* 淡紫色 */
                                    stop:0.8 #ffe9c7, /* 淡橙色 */
                                    stop:1 #ffffff); /* 白色 */
        border: 1px solid #dddddd; /* 可选：添加轻微边框 */
    }
"""


class UiTranslation(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(300, 300, 500, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self._drag_position = None
        self.current_original_text = ""
        self.current_translation = ""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QHBoxLayout()

        title_label = QLabel("😄ClipTranslate")
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setFont(QFont("Consolas", 12, QFont.Bold))
        header_layout.addWidget(title_label, 1)

        self.copy_button = QPushButton("复制译文")
        self.copy_button.setFixedHeight(30)
        self.copy_button.clicked.connect(self.copy_translation)
        self.copy_button.setStyleSheet(COPY_BUTTON_CSS)
        header_layout.addWidget(self.copy_button)

        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.setFont(QFont("Arial", 14))
        close_button.clicked.connect(self.hide)
        close_button.setStyleSheet(CLOSE_BUTTON_CSS)
        header_layout.addWidget(close_button, 0)

        layout.addLayout(header_layout)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("consolas", 12))
        self.text_area.setStyleSheet(TEXT_AREA_CSS)
        layout.addWidget(self.text_area)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        self.progress_bar.setStyleSheet(PROGRESS_BAR_CSS)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.token_label = QLabel()
        self.token_label.setAlignment(Qt.AlignLeft)
        self.token_label.setFont(QFont("Consolas", 9, QFont.Bold))
        layout.addWidget(self.token_label)

        self.setStyleSheet(UITRANSLATION_CSS)
        logger.info("翻译窗口初始化完成")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.position().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_position is not None:
            self.move(self.pos() + event.position().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = None
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    @Slot(str)
    def set_translation(self, text, translated, usage=None):
        # delimiter = "——-——" * 9
        delimiter = ""
        self.current_translation = translated
        self.text_area.setText(f"{text}\n{delimiter}\n{translated}")

        # 滚动到底部
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )

        # 显示token使用情况
        if usage:
            prompt = usage.get("prompt_tokens", 0)
            completion = usage.get("completion_tokens", 0)
            total = usage.get("total_tokens", 0)
            model_name = usage.get("model", "")
            if total == 0:
                self.token_label.setText(f"😁您使用的是免费模型：{model_name}")
            else:
                if "turbo" in model_name.lower():
                    prompt_cost = 0.001 * prompt / 1000  # 0.001元每千Token
                    completion_cost = 0.003 * completion / 1000  # 0.003元每千Token
                else:
                    prompt_cost = 0.015 * prompt / 1000  # 0.015元每千Token
                    completion_cost = 0.045 * completion / 1000  # 0.045元每千Token

                total_cost = prompt_cost + completion_cost
                cost_str = f"{prompt_cost:.4f}+{completion_cost:.4f}={total_cost:.4f}元"
                self.token_label.setText(
                    f"😭Token: {prompt}+{completion}={total} 💰花费: {cost_str} 🤖模型：{model_name}"
                )

        self.progress_bar.hide()
        self.show()
        self.activateWindow()

    @Slot()
    def show_loading(self, text):
        self.current_original_text = text
        self.text_area.setText(f"{text}")
        self.progress_bar.show()
        self.show()
        self.activateWindow()

    @Slot(str)
    def show_error(self, error_msg):
        self.text_area.setText(f"错误: {error_msg}")
        self.progress_bar.hide()
        self.show()
        self.activateWindow()

    def copy_translation(self):
        if self.current_translation:
            pyperclip.copy(self.current_translation)
            original_text = self.copy_button.text()
            self.copy_button.setText("已复制!")
            self.copy_button.setStyleSheet(COPYED_BUTTON_CSS)

            # 使用QTimer延时恢复按钮文字
            QTimer.singleShot(1500, lambda: self.reset_copy_button(original_text))

    def reset_copy_button(self, text):
        self.copy_button.setText(text)
        self.copy_button.setStyleSheet(COPY_BUTTON_CSS)

    @Slot(str)
    def update_translation_progress(self, partial_translation):
        self.current_translation = partial_translation
        # delimiter = "——-——" * 9
        delimiter = ""
        self.text_area.setText(
            f"{self.current_original_text}\n{delimiter}\n{partial_translation}"
        )

        # 滚动到底部
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
