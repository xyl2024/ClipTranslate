import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CHAT_BASE_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
DEFAULT_HOTKEY_TO_CH = "f2"
DEFAULT_HOTKEY_TO_EN = "f4"


class ConfigManager:
    DEFAULT_CONFIG = {
        "hotkey_to_chinese": DEFAULT_HOTKEY_TO_CH,
        "hotkey_to_english": DEFAULT_HOTKEY_TO_EN,
        # 通用聊天模型配置
        "chat_api_key": "",
        "chat_api_url": DEFAULT_CHAT_BASE_URL,
        "chat_api_model": DEFAULT_CHAT_MODEL,
    }

    def __init__(self):
        self.config_dir = Path.home() / ".cliptranslate"
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()

    def load_config(self):
        try:
            self.config_dir.mkdir(exist_ok=True)

            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                    # 配置迁移：处理旧版本的配置格式
                    self._migrate_old_config(config)

                    # 确保所有默认键都存在
                    for key, default_value in self.DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = default_value
                    return config
            else:
                self.save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}。使用默认配置。")
            return self.DEFAULT_CONFIG.copy()

    def _migrate_old_config(self, config):
        # 如果存在旧的配置键，将其迁移到新的配置键
        if "api_key" in config and not config.get("chat_api_key"):
            config["chat_api_key"] = config["api_key"]
            logger.info("迁移旧配置：api_key -> chat_api_key")

        if "api_url" in config and not config.get("chat_api_url"):
            config["chat_api_url"] = config["api_url"]
            logger.info("迁移旧配置：api_url -> chat_api_url")

        if "api_model" in config and not config.get("chat_api_model"):
            config["chat_api_model"] = config["api_model"]
            logger.info("迁移旧配置：api_model -> chat_api_model")

        old_keys = ["api_key", "api_url", "api_model"]
        for key in old_keys:
            if key in config:
                del config[key]
                logger.info(f"删除旧配置键: {key}")

        # 迁移 Qwen 配置到 Chat 配置
        if not config.get("chat_api_key") and config.get("qwen_api_key"):
            config["chat_api_key"] = config["qwen_api_key"]
            logger.info("迁移旧配置：qwen_api_key -> chat_api_key")

        if not config.get("chat_api_url") and config.get("qwen_api_url"):
            config["chat_api_url"] = config["qwen_api_url"]
            logger.info("迁移旧配置：qwen_api_url -> chat_api_url")

        if not config.get("chat_api_model") and config.get("qwen_api_model"):
            config["chat_api_model"] = config["qwen_api_model"]
            logger.info("迁移旧配置：qwen_api_model -> chat_api_model")

        # 如果 translator_type 是 qwen，改为 chat
        if config.get("translator_type") == "qwen":
            config["translator_type"] = "chat"
            logger.info("迁移旧配置：translator_type qwen -> chat")

    def save_config(self, config=None):
        if config:
            self.config = config

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def get_config(self):
        return self.config

    def update_config(self, new_config):
        self.config.update(new_config)
        return self.save_config()

    def get(self, key, default=None):
        return self.config.get(key, default)


