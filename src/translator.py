import logging
import requests
import json

logger = logging.getLogger(__name__)


class Translator:
    def translate(self, text, target_lang="Chinese"):
        raise NotImplementedError("Translator派生类未实现translate()方法")

    def translate_stream(self, text, target_lang="Chinese", callback=None):
        raise NotImplementedError("Translator派生类未实现translate_stream()方法")


class AliyuncsTranslator(Translator):
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = self.config.get("api_key", "")
        self.api_url = self.config.get("api_url", "")
        self.api_model = self.config.get("api_model", "")
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": self.api_model,
        }
        if not self.api_key:
            logger.error("未提供API密钥，翻译功能将不可用")

        logger.info("AliyuncsTranslator init done.")

    def update_config(self, config):
        self.config = config
        self.api_key = config.get("api_key", self.api_key)
        self.api_url = config.get("api_url", self.api_url)
        self.api_model = config.get("api_model", self.api_model)
        logger.info("Translator config updated.")

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

            logger.info(f"原文：{text}")
            logger.info(f"译文({target_lang})：{content}")
            logger.info(f"Token使用: {self.last_usage}")

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
