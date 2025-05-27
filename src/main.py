import re
import sys
import keyboard
import pyperclip
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QAction
from PySide6.QtCore import Slot, QTimer, Qt
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox

from ui_translation import UiTranslation
from translator import QwenTranslator, ChatTranslator
from translator_thread import TranslatorThread
from config_manager import ConfigManager
from ui_settings import UiSettings
from utils import get_app_icon


def setup_logger():
    log_dir = Path.home() / ".cliptranslate_logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"translator_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(threadName)s][%(filename)s:%(lineno)d]: %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


class App:
    def __init__(self):
        logger.info("应用程序正在初始化...")
        self.app = QApplication.instance() or QApplication(sys.argv)

        app_icon = get_app_icon("app_icon.png")
        self.app.setWindowIcon(app_icon)

        self.config_manager = ConfigManager()
        self.ui_translation = UiTranslation()

        try:
            config = self.config_manager.get_config()
            translator_type = config.get("translator_type", "qwen")

            if translator_type == "chat":
                self.translator = ChatTranslator(config)
                logger.info("使用通用聊天模型翻译器")
            else:
                self.translator = QwenTranslator(config)
                logger.info("使用Qwen专用翻译器")
        except ValueError as e:
            logger.warning(f"初始化翻译器警告: {e}")
            logger.info("默认使用Qwen专用翻译器")
            self.translator = QwenTranslator({})
            QTimer.singleShot(
                1000, lambda: self.show_settings_with_message("请设置API密钥")
            )

        self.translator_thread = TranslatorThread(self.translator)
        self.translator_thread.translation_done.connect(
            self.ui_translation.set_translation
        )
        self.translator_thread.translation_error.connect(self.ui_translation.show_error)
        self.translator_thread.translation_progress.connect(
            self.ui_translation.update_translation_progress
        )

        self.ui_settings = None

        self.setup_hotkeys()
        self.setup_tray_icon()

        logger.info("应用程序的初始化已完成")

    def translate_clipboard(self, target_lang="Chinese"):
        try:
            logger.info(f"开始处理剪贴板翻译请求，目标语言：{target_lang}")

            if self.translator_thread.is_running:
                logger.info("翻译线程正在处理其他请求，忽略此次请求")
                return

            text = pyperclip.paste()
            if not text.strip():
                logger.info("剪贴板无文本内容")
                self.ui_translation.set_translation(
                    "剪贴板无文本内容", "The clipboard has no text content"
                )
                return

            exceeds_threshold, message, is_chinese_text = (
                self.detect_text_type_and_check_length(text)
            )
            logger.info(
                f"文本长度检查结果：超过阈值={exceeds_threshold}，是中文={is_chinese_text}"
            )

            if exceeds_threshold:
                logger.info("文本超过阈值，显示确认对话框")

                dialog_result = self.show_simple_confirmation(
                    "ClipTranslate 提示",
                    message,
                    "⚠️翻译长文本可能会：\n1.消耗很多的Tokens;\n2.达到模型上下文限制",
                )

                logger.info(f"用户对话框选择结果：{dialog_result}")

                if not dialog_result:
                    logger.info("用户选择不继续翻译，取消翻译流程")
                    return

            logger.info("开始执行翻译请求")
            self.start_translation(text, target_lang)
            self.ui_translation.show_loading(text)

        except Exception as e:
            logger.exception(f"翻译剪贴板过程中发生异常: {str(e)}")

    def show_simple_confirmation(self, title, message, detail):
        try:
            logger.info(f"显示确认对话框: {title}")

            msg_box = QMessageBox(self.ui_translation)  # 使用父窗口，关键
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setInformativeText(detail)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

            result = msg_box.exec()
            logger.info(f"result={result}, Yes={QMessageBox.Yes}, No={QMessageBox.No}")
            return result == QMessageBox.Yes

        except Exception as e:
            logger.exception(f"显示确认对话框时发生异常: {str(e)}")
            return False

    def detect_text_type_and_check_length(self, text):
        chinese_threshold = self.config_manager.get("chinese_threshold", 300)
        english_threshold = self.config_manager.get("english_threshold", 1000)

        if not text:
            return False, "", False
        # 这里判断文本类型采用简单的方式：
        # 根据前30个字符的中文比例判断
        sample_text = text[: min(30, len(text))]
        chinese_char_count = len(re.findall(r"[\u4e00-\u9fff]", sample_text))
        is_chinese_text = (
            chinese_char_count / len(sample_text) > 0.5 if sample_text else False
        )
        threshold = chinese_threshold if is_chinese_text else english_threshold
        text_type = "中文" if is_chinese_text else "英文"

        if len(text) > threshold:
            message = f"剪贴板文本(主要为{text_type})长度: {len(text)} 字符\n阈值: {threshold} 字符\n是否继续翻译？"
            return True, message, is_chinese_text

        return False, "", is_chinese_text

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self.app)
        icon = get_app_icon("app_icon.png")
        self.tray_icon.setIcon(icon)
        if icon.isNull():
            logger.warning("无法加载应用图标 app_icon.png，使用系统默认图标")
        self.ui_translation.setWindowIcon(icon)

        tray_menu = QMenu()
        translate_menu = QMenu("翻译剪贴板")

        translate_to_chinese = QAction("翻译为中文", self.app)
        translate_to_chinese.triggered.connect(
            lambda: self.translate_clipboard("Chinese")
        )
        translate_menu.addAction(translate_to_chinese)

        translate_to_english = QAction("翻译为英文", self.app)
        translate_to_english.triggered.connect(
            lambda: self.translate_clipboard("English")
        )
        translate_menu.addAction(translate_to_english)
        tray_menu.addMenu(translate_menu)

        show_action = QAction("显示翻译窗口", self.app)
        show_action.triggered.connect(self.ui_translation.show)
        tray_menu.addAction(show_action)

        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出程序", self.app)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("ClipTranslate")
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.ui_translation.isVisible():
                self.ui_translation.hide()
            else:
                self.ui_translation.show()

    def quit_application(self):
        logger.info("退出应用程序\n\n")
        sys.exit(0)

    def setup_hotkeys(self):
        config = self.config_manager.get_config()
        self.hotkey_to_chinese = config.get("hotkey_to_chinese", "f2")
        self.hotkey_to_english = config.get("hotkey_to_english", "f10")

        self.hotkey_timer = QTimer()
        self.hotkey_timer.timeout.connect(self.check_hotkeys)
        self.hotkey_timer.start(100)

        self.last_hotkey_time = 0
        self.hotkey_cooldown = 0.5

    def check_hotkeys(self):
        try:
            current_time = datetime.now().timestamp()

            # 检查中文翻译热键
            if keyboard.is_pressed(self.hotkey_to_chinese) and (
                current_time - self.last_hotkey_time >= self.hotkey_cooldown
            ):
                logger.debug(f"按下热键{self.hotkey_to_chinese}，翻译成中文 ")
                self.last_hotkey_time = current_time
                self.translate_clipboard("Chinese")

            # 检查英文翻译热键
            elif keyboard.is_pressed(self.hotkey_to_english) and (
                current_time - self.last_hotkey_time >= self.hotkey_cooldown
            ):
                logger.debug(f"按下热键{self.hotkey_to_english}，翻译成英文 ")
                self.last_hotkey_time = current_time
                self.translate_clipboard("English")

        except Exception as e:
            logger.exception(f"检查热键错误: {str(e)}")

    @Slot(str)
    def start_translation(self, text, target_lang="Chinese"):
        self.translator_thread.set_text(text)
        self.translator_thread.set_target_lang(target_lang)
        if not self.translator_thread.isRunning():
            self.translator_thread.start()

    def show_settings(self):
        if not self.ui_settings:
            self.ui_settings = UiSettings(self.config_manager.get_config(), None)
            self.ui_settings.settings_saved.connect(self.apply_settings)

        if not self.ui_settings.isVisible():
            self.ui_settings.load_config()

        self.ui_settings.show()
        self.ui_settings.raise_()
        self.ui_settings.activateWindow()

    def show_settings_with_message(self, message):
        self.show_settings()
        if self.ui_settings:
            self.tray_icon.showMessage(
                "设置提示", message, QSystemTrayIcon.Information, 5000
            )

    @Slot(dict)
    def apply_settings(self, new_config):
        try:
            old_config = self.config_manager.get_config().copy()
            self.config_manager.update_config(new_config)

            # 检查翻译器类型是否改变
            old_translator_type = old_config.get("translator_type", "qwen")
            new_translator_type = new_config.get("translator_type", "qwen")

            if old_translator_type != new_translator_type:
                if new_translator_type == "chat":
                    self.translator = ChatTranslator(new_config)
                    logger.info("切换到通用聊天模型翻译器")
                else:
                    self.translator = QwenTranslator(new_config)
                    logger.info("切换到Qwen专用翻译器")

                self.translator_thread.translator = self.translator
            else:
                self.translator.update_config(new_config)

            if old_config.get("hotkey_to_chinese") != new_config.get(
                "hotkey_to_chinese"
            ) or old_config.get("hotkey_to_english") != new_config.get(
                "hotkey_to_english"
            ):
                self.hotkey_to_chinese = new_config.get(
                    "hotkey_to_chinese", self.hotkey_to_chinese
                )
                self.hotkey_to_english = new_config.get(
                    "hotkey_to_english", self.hotkey_to_english
                )

                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "设置已更新",
                        f"新热键已生效: 中文={self.hotkey_to_chinese}, 英文={self.hotkey_to_english}",
                        QSystemTrayIcon.Information,
                        3000,
                    )

            logger.info("设置已成功应用")
        except Exception as e:
            logger.error(f"应用设置时出错: {e}")
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "设置错误",
                    f"应用设置时出错: {str(e)}",
                    QSystemTrayIcon.Critical,
                    5000,
                )

    def run(self):
        try:
            logger.info("启动应用程序")
            sys.exit(self.app.exec())
        finally:
            self.hotkey_timer.stop()

            if self.translator_thread.isRunning():
                self.translator_thread.quit()
                self.translator_thread.wait()

            if self.ui_settings:
                self.ui_settings.close()
                self.ui_settings = None


if __name__ == "__main__":
    app = App()
    app.run()
