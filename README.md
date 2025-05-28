<p align="center">
  <img width="350px" height="350px" src="assets/app_icon.png" />
</p>

<p align="center">ClipTranslate 一款基于大模型的剪贴板翻译工具</p>

<p align="center"><a href="README.en.md">English</a> | 中文</p>

## 🚀 **项目概述**

ClipTranslate 是一款 Windows 桌面便捷翻译工具，允许用户通过全局快捷键将剪贴板中的文本内容快速翻译成中文或英文，并在独立窗口中显示原文和译文。

ℹ️ **开发说明**

> 本项目通过 Claude 开发与测试。

## 🔧 **主要功能**

1️⃣ 通过全局快捷键触发翻译

2️⃣ 自动获取剪贴板文本内容

3️⃣ 调用阿里云千问翻译模型API进行翻译

4️⃣ 调用通用聊天大模型API进行翻译

5️⃣ 在独立窗口中同时显示原文和译文

📌 **相关链接**

💰 千问模型价格：
https://help.aliyun.com/zh/model-studio/machine-translation

🔑 获取API Key：
https://help.aliyun.com/zh/model-studio/get-api-key?spm=a2c4g.11186623.0.0.210766518NP6kD


## 📥 **使用步骤**

> 本项目通过 uv 进行管理，你可以查看[官方使用手册](https://docs.astral.sh/uv/)学习 uv 的安装与使用。

1️⃣ 克隆或下载此仓库

2️⃣ 安装依赖包

3️⃣ 运行应用程序

```bash
$ git clone https://github.com/xyl2024/ClipTranslate.git
$ cd ClipTranslate
$ uv sync
$ uv run src/main.py
```

## ⚙️ **首次使用配置**

1️⃣ 运行应用程序后，在系统托盘区找到 ClipTranslate 图标

2️⃣ 右键点击图标，选择"设置"

3️⃣ 输入您的阿里云API密钥/聊天大模型API密钥

4️⃣ 可自定义翻译快捷键

5️⃣ 点击"保存"完成配置

## 💡 **使用方法**

1️⃣ 复制需要翻译的文本（Ctrl+C）

2️⃣ 按下配置的快捷键：
   - F2键 翻译为中文
   - F4键 翻译为英文

3️⃣ 翻译窗口将自动显示，流式输出原文和译文

4️⃣ 点击"复制译文"按钮复制译文

5️⃣ 按ESC键或点击关闭按钮可隐藏窗口

6️⃣ 双击系统托盘图标可显示/隐藏翻译窗口

🎥 示例：

![](assets/usage.gif)


## 📂 **配置文件**

配置文件位于 `HOME/.cliptranslate/config.json`：

```json
{
    "hotkey_to_chinese": "f2",
    "hotkey_to_english": "f4",
    "chinese_threshold": 300,
    "english_threshold": 1000,
    "translator_type": "chat",
    "qwen_api_key": "sk-************************************************",
    "qwen_api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "qwen_api_model": "qwen-mt-plus",
    "chat_api_key": "sk-************************************************",
    "chat_api_url": "https://api.siliconflow.cn/v1/chat/completions",
    "chat_api_model": "Qwen/Qwen3-8B"
}
```

## 📝 **日志文件**

日志位于 `HOME/.cliptranslate_logs`

## ⚠️ **注意事项**

❗ 该翻译服务依赖于大模型，会产生API调用费用

❗ 全局快捷键功能仅在 Windows 平台上可用

## 🎨 **资源**

1️⃣ **PySide6教程**
本项目基于PySide6构建，学习资源：
https://www.pythonguis.com/tutorials/pyside6-creating-your-first-window/

2️⃣ **图标资源**
本项目icon来自阿里巴巴矢量图标库：
https://www.iconfont.cn/