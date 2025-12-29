"""应用常量

集中管理应用中的配置常量和魔法数字。
"""

# 热键监听相关
HOTKEY_CHECK_INTERVAL_MS = 100  # 热键轮询间隔（毫秒）
HOTKEY_COOLDOWN_SECONDS = 0.5  # 热键防抖时间（秒）

# 文本长度阈值（默认值）
CHINESE_TEXT_THRESHOLD = 300  # 中文文本长度阈值
ENGLISH_TEXT_THRESHOLD = 1000  # 英文文本长度阈值

# 系统托盘消息显示时间（毫秒）
TRAY_MESSAGE_INFO_DURATION = 5000  # 信息消息显示时长
TRAY_MESSAGE_WARNING_DURATION = 3000  # 警告消息显示时长

# 弹窗延迟
SETTINGS_POPUP_DELAY_MS = 1000  # 设置弹窗延迟（毫秒）

# 按钮恢复时间
COPY_BUTTON_RESTORE_MS = 1500  # 复制按钮恢复时间（毫秒）

# 中文检测相关
CHINESE_DETECTION_SAMPLE_SIZE = 30  # 中文检测样本大小
CHINESE_DETECTION_RATIO_THRESHOLD = 0.5  # 中文字符比例阈值
CHINESE_CHAR_PATTERN = r"[\u4e00-\u9fff]"  # 中文字符正则表达式

# 支持的目标语言
SUPPORTED_TARGET_LANGUAGES = ["Chinese", "English"]

# 默认目标语言
DEFAULT_TARGET_LANGUAGE = "Chinese"

# 日志配置
LOG_DIR = ".cliptranslate_logs"
LOG_FILE_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_FILE_BACKUP_COUNT = 3
