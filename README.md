# ClipTranslate - 剪贴板翻译工具

ClipTranslate 是一款 Windows 桌面便捷翻译工具，允许用户通过全局快捷键将剪贴板中的文本内容快速翻译成中文或英文，并在独立窗口中显示原文和译文。

> 本项目全程通过 claude 3.7 sonnet 开发与测试。

## 主要功能

- 通过全局快捷键触发翻译
- 自动获取剪贴板文本内容
- 调用阿里云千问翻译模型API进行翻译
- 在独立窗口中同时显示原文和译文

Qwen-MT模型价格：https://help.aliyun.com/zh/model-studio/machine-translation

获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key?spm=a2c4g.11186623.0.0.210766518NP6kD

## 使用步骤

> 本项目通过 uv 进行管理，你可以查看[官方使用手册](https://docs.astral.sh/uv/)学习 uv 的使用。

1. 克隆或下载此仓库
2. 安装依赖包
3. 运行应用程序
```
$ git clone https://github.com/xyl2024/ClipTranslate.git
$ cd ClipTranslate
$ uv sync
$ uv run src/main.py
```

## 首次使用配置

1. 运行应用程序后，在系统托盘区找到 ClipTranslate 图标
2. 右键点击图标，选择"设置"
3. 输入您的阿里云千问翻译API密钥
4. 如需要，可以自定义翻译快捷键
5. 点击"保存"完成配置

## 使用方法

1. 复制需要翻译的文本（Ctrl+C）
2. 按下配置的快捷键：
   - 默认F2键：将文本翻译为中文
   - 默认F10键：将文本翻译为英文
3. 翻译窗口将自动显示，流式输出，包含原文和译文
4. 可点击"复制译文"按钮将译文复制到剪贴板
5. 按ESC键或点击关闭按钮可隐藏翻译窗口
6. 双击系统托盘图标可显示/隐藏翻译窗口

示例：
![](assets/usage.gif)

## 配置文件

配置文件`config.json`位于 `HOME/.cliptranslate` 目录下，格式如下：

```json
{
  "API_KEY": "YOUR_API_KEY",
  "BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
  "MODEL": "qwen-mt-turbo", // 或者 "qwen-mt-plus"，更贵的模型
  "shortcut_translate_to_chinese": "f2",
  "shortcut_translate_to_english": "f10"
}
```

## 注意事项

- 翻译服务依赖于阿里云千问API，会产生API调用费用
- 全局快捷键功能仅在 Windows 平台上可用

## 许可证

[MIT](LICENSE)