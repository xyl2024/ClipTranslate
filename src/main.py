import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtCore import Slot, QTimer
from PySide6.QtGui import QAction, QIcon
import keyboard
import pyperclip
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from ui_translation import UiTranslation
from translator import AliyuncsTranslator
from translator_thread import TranslatorThread
from config_manager import ConfigManager
from ui_settings import UiSettings
from utils import get_app_icon


def setup_logger():
    log_dir = Path.home() / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"translator_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


class App:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

        # 设置应用程序图标
        app_icon = get_app_icon("app_icon.png")
        self.app.setWindowIcon(app_icon)

        # 初始化配置管理器
        self.config_manager = ConfigManager()

        # 初始化UI
        self.ui_translation = UiTranslation()

        # 初始化翻译器，传入配置
        try:
            self.translator = AliyuncsTranslator(self.config_manager.get_config())
        except ValueError as e:
            logger.warning(f"初始化翻译器警告: {e}")
            # 创建一个临时翻译器实例
            self.translator = AliyuncsTranslator({})

            # 显示设置窗口提示用户设置API密钥
            QTimer.singleShot(
                1000, lambda: self.show_settings_with_message("请设置API密钥")
            )

        # 初始化翻译线程
        self.translator_thread = TranslatorThread(self.translator)
        self.translator_thread.translation_done.connect(
            self.ui_translation.set_translation
        )
        self.translator_thread.translation_error.connect(self.ui_translation.show_error)
        self.translator_thread.translation_progress.connect(
            self.ui_translation.update_translation_progress
        )

        # 初始化设置窗口
        self.settings_window = None

        # 设置热键
        self.setup_hotkeys()
        self.setup_tray_icon()

        logger.info("Initialization of the App is completed.")

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

        # 使用工具函数加载图标
        icon = get_app_icon("app_icon.png")
        self.tray_icon.setIcon(icon)
        # 检查图标是否正确加载，如果不正确，记录警告
        if icon.isNull():
            logger.warning("无法加载应用图标 app_icon.png，使用系统默认图标")
        # 设置窗口图标
        self.ui_translation.setWindowIcon(icon)

        tray_menu = QMenu()

        # 添加翻译菜单项
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

        # 添加显示翻译窗口菜单项
        show_action = QAction("显示翻译窗口", self.app)
        show_action.triggered.connect(self.ui_translation.show)
        tray_menu.addAction(show_action)

        # 添加设置菜单项
        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # 添加退出菜单项
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
        logger.info("Quit the App")
        sys.exit(0)

    def setup_hotkeys(self):
        # 获取配置中的快捷键
        config = self.config_manager.get_config()
        self.hotkey_to_chinese = config.get("hotkey_to_chinese", "f2")
        self.hotkey_to_english = config.get("hotkey_to_english", "f10")

        # 创建定时器检查热键
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
                logger.debug(
                    f"The hotkey {self.hotkey_to_chinese} is pressed, translating to Chinese"
                )
                self.last_hotkey_time = current_time
                self.translate_clipboard("Chinese")

            # 检查英文翻译热键
            elif keyboard.is_pressed(self.hotkey_to_english) and (
                current_time - self.last_hotkey_time >= self.hotkey_cooldown
            ):
                logger.debug(
                    f"The hotkey {self.hotkey_to_english} is pressed, translating to English"
                )
                self.last_hotkey_time = current_time
                self.translate_clipboard("English")

        except Exception as e:
            logger.exception(f"Check hotkey error: {str(e)}")

    @Slot(str)
    def start_translation(self, text, target_lang="Chinese"):
        self.translator_thread.set_text(text)
        self.translator_thread.set_target_lang(target_lang)
        if not self.translator_thread.isRunning():
            self.translator_thread.start()

    def show_settings(self):
        if not self.settings_window:
            # 传入self.app作为父对象
            self.settings_window = UiSettings(self.config_manager.get_config(), None)
            self.settings_window.settings_saved.connect(self.apply_settings)

        # 防止窗口已经被销毁的情况
        if not self.settings_window.isVisible():
            self.settings_window.load_config()  # 重新加载配置

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()  # 确保窗口被激活

        self.settings_window.show()
        self.settings_window.raise_()

    def show_settings_with_message(self, message):
        self.show_settings()
        if self.settings_window:
            self.tray_icon.showMessage(
                "设置提示", message, QSystemTrayIcon.Information, 5000
            )

    @Slot(dict)
    def apply_settings(self, new_config):
        try:
            # 保存旧配置用于比较
            old_config = self.config_manager.get_config().copy()

            # 更新配置
            self.config_manager.update_config(new_config)

            # 更新翻译器配置
            self.translator.update_config(new_config)

            # 更新热键
            if old_config.get("hotkey_to_chinese") != new_config.get(
                "hotkey_to_chinese"
            ) or old_config.get("hotkey_to_english") != new_config.get(
                "hotkey_to_english"
            ):
                # 热键已更改，需要重新设置
                self.hotkey_to_chinese = new_config.get(
                    "hotkey_to_chinese", self.hotkey_to_chinese
                )
                self.hotkey_to_english = new_config.get(
                    "hotkey_to_english", self.hotkey_to_english
                )

                # 显示一条通知，告知用户热键已更新
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "设置已更新",
                        f"新热键已生效: 中文={self.hotkey_to_chinese}, 英文={self.hotkey_to_english}",
                        QSystemTrayIcon.Information,
                        3000,
                    )

            logger.info("Settings applied successfully")
        except Exception as e:
            logger.error(f"应用设置时出错: {e}")
            # 显示错误通知
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "设置错误",
                    f"应用设置时出错: {str(e)}",
                    QSystemTrayIcon.Critical,
                    5000,
                )

    def run(self):
        try:
            logger.info("The App starts.")
            sys.exit(self.app.exec())
        finally:
            # 停止定时器
            self.hotkey_timer.stop()

            # 清理翻译线程
            if self.translator_thread.isRunning():
                self.translator_thread.quit()
                self.translator_thread.wait()

            # 清理设置窗口
            if self.settings_window:
                self.settings_window.close()
                self.settings_window = None


if __name__ == "__main__":
    app = App()
    app.run()
