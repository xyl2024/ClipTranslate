<p align="center">
  <img width="300px" height="100px" src="assets/logo.svg" />
</p>

<p align="center">ClipTranslate, a clipboard translation tool based on LLM</p>

<p align="center">English | <a href="README.md">中文</a></p>


## 🚀 **Project Overview**

ClipTranslate is a convenient Windows desktop translation tool that allows users to quickly translate the text content in their clipboard into Chinese or English using global hotkeys. The original text and its translation are displayed in a separate window.

> This project is developed and tested using Claude.

## 🔧 **Key Features**

- Trigger translation via global hotkeys
- Automatically retrieve clipboard text content
- Use Alibaba Cloud's Qianwen Translation Model API for translation
- Use a general chat large model API for translation (Not yet perfected, currently only tested with the free Qwen/Qwen3-8B model from Silicon Flow)
- Display both original text and translation in a separate window

## 📥 **Installation Steps**

### Download the executable file

- Download the latest zip file from the Release page https://github.com/xyl2024/ClipTranslate/releases
- Double-click to run ClipTranslate.exe

### Run with Python 

> This project is managed using `uv`. You can refer to the [official manual](https://docs.astral.sh/uv/) to learn how to install and use `uv`.

1. Clone or download this repository
2. Install dependencies
3. Run the application

```bash
$ git clone https://github.com/xyl2024/ClipTranslate.git
$ cd ClipTranslate
$ uv sync
$ uv run src/main.py
```

## ⚙️ **First-time Setup**

1. After running the application, find the ClipTranslate icon in the system tray
2. Right-click the icon and select "Settings"
3. Enter your Alibaba Cloud API key/Chat model API key
4. Customize the translation hotkeys
5. Click "Save" to complete the setup

## 💡 **How to Use**

1. Copy the text you want to translate (Ctrl+C)
2. Press the configured hotkey:  
   - F2 to translate to Chinese  
   - F4 to translate to English
3. The translation window will automatically display, showing both the original and translated text
4. Click the "Copy Translation" button to copy the translation
5. Press the ESC key or click the close button to hide the window
6. Double-click the system tray icon to show/hide the translation window

🎥 Example:

![](assets/usage.webp)


## 📂 **Configuration File**

The configuration file is located at `HOME/.cliptranslate/config.json`:

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

## 📝 **Log Files**

Logs are located at `HOME/.cliptranslate_logs`

## ⚠️ **Cautions**

❗ This translation service relies on large models and may incur API usage fees

❗ The global hotkey functionality is only available on Windows

## 🎨 **Resources**

- **PySide6 Tutorial**
This project is built with PySide6. Reference [Learning resources](https://www.pythonguis.com/tutorials/pyside6-creating-your-first-window/).

- **Icon Resources**
The icons in this project come from [Alibaba's Icon Library](https://www.iconfont.cn/).
The logo for this project comes from [text-to-svg](https://github.com/JiuRanYa/text-to-svg). 

- **LLM**
  - [Qwen-MT](https://help.aliyun.com/zh/model-studio/machine-translation)
  - [siliconflow-Qwen/Qwen3-8B](https://cloud.siliconflow.cn/models?target=Qwen/Qwen3-8B)