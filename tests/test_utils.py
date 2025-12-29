"""测试 utils.py 中的工具函数"""

from utils import clean_string


def test_clean_string_simple():
    """测试简单的字符串清理"""
    text = "  hello   world  "
    result = clean_string(text)
    assert result == "hello world"


def test_clean_string_multiple_spaces():
    """测试多个连续空格"""
    text = "this   has    many    spaces"
    result = clean_string(text)
    assert result == "this has many spaces"


def test_clean_string_multiline():
    """测试多行文本清理"""
    text = "  line 1  \n  line 2  \n  line 3  "
    result = clean_string(text)
    assert result == "line 1\nline 2\nline 3"


def test_clean_string_empty_lines():
    """测试空行过滤"""
    text = "line 1\n\nline 2\n\n\nline 3"
    result = clean_string(text)
    assert result == "line 1\nline 2\nline 3"


def test_clean_string_all_spaces():
    """测试全空格文本"""
    text = "     \n    \n     "
    result = clean_string(text)
    assert result == ""


def test_clean_string_empty():
    """测试空字符串"""
    text = ""
    result = clean_string(text)
    assert result == ""


def test_clean_string_preserve_single_space():
    """测试保留单个空格"""
    text = "hello world"
    result = clean_string(text)
    assert result == "hello world"


def test_clean_string_complex():
    """测试复杂文本"""
    text = "  hello   world  \n\n  foo   bar  \n  test  "
    result = clean_string(text)
    assert result == "hello world\nfoo bar\ntest"
