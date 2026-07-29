"""使用实例配置的代理查询出口 IP。"""

from __future__ import annotations

import asyncio
import os


def configured_proxy() -> str | None:
    """读取实例首个代理地址。

    Returns:
        配置的首个代理地址；未配置时返回 ``None``。
    """
    proxy = os.getenv("PROXY_URL", "").split(",", 1)[0].strip()
    return proxy.replace("{}", "chat2api-status") or None


async def fetch_exit_ip() -> str:
    """通过实例代理查询当前出口 IP。

    Returns:
        ``api.ipify.org`` 返回的出口 IP。
    """
    from utils.Client import Client

    client = Client(proxy=configured_proxy(), timeout=8)
    try:
        response = await client.get("https://api.ipify.org")
        if response.status_code != 200 or not response.text.strip():
            raise RuntimeError(f"exit IP probe failed: HTTP {response.status_code}")
        return response.text.strip()
    finally:
        await client.close()


def main() -> None:
    """查询并打印出口 IP。"""
    print(asyncio.run(fetch_exit_ip()))


if __name__ == "__main__":
    main()
