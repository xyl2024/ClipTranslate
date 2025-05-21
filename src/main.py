import sys
import keyboard
import pyperclip
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QAction
from PySide6.QtCore import Slot, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from ui_translation import UiTranslation
from translator import QwenTranslator
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
            self.translator = QwenTranslator(self.config_manager.get_config())
        except ValueError as e:
            logger.warning(f"初始化翻译器警告: {e}")
            self.translator = QwenTranslator({})
            QTimer.singleShot(
                1000, lambda: self.show_settings_with_message("请设置API密钥")
            )

        self.translator_thread = TranslatorThread(self.translator)
        self.translator_thread.translation_done.connect(
            self.ui_translation.set_translation
        )
        self.translator_thread.translation_error.connect(
            self.ui_translation.show_error
        )
        self.translator_thread.translation_progress.connect(
            self.ui_translation.update_translation_progress
        )

        self.ui_settings = None

        self.setup_hotkeys()
        self.setup_tray_icon()

        logger.info("应用程序的初始化已完成")

    def translate_clipboard(self, target_lang="Chinese"):
        if self.translator_thread.is_running:
            return

        text = pyperclip.paste()
        if not text.strip():
            self.ui_translation.set_translation("剪贴板为空", "The clipboard is empty")
            return

        self.start_translation(text, target_lang)
        self.ui_translation.show_loading(text)

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
        self.tray_icon.setToolTip("中英互译工具")
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
