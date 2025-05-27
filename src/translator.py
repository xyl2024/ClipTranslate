import json
import logging
import requests

logger = logging.getLogger(__name__)

SEPARATOR = "<user_input>"
SYSTEM_PROMPT_CH = f"""你是一个专业的翻译助手。请将用户提供的文本翻译成中文。用户提供的文本被一对标签{SEPARATOR}包含。
翻译要求：
1. 如果用户输入的文本是中文，直接原封不动地输出原文；
2. 保持原文的语气和风格，确保翻译准确、自然、流畅；
3. 对于专业术语，优先使用标准译名；
4. 如果用户输入的文本是一个句子，直接输出翻译结果，不要添加任何解释或说明；
5. 如果用户输入的文本是一个英语单词（包括原型、过去时以及进行时等语态），你需要尝试提供对该英语单词的解释，包括词性、读音、一个或多个中文意思以及对应的双语例句；
"""
SYSTEM_PROMPT_EN = f"""You are a professional translation assistant. Please translate the user's text into English. The text provided by the user is enclosed within a pair of tags {SEPARATOR}.
Translation requirements:
1. If the text input by the user is in English, output the original text as is.
2. Maintain the tone and style of the original text, ensuring an accurate, natural, and fluent translation.
3. For professional terms, prefer the standard translated names.
4. Directly output the translation result without adding any explanations or comments.
"""


class Translator:
    def translate(self, text, target_lang="Chinese"):
        raise NotImplementedError("Translator派生类未实现translate()方法")

    def translate_stream(self, text, target_lang="Chinese", callback=None):
        raise NotImplementedError("Translator派生类未实现translate_stream()方法")


class QwenTranslator(Translator):
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = self.config.get("qwen_api_key", "")
        self.api_url = self.config.get("qwen_api_url", "")
        self.api_model = self.config.get("qwen_api_model", "")
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.api_model,
        }
        if not self.api_key:
            logger.error("未提供API密钥，翻译功能将不可用")

        logger.info("千问翻译器初始化完成")

    def update_config(self, config):
        self.config = config
        self.api_key = config.get("qwen_api_key", self.api_key)
        self.api_url = config.get("qwen_api_url", self.api_url)
        self.api_model = config.get("qwen_api_model", self.api_model)
        logger.info("翻译器配置已更新")

    def translate(self, text, target_lang="Chinese"):
        if target_lang not in ["Chinese", "English"]:
            target_lang = "Chinese"

        if not self.api_key:
            raise ValueError("未配置API密钥，请在设置中配置")

        if not self.api_url:
            raise ValueError("未配置API URL，请在设置中配置")

        if not self.api_model:
            raise ValueError("未配置API模型，请在设置中配置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.api_model,
            "messages": [{"role": "user", "content": text}],
            "translation_options": {"source_lang": "auto", "target_lang": target_lang},
        }

        response = requests.post(self.api_url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_content = response.json()["choices"][0]["message"][
                "content"
            ].strip()
            logger.info(f"原文：{text}")
            logger.info(f"译文({target_lang})：{response_content}")
            return response_content
        else:
            raise Exception(f"API错误: {response.status_code} - {response.text}")

    def translate_stream(self, text, target_lang="Chinese", callback=None):
        if target_lang not in ["Chinese", "English"]:
            target_lang = "Chinese"

        if not self.api_key:
            raise ValueError("未配置API密钥，请在设置中配置")

        if not self.api_url:
            raise ValueError("未配置API URL，请在设置中配置")

        if not self.api_model:
            raise ValueError("未配置API模型，请在设置中配置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.api_model,
            "messages": [{"role": "user", "content": text}],
            "translation_options": {"source_lang": "auto", "target_lang": target_lang},
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                stream=True,
            )

            if response.status_code != 200:
                raise Exception(f"API错误: {response.status_code} - {response.text}")

            self.reset_last_usage()

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        json_str = line[6:]  # 跳过 "data: " 前缀
                        if json_str == "[DONE]":  # 流结束标记
                            break

                        try:
                            chunk = json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"无法解析 JSON: {json_str}, 错误: {e}")

                        if chunk["choices"]:
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                if callback:
                                    callback(content)
                        else:
                            self.last_usage = {
                                "prompt_tokens": chunk["usage"].get("prompt_tokens", 0),
                                "completion_tokens": chunk["usage"].get(
                                    "completion_tokens", 0
                                ),
                                "total_tokens": chunk["usage"].get("total_tokens", 0),
                                "model": chunk["model"],
                            }

            logger.info(f"原文：{text[:20]}......")
            logger.info(f"译文：{content[:20]}......")
            logger.info(f"成本: {self.last_usage}")
            return content

        except Exception as e:
            logger.error(f"流式翻译过程中发生错误: {e}")
            raise

    def reset_last_usage(self):
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.api_model,
        }

    def get_last_usage(self):
        return self.last_usage


