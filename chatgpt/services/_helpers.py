"""无状态头部工具函数。

供 ChatService、Mixin 与 Gateway 类型化和清洗 HTTP 头部使用。
原始位置：chatgpt/ChatService.py:46-66
"""

import json


_FINGERPRINT_HEADER_KEYS = {
    "user-agent", "oai-device-id", "oai-session-id",
    "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform",
    "sec-ch-ua-full-version-list", "sec-ch-ua-full-version",
    "sec-ch-ua-bitness", "sec-ch-ua-model", "sec-ch-ua-platform-version",
    "sec-ch-ua-arch", "sec-ch-ua-form-factors",
}


def _stringify_header_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _sanitize_headers(headers):
    clean = {}
    for key, value in (headers or {}).items():
        if not key:
            continue
        value = _stringify_header_value(value)
        if value is not None:
            clean[str(key)] = value
    return clean


def _sanitize_fingerprint_headers(fingerprint):
    """仅保留可作为 HTTP 头的指纹字段并规范值类型。"""
    return _sanitize_headers({
        key: value
        for key, value in (fingerprint or {}).items()
        if key in _FINGERPRINT_HEADER_KEYS
    })
