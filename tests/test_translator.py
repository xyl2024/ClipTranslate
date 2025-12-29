"""测试 translator.py 中的翻译器"""

from unittest.mock import Mock, MagicMock, patch

from translator import Translator, ChatTranslator, EmojiTranslator


def test_translator_validate_config():
    """测试配置验证"""
    translator = Translator()

    # 正常配置
    translator._validate_config("api_key", "api_url", "model")

    # 缺少 API key
    try:
        translator._validate_config("", "api_url", "model")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "API密钥" in str(e)

    # 缺少 API URL
    try:
        translator._validate_config("api_key", "", "model")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "API URL" in str(e)

    # 缺少模型
    try:
        translator._validate_config("api_key", "api_url", "")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "API模型" in str(e)


def test_translator_validate_target_lang():
    """测试目标语言验证"""
    translator = Translator()

    # 有效的语言
    assert translator._validate_target_lang("Chinese") == "Chinese"
    assert translator._validate_target_lang("English") == "English"

    # 无效的语言，应该默认为 Chinese
    assert translator._validate_target_lang("Spanish") == "Chinese"
    assert translator._validate_target_lang("") == "Chinese"


def test_translator_reset_last_usage():
    """测试重置使用统计"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = ChatTranslator(config)

    translator.last_usage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
    }

    translator.reset_last_usage()

    assert translator.last_usage["prompt_tokens"] == 0
    assert translator.last_usage["completion_tokens"] == 0
    assert translator.last_usage["total_tokens"] == 0


def test_translator_get_last_usage():
    """测试获取使用统计"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = ChatTranslator(config)

    usage = translator.get_last_usage()

    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage


def test_chat_translate_not_implemented():
    """测试基类的 translate 方法未实现"""
    translator = Translator()

    try:
        translator.translate("hello", "Chinese")
        assert False, "应该抛出 NotImplementedError"
    except NotImplementedError:
        pass


def test_chat_translate_stream_not_implemented():
    """测试基类的 translate_stream 方法未实现"""
    translator = Translator()

    try:
        translator.translate_stream("hello", "Chinese")
        assert False, "应该抛出 NotImplementedError"
    except NotImplementedError:
        pass


def test_chat_translator_init():
    """测试 ChatTranslator 初始化"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = ChatTranslator(config)

    assert translator.api_key == "test_key"
    assert translator.api_url == "test_url"
    assert translator.api_model == "test_model"
    assert translator.last_usage["model"] == "test_model"


def test_chat_translator_update_config():
    """测试 ChatTranslator 更新配置"""
    config = {
        "chat_api_key": "old_key",
        "chat_api_url": "old_url",
        "chat_api_model": "old_model",
    }
    translator = ChatTranslator(config)

    new_config = {
        "chat_api_key": "new_key",
        "chat_api_url": "new_url",
        "chat_api_model": "new_model",
    }

    translator.update_config(new_config)

    assert translator.api_key == "new_key"
    assert translator.api_url == "new_url"
    assert translator.api_model == "new_model"


def test_chat_translator_build_prompt():
    """测试 ChatTranslator 构建提示词"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = ChatTranslator(config)

    # 中文翻译提示词
    messages = translator._build_translation_prompt("hello", "Chinese")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "hello" in messages[1]["content"]

    # 英文翻译提示词
    messages = translator._build_translation_prompt("你好", "English")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "You are a professional translation assistant" in messages[0]["content"]


@patch("translator.OpenAI")
def test_chat_translator_translate_stream(mock_openai):
    """测试 ChatTranslator 流式翻译"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = ChatTranslator(config)

    # 模拟 OpenAI 客户端
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    translator.client = mock_client

    # 模拟流式响应
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta.content = "测试"
    mock_stream = [mock_chunk, mock_chunk]
    mock_client.chat.completions.create.return_value = iter(mock_stream)

    callback = MagicMock()
    result = translator.translate_stream("test", "Chinese", callback)

    # 验证结果
    assert "测试" in result
    callback.assert_called()
    mock_client.chat.completions.create.assert_called_once()


def test_emoji_translator_init():
    """测试 EmojiTranslator 初始化"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = EmojiTranslator(config)

    assert translator.api_key == "test_key"
    assert translator.api_url == "test_url"
    assert translator.api_model == "test_model"
    assert translator.last_usage["model"] == "test_model"


@patch("translator.OpenAI")
def test_emoji_translator_translate_stream(mock_openai):
    """测试 EmojiTranslator 流式生成"""
    config = {
        "chat_api_key": "test_key",
        "chat_api_url": "test_url",
        "chat_api_model": "test_model",
    }
    translator = EmojiTranslator(config)

    # 模拟 OpenAI 客户端
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    translator.client = mock_client

    # 模拟流式响应
    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta.content = "😊"
    mock_stream = [mock_chunk]
    mock_client.chat.completions.create.return_value = iter(mock_stream)

    callback = MagicMock()
    result = translator.translate_stream("happy", "Emoji", callback)

    # 验证结果
    assert result == "😊"
    callback.assert_called()
    mock_client.chat.completions.create.assert_called_once()