class ChatTranslator(Translator):
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = self.config.get("chat_api_key", "")
        self.api_url = self.config.get("chat_api_url", "")
        self.api_model = self.config.get("chat_api_model", "")
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.api_model,
        }

        if not self.api_key:
            logger.error("未提供API密钥，翻译功能将不可用")

        logger.info("通用聊天翻译器初始化完成")

    def _build_translation_prompt(self, text, target_lang):
        """构建翻译提示词"""
        if target_lang == "Chinese":
            system_prompt = SYSTEM_PROMPT_CH
        else:
            system_prompt = SYSTEM_PROMPT_EN

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": SEPARATOR + text + SEPARATOR},
        ]

    def translate_stream(self, text, target_lang="Chinese", callback=None):
        if target_lang not in ["Chinese", "English"]:
            target_lang = "Chinese"

        if not self.api_key:
            raise ValueError("未配置API密钥，请在设置中配置")

        if not self.api_url:
            raise ValueError("未配置API URL，请在设置中配置")

        if not self.api_model:
            raise ValueError("未配置API模型，请在设置中配置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = self._build_translation_prompt(text, target_lang)

        data = {
            "model": self.api_model,
            "messages": messages,
            "stream": True,
            "enable_thinking": False,  # todo，需要适配一下无thinking功能的大模型
            "temperature": 0.3,  # 降低随机性，提高翻译一致性
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                stream=True,
            )

            if response.status_code != 200:
                raise Exception(f"API错误: {response.status_code} - {response.text}")

            self.reset_last_usage()
            full_content = ""

            for line in response.iter_lines():
                if line:
                    # logger.debug(line.decode("utf-8"))
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        json_str = line[6:]  # 跳过 "data: " 前缀
                        if json_str.strip() == "[DONE]":  # 流结束标记
                            break

                        try:
                            chunk = json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"无法解析 JSON: {json_str}, 错误: {e}")
                            continue

                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            # logger.debug(delta)
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                if callback:
                                    callback(full_content)

                        # 暂时不统计，建议使用免费模型。
                        # # 处理使用量统计（如果有）
                        # if "usage" in chunk:
                        #     self.last_usage = {
                        #         "prompt_tokens": chunk["usage"].get("prompt_tokens", 0),
                        #         "completion_tokens": chunk["usage"].get("completion_tokens", 0),
                        #         "total_tokens": chunk["usage"].get("total_tokens", 0),
                        #         "model": chunk.get("model", self.api_model),
                        #     }

            logger.info(f"原文：{text[:15]}...")
            logger.info(f"译文({target_lang})：{full_content[:15]}...")
            # logger.info(f"Token使用量: {self.last_usage}")
            logger.info(f"翻译模型：{self.last_usage.get('model', '未知')}")

            return full_content

        except Exception as e:
            logger.error(f"流式翻译过程中发生错误: {e}")
            raise

    def update_config(self, config):
        self.config = config
        self.api_key = config.get("chat_api_key", self.api_key)
        self.api_url = config.get("chat_api_url", self.api_url)
        self.api_model = config.get("chat_api_model", self.api_model)
        logger.info("通用聊天翻译器配置已更新")

    def reset_last_usage(self):
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.api_model,
        }

    def get_last_usage(self):
        return self.last_usage
