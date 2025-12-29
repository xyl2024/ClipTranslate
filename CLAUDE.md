# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 重要规则

- 使用 `中文` 与用户进行交互。
- 生成新的代码后，在 src/ 目录使用 `uv run ruff format .` 的方式格式化所有python代码。
- 增量代码需要增加依赖时，使用 `uv add` 的方式执行添加，不要手动编写 pyproject.toml。

## 项目概述
ClipTranslate 是一款基于 PySide6（Qt6）和大型语言模型 API 的 Windows 桌面剪贴板翻译工具。用户可通过全局热键翻译剪贴板内容，流式翻译结果会显示在一个无边框且始终置顶的窗口中。

**技术栈**: Python 3.12, PySide6, `keyboard` 库（全局热键）、`pyperclip`（剪贴板）、`openai` SDK（OpenAI 兼容 API）、`uv`（包管理器）

## 开发命令
```bash
# 安装依赖
uv sync
# 格式化代码
uv run ruff format src/
# 运行应用
uv run src/main.py
# 构建 Windows 可执行文件
python build.py # 推荐（清理、运行 PyInstaller、复制图标）
# 或者：
pyinstaller clipTranslate.spec -y
```

## 架构
该应用采用分层的 MVC 类似架构：
- **入口点**: `src/main.py` - `App` 类初始化 QApplication，管理系统托盘、热键（通过 QTimer 轮询），并协调翻译请求
- **常量层**: `src/constants.py` - 集中管理应用常量（热键间隔、文本长度阈值、中文检测参数等）
- **UI 层**: `src/ui_translation.py`（主窗口）、`src/ui_settings.py`（设置对话框） - 无边框窗口，支持自定义 CSS，按 ESC 键隐藏窗口，双击托盘切换窗口可见状态
- **翻译层**: `src/translator.py` - 抽象 `Translator` 基类及具体实现：
  - `ChatTranslator` - 兼容 OpenAI 的 API（使用 `openai` SDK）
  - `EmojiTranslator` - 使用 OpenAI 兼容 API 生成 emoji 表情
- **线程封装**: `src/translator_thread.py` - `TranslatorThread` 将翻译操作封装在 `QThread` 中，避免 UI 阻塞。发射信号：`translation_done`、`translation_error`、`translation_progress`（流式）
- **配置层**: `src/config_manager.py` - 加载/保存 JSON 配置到 `HOME/.cliptranslate/config.json`，处理旧格式迁移

### 翻译请求流程
1. 检测到全局热键（F2/F4/F6）或点击托盘菜单
2. `App.translate_clipboard()` 或 `App.generate_emoji_from_clipboard()` 捕获剪贴板文本
3. 校验文本（长度检查、中文检测）
4. 若文本过长，弹出确认对话框（仅翻译模式）
5. `App.start_translation()` 或 `App.start_emoji_translation()` 启动 `TranslatorThread`
6. 线程调用 `Translator.translate_stream()` 并传回调函数
7. 流式更新通过 `translation_progress` 信号发送
8. 最终结果通过 `translation_done` 信号返回（原文、翻译、使用统计）

### Emoji 生成流程
1. 检测到 F6 热键或点击托盘"生成Emoji"菜单
2. `App.generate_emoji_from_clipboard()` 捕获剪贴板文本
3. 启动 `EmojiTranslatorThread` 调用 `EmojiTranslator.translate_stream()`

### 关键模式
**策略模式**: 通过抽象 `Translator` 基类实现可插拔的翻译器。新增后端只需实现 `translate()` 和 `translate_stream()` 方法。
**Qt 信号/槽**: 所有异步通信均使用 Qt 的信号/槽机制，确保线程安全更新。槽方法需使用 `@Slot()` 装饰器。
**流式翻译**: 所有翻译器必须支持流式。使用 `openai` SDK 的流式接口，回调接收累积文本块。
**全局热键**: 在 `check_hotkeys()` 中使用 `QTimer` 轮询，间隔在 `constants.HOTKEY_CHECK_INTERVAL_MS` 定义（100ms）。`keyboard.is_pressed()` 检测按键状态。防抖时间在 `constants.HOTKEY_COOLDOWN_SECONDS` 定义（0.5秒）。
**配置**: `ConfigManager.DEFAULT_CONFIG` 定义默认值。配置位置：`HOME/.cliptranslate/config.json`。迁移逻辑在 `_migrate_old_config()` 中。

## 重要限制
- **仅限 Windows**: 全局热键功能（`keyboard` 库）仅适用于 Windows
- **单实例**: 没有防止多实例同时运行的保护措施（已知问题）
- **热键编辑限制**: 设置对话框无法识别 F1-F12 功能键（已知问题）

## 代码规范
- 文件命名：Python 文件使用 snake_case
- 类名：PascalCase（如 `UiTranslation`、`ConfigManager`）
- 方法命名：snake_case
- CSS 样式：模块级常量以 `_CSS` 结尾（彩虹渐变背景、自定义颜色）
- 注释：中英文混用
- UI 组件：无边框，`Qt.WindowStaysOnTopHint`、`Qt.Tool`（无任务栏条目）

## 日志记录
集中式日志记录器在 `main.setup_logger()` 中。日志写入 `HOME/.cliptranslate_logs/translator_YYYYMMDD.log`。轮转文件处理器（5MB，保留 3 个备份）+ 控制台处理器。格式：`[时间戳][级别][线程][文件:行]: 消息`

## 配置结构
```json
{
  "hotkey_to_chinese": "f2",
  "hotkey_to_english": "f4",
  "hotkey_to_emoji": "f6",
  "chat_api_key": "sk-...",
  "chat_api_url": "https://api.openai.com/v1/chat/completions",
  "chat_api_model": "gpt-3.5-turbo",
  "window_opacity": 0.95
}
```

## 关键文件
- `src/main.py` - 应用入口，`App` 类
- `src/constants.py` - 应用常量（热键、阈值、日志配置等）
- `src/translator.py` - `Translator`、`ChatTranslator`、`EmojiTranslator`
- `src/translator_thread.py` - `TranslatorThread`（QThread 封装）
- `src/config_manager.py` - `ConfigManager`
- `src/ui_translation.py` - `UiTranslation`（主窗口）
- `src/ui_settings.py` - `UiSettings`（设置对话框）
- `src/utils.py` - 工具函数（图标加载、字符串清理等）
- `build.py` - 构建脚本
- `clipTranslate.spec` - PyInstaller 规范