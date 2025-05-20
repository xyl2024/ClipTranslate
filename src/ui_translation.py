from PySide6.QtWidgets import (QMainWindow, QTextEdit, 
                              QVBoxLayout, QWidget, QLabel, QPushButton,
                              QProgressBar, QHBoxLayout,
                              )
from PySide6.QtCore import Qt, Slot, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
import pyperclip
import logging

logger = logging.getLogger(__name__)

TEXT_AREA_CSS = """
    QTextEdit {
        background-color: #f8f8f8;
        border: 1px solid #e0e0e0;
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

class UiTranslation(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setGeometry(300, 300, 500, 300)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool    
        )
        
        self._drag_position = None
        self.current_original_text = ""  # 存储当前原文
        self.current_translation = ""    # 存储当前译文
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("😄ClipTranslate")
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setFont(QFont("Consolas", 12, QFont.Bold))
        header_layout.addWidget(title_label, 1)
        
        # 添加复制按钮
        self.copy_button = QPushButton("复制译文")
        self.copy_button.setFixedHeight(30)
        self.copy_button.clicked.connect(self.copy_translation)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(self.copy_button)
        
        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.setFont(QFont("Arial", 14))
        close_button.clicked.connect(self.hide)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
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
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #D2DCDF;
            }
        """)

        # 添加token使用状态标签
        self.token_label = QLabel()
        self.token_label.setAlignment(Qt.AlignLeft)
        self.token_label.setFont(QFont("Consolas", 9, QFont.Bold))
        layout.addWidget(self.token_label)
        
        logger.info("TranslationWindow init done.")
        
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
        delimiter = "——-——" * 9
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
            
            if "turbo" in model_name.lower():
                prompt_cost = 0.001 * prompt / 1000  # 0.001元每千Token
                completion_cost = 0.003 * completion / 1000  # 0.003元每千Token
            else:
                prompt_cost = 0.015 * prompt / 1000  # 0.015元每千Token
                completion_cost = 0.045 * completion / 1000  # 0.045元每千Token

            total_cost = prompt_cost + completion_cost
            cost_str = f"{prompt_cost:.4f}+{completion_cost:.4f}={total_cost:.4f}元"
            self.token_label.setText(f"😭Token: {prompt}+{completion}={total} | 💰Cost: {cost_str}")

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
            # 临时改变按钮文字，表示已复制
            original_text = self.copy_button.text()
            self.copy_button.setText("已复制!")
            self.copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
            """)
            
            # 使用QTimer延时恢复按钮文字
            QTimer.singleShot(1500, lambda: self.reset_copy_button(original_text))
            
    def reset_copy_button(self, text):
        self.copy_button.setText(text)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    @Slot(str)
    def update_translation_progress(self, partial_translation):
        self.current_translation = partial_translation
        delimiter = "——-——" * 9
        self.text_area.setText(f"{self.current_original_text}\n{delimiter}\n{partial_translation}")
        
        # 滚动到底部
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )