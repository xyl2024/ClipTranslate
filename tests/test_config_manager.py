"""测试 config_manager.py 中的配置管理"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from config_manager import ConfigManager


def test_config_manager_default_config():
    """测试默认配置"""
    manager = ConfigManager()
    config = manager.get_config()
    assert "hotkey_to_chinese" in config
    assert "hotkey_to_english" in config
    assert "chat_api_key" in config
    assert "chat_api_url" in config
    assert "chat_api_model" in config
    assert "window_opacity" in config


def test_config_manager_migrate_old_config():
    """测试旧配置迁移"""
    old_config = {
        "api_key": "old_key",
        "api_url": "old_url",
        "api_model": "old_model",
    }

    manager = ConfigManager()
    manager._migrate_old_config(old_config)

    assert "chat_api_key" in old_config
    assert old_config["chat_api_key"] == "old_key"
    assert "api_key" not in old_config


def test_config_manager_migrate_qwen_config():
    """测试 Qwen 配置迁移"""
    old_config = {
        "qwen_api_key": "qwen_key",
        "qwen_api_url": "qwen_url",
        "qwen_api_model": "qwen_model",
        "translator_type": "qwen",
    }

    manager = ConfigManager()
    manager._migrate_old_config(old_config)

    assert old_config["chat_api_key"] == "qwen_key"
    assert old_config["chat_api_url"] == "qwen_url"
    assert old_config["chat_api_model"] == "qwen_model"
    assert old_config["translator_type"] == "chat"


def test_config_manager_get():
    """测试获取配置值"""
    manager = ConfigManager()

    # 测试存在的键
    assert manager.get("hotkey_to_chinese") is not None

    # 测试不存在的键
    assert manager.get("non_existent_key", "default") == "default"


def test_config_manager_update():
    """测试更新配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        with patch.object(ConfigManager, "__init__", lambda self: None):
            manager = ConfigManager()
            manager.config_dir = tmpdir_path
            manager.config_file = tmpdir_path / "config.json"
            manager.config = ConfigManager.DEFAULT_CONFIG.copy()

            result = manager.update_config({"hotkey_to_chinese": "f3"})

            assert result is True
            assert manager.config["hotkey_to_chinese"] == "f3"

            # 验证文件已保存
            with open(manager.config_file, "r", encoding="utf-8") as f:
                saved_config = json.load(f)
                assert saved_config["hotkey_to_chinese"] == "f3"


def test_config_manager_save_config():
    """测试保存配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        with patch.object(ConfigManager, "__init__", lambda self: None):
            manager = ConfigManager()
            manager.config_dir = tmpdir_path
            manager.config_file = tmpdir_path / "config.json"
            manager.config = ConfigManager.DEFAULT_CONFIG.copy()

            result = manager.save_config()

            assert result is True
            assert manager.config_file.exists()


def test_config_manager_load_from_file():
    """测试从文件加载配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config_file = tmpdir_path / "config.json"

        # 写入测试配置
        test_config = {
            "hotkey_to_chinese": "f5",
            "hotkey_to_english": "f6",
            "chat_api_key": "test_key",
            "chat_api_url": "test_url",
            "chat_api_model": "test_model",
            "window_opacity": 0.9,
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(test_config, f)

        with patch.object(ConfigManager, "__init__", lambda self: None):
            manager = ConfigManager()
            manager.config_dir = tmpdir_path
            manager.config_file = config_file

            config = manager.load_config()

            assert config["hotkey_to_chinese"] == "f5"
            assert config["window_opacity"] == 0.9


def test_config_manager_load_missing_keys():
    """测试加载缺少默认键的配置"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config_file = tmpdir_path / "config.json"

        # 写入不完整的配置
        test_config = {"hotkey_to_chinese": "f5"}
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(test_config, f)

        with patch.object(ConfigManager, "__init__", lambda self: None):
            manager = ConfigManager()
            manager.config_dir = tmpdir_path
            manager.config_file = config_file

            config = manager.load_config()

            # 应该补全缺少的键
            assert "hotkey_to_english" in config
            assert "chat_api_url" in config
