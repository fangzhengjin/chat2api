import unittest

from fastapi import HTTPException

from api.models import filter_chatgpt_models_payload, resolve_request_model
from chatgpt.services.model_mixin import ModelMixin


class FakeResponse:
    """提供模型接口测试所需的最小响应。"""

    status_code = 200
    headers = {"Content-Type": "application/json"}
    text = ""

    def json(self):
        """返回包含精确模型 slug 的响应数据。"""
        return {"models": [{"slug": "gpt-5-5-pro"}]}


class FakeSession:
    """记录远程模型列表请求次数。"""

    def __init__(self):
        self.calls = 0

    async def get(self, url, headers, timeout):
        """记录一次请求并返回固定模型列表。"""
        self.calls += 1
        return FakeResponse()


class ModelSelectionTests(unittest.IsolatedAsyncioTestCase):
    """验证远程精确模型选择与缓存行为。"""

    def setUp(self):
        """清理跨测试共享的模型缓存。"""
        ModelMixin.available_model_cache.clear()

    def test_request_model_is_not_rewritten(self):
        """普通模型保持精确 slug，自定义 GPT 仍解析 gizmo_id。"""
        self.assertEqual(resolve_request_model("gpt-5-pro"), ("gpt-5-pro", None))
        self.assertEqual(resolve_request_model("gpt-5-5-pro"), ("gpt-5-5-pro", None))
        self.assertEqual(resolve_request_model("g-example"), ("gpt-5-5", "g-example"))

    def test_chatgpt_models_are_filtered_named_and_ordered(self):
        """网页端仅展示白名单模型，并生成对应菜单与默认模型。"""
        payload = {
            "models": [
                {"slug": "gpt-5-6-thinking", "title": "Thinking"},
                {"slug": "gpt-4o", "title": "GPT-4o"},
                {"slug": "gpt-5-3", "title": "GPT-5.3"},
                {"slug": "gpt-5-5", "title": "GPT-5.5"},
                {"slug": "gpt-5-5-pro", "title": "Pro"},
            ],
            "categories": [{"category": "legacy"}],
            "internal_groups": [{"group": "legacy"}],
            "default_model_slug": "gpt-4o",
        }

        filtered = filter_chatgpt_models_payload(payload)

        self.assertEqual(
            [model["slug"] for model in filtered["models"]],
            ["gpt-5-3", "gpt-5-5", "gpt-5-5-pro", "gpt-5-6-thinking"],
        )
        self.assertEqual(
            [model["title"] for model in filtered["models"]],
            ["ChatGPT 5.3", "ChatGPT 5.5", "ChatGPT 5.5 Pro", "ChatGPT 5.6 Thinking"],
        )
        self.assertEqual(
            [category["default_model"] for category in reversed(filtered["categories"])],
            ["gpt-5-3", "gpt-5-5", "gpt-5-5-pro", "gpt-5-6-thinking"],
        )
        self.assertEqual(
            [category["human_category_name"] for category in reversed(filtered["categories"])],
            ["ChatGPT 5.3", "ChatGPT 5.5", "ChatGPT 5.5 Pro", "ChatGPT 5.6 Thinking"],
        )
        self.assertEqual(
            [category["short_explainer"] for category in reversed(filtered["categories"])],
            ["gpt-5-3", "gpt-5-5", "gpt-5-5-pro", "gpt-5-6-thinking"],
        )
        self.assertEqual(filtered["internal_groups"], [])
        self.assertEqual(filtered["default_model_slug"], "gpt-5-5")

    async def test_exact_remote_model_is_cached_for_twelve_hours(self):
        """精确模型通过校验，且同一账号在缓存期内只查询一次。"""
        service = ModelMixin()
        service.req_token = "token"
        service.account_id = "account"
        service.host_url = "https://example.com"
        service.history_disabled = True
        service.base_headers = {}
        service.s = FakeSession()
        service.origin_model = "gpt-5-5-pro"
        service.req_model = "gpt-5-5-pro"
        service.gizmo_id = None
        service.access_token = "token"

        await service.validate_model_access()
        await service.validate_model_access()

        self.assertEqual(service.s.calls, 1)
        self.assertEqual(service.available_model_cache_ttl, 12 * 60 * 60)

    async def test_unknown_model_is_rejected(self):
        """远程列表未精确包含请求模型时返回 model_not_found。"""
        service = ModelMixin()
        service.origin_model = "gpt-missing"
        service.req_model = "gpt-missing"
        service.gizmo_id = None
        service.access_token = "token"

        async def fetch_available_models():
            return {"gpt-5-5-pro"}

        service.fetch_available_models = fetch_available_models
        with self.assertRaises(HTTPException) as context:
            await service.validate_model_access()
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
