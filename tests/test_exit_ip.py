import os
import sys
import types
import unittest
from unittest.mock import patch

from utils.exit_ip import configured_proxy, fetch_exit_ip


class FakeResponse:
    """提供出口探测测试所需的最小响应。"""

    status_code = 200
    text = "203.0.113.10\n"


class FakeClient:
    """记录探测请求使用的代理和关闭状态。"""

    instance = None

    def __init__(self, proxy=None, timeout=0):
        self.proxy = proxy
        self.timeout = timeout
        self.closed = False
        FakeClient.instance = self

    async def get(self, url):
        """返回固定出口 IP 响应。"""
        self.url = url
        return FakeResponse()

    async def close(self):
        """记录客户端已关闭。"""
        self.closed = True


class ExitIpTests(unittest.IsolatedAsyncioTestCase):
    """验证出口 IP 探测使用实例代理。"""

    async def test_probe_uses_configured_proxy(self):
        """探测请求读取首个代理并替换会话占位符。"""
        fake_module = types.ModuleType("utils.Client")
        fake_module.Client = FakeClient
        env = {"PROXY_URL": "socks5://proxy/{} , socks5://backup"}
        with patch.dict(os.environ, env, clear=False), patch.dict(
            sys.modules, {"utils.Client": fake_module}
        ):
            self.assertEqual(
                configured_proxy(), "socks5://proxy/chat2api-status"
            )
            self.assertEqual(await fetch_exit_ip(), "203.0.113.10")

        self.assertEqual(FakeClient.instance.timeout, 8)
        self.assertEqual(FakeClient.instance.url, "https://api.ipify.org")
        self.assertTrue(FakeClient.instance.closed)


if __name__ == "__main__":
    unittest.main()
