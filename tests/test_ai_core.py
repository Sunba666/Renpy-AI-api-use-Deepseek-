"""测试 ai_core 纯逻辑函数。"""

import pytest
import sys
import os

# 让 Python 能找到 game/ai_core.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from ai_core import (
    DEFAULT_MODEL,
    build_request_data,
    escape_renpy_text_braces,
    split_text_into_pages,
    trim_messages,
)


# ─── Cycle 1: Model name ────────────────────────────────────────────────────

class TestModelName:
    def test_default_model_is_v4_flash(self):
        """默认模型名应为 deepseek-v4-flash（非遗留的 deepseek-chat）。"""
        assert DEFAULT_MODEL == "deepseek-v4-flash"

    def test_build_request_data_uses_correct_model(self):
        """build_request_data 返回的请求体应包含正确的模型名。"""
        data = build_request_data(
            messages=[{"role": "user", "content": "hello"}]
        )
        assert data["model"] == "deepseek-v4-flash"

    def test_build_request_data_can_override_model(self):
        """应支持临时覆盖模型名。"""
        data = build_request_data(
            messages=[{"role": "user", "content": "hello"}],
            model="deepseek-v4-pro",
        )
        assert data["model"] == "deepseek-v4-pro"


# ─── 已有功能回归测试 ────────────────────────────────────────────────────────

class TestEscapeBraces:
    def test_braces_escaped(self):
        assert escape_renpy_text_braces("{hello}") == "{{hello}}"
        assert escape_renpy_text_braces("a{b}c") == "a{{b}}c"

    def test_no_braces_unchanged(self):
        assert escape_renpy_text_braces("hello world") == "hello world"

    def test_non_string_converted(self):
        assert escape_renpy_text_braces(42) == "42"


class TestSplitPages:
    def test_short_text_single_page(self):
        assert split_text_into_pages("你好") == ["你好"]

    def test_empty_text(self):
        assert split_text_into_pages("") == ["(没有内容)"]

    def test_split_at_period(self):
        long = "。".join(["第{}段".format(i) for i in range(1, 6)]) + "。"
        pages = split_text_into_pages(long, max_chars_per_page=10)
        assert len(pages) > 1


class TestTrimMessages:
    def test_below_limit_unchanged(self):
        msgs = [{"role": "user", "content": "hi"}]
        assert trim_messages(msgs, max_turns=10) == msgs

    def test_preserves_system_prompt(self):
        msgs = [{"role": "system", "content": "be nice"}] + [
            {"role": "user", "content": "msg{}".format(i)} for i in range(30)
        ]
        trimmed = trim_messages(msgs, max_turns=10)
        assert trimmed[0]["role"] == "system"
        assert len(trimmed) <= 21  # 1 system + 20 (10 turns)


# ─── Cycle 2: JSON Output 情绪提取 ──────────────────────────────────────────

class TestExtractEmotionFromJson:
    """extract_emotion_from_json() 从 AI 的 JSON 回复中提取情绪字段。"""

    def test_happy_emotion(self):
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "happy", "text": "太好了！"}'
        )
        assert result == "happy"

    def test_sad_emotion(self):
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "sad", "text": "我很难过..."}'
        )
        assert result == "sad"

    def test_angry_emotion(self):
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "angry", "text": "这太过分了"}'
        )
        assert result == "angry"

    def test_surprised_emotion(self):
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "surprised", "text": "真的吗？"}'
        )
        assert result == "surprised"

    def test_neutral_emotion_default(self):
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "neutral", "text": "今天天气不错。"}'
        )
        assert result == "neutral"

    def test_malformed_json_fallback_to_neutral(self):
        """非 JSON 回复应 fallback 到 neutral。"""
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            "我今天心情很好！"
        )
        assert result == "neutral"

    def test_missing_emotion_field_fallback(self):
        """JSON 中缺少 emotion 字段应 fallback 到 neutral。"""
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"text": "没有情绪字段"}'
        )
        assert result == "neutral"

    def test_invalid_emotion_value_fallback(self):
        """JSON 中 emotion 值无效应 fallback 到 neutral。"""
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '{"emotion": "ecstatic", "text": "太棒了！"}'
        )
        assert result == "neutral"

    def test_json_in_text_blocks(self):
        """AI 回复可能在 JSON 前后带 markdown 代码块标记。"""
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json(
            '```json\n{"emotion": "happy", "text": "你好！"}\n```'
        )
        assert result == "happy"

    def test_empty_string_fallback(self):
        """空字符串应 fallback 到 neutral。"""
        from ai_core import extract_emotion_from_json
        result = extract_emotion_from_json("")
        assert result == "neutral"


# ─── Cycle 3: 并发锁 ─────────────────────────────────────────────────────────

class TestConcurrencyGuard:
    def test_allows_request_when_free(self):
        from ai_core import is_request_allowed
        assert is_request_allowed(False) is True

    def test_blocks_request_when_in_progress(self):
        from ai_core import is_request_allowed
        assert is_request_allowed(True) is False
