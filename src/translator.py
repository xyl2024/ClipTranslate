"""翻译器模块

提供抽象翻译器基类和具体实现。
"""

import json
import logging
from openai import OpenAI
from typing import Optional, Callable, Dict, Any

import requests

logger = logging.getLogger(__name__)

SEPARATOR = "<user_input>"
SYSTEM_PROMPT_CH = f"""你是一个专业的翻译助手。请将用户提供的文本翻译成中文。用户提供的文本被一对标签{SEPARATOR}包含。
翻译要求：
1. 如果用户输入的文本是中文，直接原封不动地输出原文；
2. 保持原文的语气和风格，确保翻译准确、自然、流畅；
3. 对于专业术语，优先使用标准译名；
4. 如果用户输入的文本是一个句子，直接输出翻译结果，不要添加任何解释或说明，也不要带上{SEPARATOR}标签；
5. 如果用户输入的文本是一个英语单词（包括原型、过去时以及进行时等语态），你需要尝试提供对该英语单词的解释，包括词性、读音、一个或多个中文意思以及对应的双语例句；
"""
SYSTEM_PROMPT_EN = f"""You are a professional translation assistant. Please translate the user's text into English. The text provided by the user is enclosed within a pair of tags {SEPARATOR}.
Translation requirements:
1. If the text input by the user is in English, output the original text as is.
2. Maintain the tone and style of the original text, ensuring an accurate, natural, and fluent translation.
3. For professional terms, prefer the standard translated names.
4. Directly output the translation result without adding any explanations or comments, and do not include the {SEPARATOR} tag.
"""

SYSTEM_PROMPT_EMOJI = f"""你是一个emoji生成助手。请根据用户提供的文本，生成最合适的emoji表情来表达文本的情感或内容。
要求：
1. 直接输出emoji，不要添加任何解释或说明；
2. 可以输出多个emoji来表达复杂情感；
3. emoji要准确反映文本的情感、语气和内容；
4. 不要输出{SEPARATOR}标签。
"""

# 支持的目标语言
SUPPORTED_TARGET_LANGUAGES = ["Chinese", "English"]


