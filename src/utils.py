import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle, QApplication
import logging

logger = logging.getLogger(__name__)


def get_app_icon(icon_name="app_icon.png"):
    # 尝试多个可能的图标位置
    possible_locations = [
        # 相对路径（相对于当前脚本）
        os.path.join("icons", icon_name),
        # 相对于应用根目录（如果是打包的应用）
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "icons",
            icon_name,
        ),
        # 绝对路径，假设图标在固定位置
        os.path.abspath(os.path.join("icons", icon_name)),
    ]

    # 尝试从可能的位置加载图标
    for icon_path in possible_locations:
        if os.path.exists(icon_path):
            try:
                icon = QIcon(icon_path)
                if not icon.isNull():
                    logger.info(f"成功加载图标: {icon_path}")
                    return icon
            except Exception as e:
                logger.warning(f"无法加载图标 {icon_path}: {e}")

    # 无法加载自定义图标，使用系统图标
    logger.warning(f"无法找到图标 {icon_name}，使用系统图标")
    return QIcon.fromTheme(
        "accessories-dictionary",
        QApplication.style().standardIcon(QStyle.SP_ComputerIcon),
    )


def get_icon_path(icon_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 尝试多个可能的图标位置
    possible_locations = [
        # 相对路径（相对于当前脚本）
        os.path.join(script_dir, "icons", icon_name),
        # 相对于应用根目录（如果是打包的应用）
        os.path.join(os.path.dirname(script_dir), "icons", icon_name),
        # 绝对路径，假设图标在固定位置
        os.path.abspath(os.path.join("icons", icon_name)),
    ]

    # 尝试找到图标文件
    for icon_path in possible_locations:
        if os.path.exists(icon_path):
            return icon_path

    return None
