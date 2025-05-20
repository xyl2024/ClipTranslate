import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    DEFAULT_CONFIG = {
        "hotkey_to_chinese": "f2",
        "hotkey_to_english": "f10",
        "api_key": "",
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "api_model": "qwen-mt-plus",
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