class Translator:
    """翻译器抽象基类。

    所有具体翻译器实现应继承此类并实现 `translate_stream` 方法。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化翻译器。

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.last_usage: Dict[str, Any] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": "",
        }

    def translate(self, text: str, target_lang: str = "Chinese") -> str:
        """翻译文本（非流式）。

        Args:
            text: 待翻译的文本
            target_lang: 目标语言 ("Chinese" 或 "English")

        Returns:
            翻译后的文本
        """
        raise NotImplementedError("Translator派生类未实现translate()方法")

    def translate_stream(
        self,
        text: str,
        target_lang: str = "Chinese",
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """流式翻译文本。

        Args:
            text: 待翻译的文本
            target_lang: 目标语言 ("Chinese" 或 "English")
            callback: 接收进度更新的回调函数

        Returns:
            翻译后的完整文本
        """
        raise NotImplementedError("Translator派生类未实现translate_stream()方法")

    def _validate_config(self, api_key: str, api_url: str, api_model: str) -> None:
        """验证翻译器配置。

        Args:
            api_key: API 密钥
            api_url: API 地址
            api_model: API 模型

        Raises:
            ValueError: 当任何必要配置缺失时
        """
        if not api_key:
            raise ValueError("未配置API密钥，请在设置中配置")

        if not api_url:
            raise ValueError("未配置API URL，请在设置中配置")

        if not api_model:
            raise ValueError("未配置API模型，请在设置中配置")

    def _validate_target_lang(self, target_lang: str) -> str:
        """验证并规范化目标语言。

        Args:
            target_lang: 目标语言

        Returns:
            规范化后的目标语言
        """
        if target_lang not in SUPPORTED_TARGET_LANGUAGES:
            target_lang = "Chinese"
        return target_lang

    def reset_last_usage(self) -> None:
        """重置最后的使用统计。"""
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": getattr(self, "api_model", ""),
        }

    def get_last_usage(self) -> Dict[str, Any]:
        """获取最后的使用统计。

        Returns:
            使用统计字典
        """
        return self.last_usage


class ChatTranslator(Translator):
    """通用聊天翻译器。

    使用 OpenAI 兼容的 API 进行翻译。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化聊天翻译器。

        Args:
            config: 配置字典，应包含 chat_api_key, chat_api_url, chat_api_model
        """
        super().__init__(config)
        self.api_key = self.config.get("chat_api_key", "")
        self.api_url = self.config.get("chat_api_url", "")
        self.api_model = self.config.get("chat_api_model", "")
        self.last_usage["model"] = self.api_model
        self.last_usage["base_url"] = self.api_url
        self.client: Optional[OpenAI] = None

        self._init_client()

        if not self.api_key:
            logger.error("未提供API密钥，翻译功能将不可用")

        logger.info("通用聊天翻译器初始化完成")

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端。"""
        if self.api_key and self.api_url:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_url,
            )

    def _build_translation_prompt(self, text: str, target_lang: str) -> list:
        """构建翻译提示词。

        Args:
            text: 待翻译的文本
            target_lang: 目标语言

        Returns:
            消息列表
        """
        if target_lang == "Chinese":
            system_prompt = SYSTEM_PROMPT_CH
        else:
            system_prompt = SYSTEM_PROMPT_EN

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": SEPARATOR + text + SEPARATOR},
        ]

    def translate_stream(
        self,
        text: str,
        target_lang: str = "Chinese",
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """流式翻译文本。"""
        target_lang = self._validate_target_lang(target_lang)
        self._validate_config(self.api_key, self.api_url, self.api_model)

        if not self.client:
            self._init_client()

        messages = self._build_translation_prompt(text, target_lang)

        try:
            self.reset_last_usage()
            full_content = ""

            stream = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,
                stream=True,
                temperature=0.3,  # 降低随机性，提高翻译一致性
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(full_content)

            logger.info(f"原文：{text[:15]}...")
            logger.info(f"译文({target_lang})：{full_content[:15]}...")
            logger.info(f"翻译模型：{self.last_usage.get('model', '未知')}")

            return full_content

        except Exception as e:
            logger.error(f"流式翻译过程中发生错误: {e}")
            raise

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新翻译器配置。

        Args:
            config: 新的配置字典
        """
        self.config = config
        self.api_key = config.get("chat_api_key", self.api_key)
        self.api_url = config.get("chat_api_url", self.api_url)
        self.api_model = config.get("chat_api_model", self.api_model)
        self.last_usage["model"] = self.api_model
        self._init_client()
        logger.info("通用聊天翻译器配置已更新")


class EmojiTranslator(Translator):
    """Emoji翻译器。

    使用 OpenAI 兼容的 API 生成与文本相符的 emoji。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Emoji翻译器。

        Args:
            config: 配置字典，应包含 chat_api_key, chat_api_url, chat_api_model
        """
        super().__init__(config)
        self.api_key = self.config.get("chat_api_key", "")
        self.api_url = self.config.get("chat_api_url", "")
        self.api_model = self.config.get("chat_api_model", "")
        self.last_usage["model"] = self.api_model
        self.last_usage["base_url"] = self.api_url
        self.client: Optional[OpenAI] = None

        self._init_client()

        if not self.api_key:
            logger.error("未提供API密钥，emoji功能将不可用")

        logger.info("Emoji翻译器初始化完成")

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端。"""
        if self.api_key and self.api_url:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_url,
            )

    def translate_stream(
        self,
        text: str,
        target_lang: str = "Emoji",
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """流式生成emoji。

        Args:
            text: 待处理的文本
            target_lang: 目标语言（此处固定为Emoji）
            callback: 接收进度更新的回调函数

        Returns:
            生成的emoji
        """
        self._validate_config(self.api_key, self.api_url, self.api_model)

        if not self.client:
            self._init_client()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_EMOJI},
            {"role": "user", "content": SEPARATOR + text + SEPARATOR},
        ]

        try:
            self.reset_last_usage()
            full_content = ""

            stream = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,
                stream=True,
                temperature=0.7,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(full_content)

            logger.info(f"原文：{text[:15]}...")
            logger.info(f"Emoji：{full_content}")
            logger.info(f"模型：{self.last_usage.get('model', '未知')}")

            return full_content

        except Exception as e:
            logger.error(f"生成emoji过程中发生错误: {e}")
            raise

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新翻译器配置。

        Args:
            config: 新的配置字典
        """
        self.config = config
        self.api_key = config.get("chat_api_key", self.api_key)
        self.api_url = config.get("chat_api_url", self.api_url)
        self.api_model = config.get("chat_api_model", self.api_model)
        self.last_usage["model"] = self.api_model
        self._init_client()
        logger.info("Emoji翻译器配置已更新")