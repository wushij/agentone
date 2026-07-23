"""app/tools/text/tool_text.py — 工具文本解析辅助"""

from __future__ import annotations

import re

_SEARCH_PREFIXES = (
    "请搜索", "帮我搜索", "帮我查", "搜索一下", "搜一下",
    "查一下", "查询一下", "网上搜", "search", "google", "百度",
)

_FILE_LIST_HINTS = (
    "文件列表", "有哪些文件", "我的文件", "上传了哪些",
    "列出文件", "所有文件", "文件清单",
)

_FILE_PREFIXES = (
    "读取文件", "打开文件", "查看文件", "文件内容", "读一下", "看看文件",
)


def strip_leading_prefixes(text: str, prefixes: tuple[str, ...]) -> str:
    result = text.strip()
    lowered = result.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix.lower()):
            result = result[len(prefix):].strip(" ：:，,。?？!！")
            lowered = result.lower()
    return result.strip()


def extract_search_query(user_input: str) -> str:
    text = strip_leading_prefixes(user_input, _SEARCH_PREFIXES)
    text = re.sub(r"^(搜索|查询|查找)\s*", "", text, flags=re.IGNORECASE).strip(" ：:，,。?？")
    return text or user_input.strip()


def wants_file_list(user_input: str) -> bool:
    text = user_input.strip()
    if not text:
        return True
    return any(h in text for h in _FILE_LIST_HINTS)


def extract_file_query(user_input: str) -> str:
    text = strip_leading_prefixes(user_input, _FILE_PREFIXES)
    text = re.sub(r"^(文件|读取|打开|查看)\s*", "", text).strip(" ：:，,。?？")
    return text


def extract_database_query(user_input: str) -> str:
    text = user_input.strip()
    if text.lower().startswith("select"):
        return text
    text = strip_leading_prefixes(
        text,
        ("请查询数据库", "查数据库", "执行sql", "运行sql", "sql查询"),
    )
    return text