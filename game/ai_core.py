"""
AI_try 核心逻辑 — 纯 Python，无 Ren'Py 依赖，可被 pytest 测试。
"""

import json

DEFAULT_MODEL = "deepseek-v4-flash"
SYSTEM_PROMPT = "你是一个温柔的心理咨询师。请按以下JSON格式回复：{\"emotion\": \"happy|sad|angry|surprised|neutral\", \"text\": \"你的回复内容\"}"
VALID_EMOTIONS = {"happy", "sad", "angry", "surprised", "neutral"}


def escape_renpy_text_braces(s: str) -> str:
    """将字符串中的花括号转义，避免 Ren'Py text 把 {...} 当成文本标签。"""
    if not isinstance(s, str):
        s = str(s)
    return s.replace("{", "{{").replace("}", "}}")


def split_text_into_pages(text: str, max_chars_per_page: int = 400) -> list[str]:
    """按句号分页，每页不超过 max_chars_per_page 字。"""
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return ["(没有内容)"]
    pages = []
    while len(text) > max_chars_per_page:
        split_pos = text.rfind("。", 0, max_chars_per_page)
        if split_pos == -1:
            split_pos = text.rfind("，", 0, max_chars_per_page)
        if split_pos == -1:
            split_pos = max_chars_per_page
        pages.append(text[: split_pos + 1])
        text = text[split_pos + 1 :]
    if text:
        pages.append(text)
    return pages


def trim_messages(messages: list[dict], max_turns: int = 10) -> list[dict]:
    """限制历史长度，保留最近 max_turns 轮对话。"""
    max_msgs = 1 + max_turns * 2
    if len(messages) <= max_msgs:
        return messages
    if messages and messages[0].get("role") == "system":
        return messages[:1] + messages[-(max_turns * 2) :]
    return messages[-(max_turns * 2) :]


def build_request_data(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.75,
    max_tokens: int = 1000,
    response_format: dict | None = None,
) -> dict:
    """构建发送到 DeepSeek API 的请求体。"""
    data: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        data["response_format"] = response_format
    return data


def extract_emotion_from_json(response_text: str) -> str:
    """从 AI 的 JSON 格式回复中提取情绪字段。

    AI 被要求按 {"emotion": "<情绪>", "text": "<回复>"} 格式回复。
    如果解析失败或情绪值无效，返回 "neutral"。
    """
    if not response_text:
        return "neutral"
    text = response_text.strip()
    # 去掉 markdown 代码块标记
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else ""
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "neutral"
    emotion = data.get("emotion", "neutral")
    if emotion not in VALID_EMOTIONS:
        return "neutral"
    return emotion


def is_request_allowed(in_progress: bool) -> bool:
    """检查是否可以发起新的 AI 请求。

    Args:
        in_progress: 当前是否有请求正在进行中。
    Returns:
        True 如果没有请求在进行，False 如果已有请求正在处理。
    """
    return not in_progress
