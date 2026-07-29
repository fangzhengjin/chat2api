import json
import unittest

from utils.token_parser import is_refresh_token, parse_json


class RefreshTokenTypeTests(unittest.TestCase):
    """验证 RefreshToken 前缀识别与 JSON 导入分类。"""

    def test_rt_prefix_is_refresh_token(self):
        """所有以 rt 开头的新旧格式均识别为 RefreshToken。"""
        self.assertTrue(is_refresh_token("rt_legacy"))
        self.assertTrue(is_refresh_token("rt.1.A7ubw"))

    def test_json_refresh_token_field_keeps_rt_dot_format(self):
        """JSON 的 refreshToken 字段可导入 rt.1. 格式。"""
        token = "rt.1.A7ubw"
        result = parse_json(json.dumps({"refreshToken": token}))
        self.assertEqual(result["refresh_tokens"], [token])


if __name__ == "__main__":
    unittest.main()
