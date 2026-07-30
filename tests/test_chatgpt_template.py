import unittest
from pathlib import Path


class ChatgptTemplateTests(unittest.TestCase):
    def test_random_uuid_polyfill_loads_before_official_modules(self):
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        polyfill = template.index("if (!crypto.randomUUID)")
        first_module = template.index('type="module"')
        self.assertLess(polyfill, first_module)
        self.assertIn("crypto.getRandomValues", template[polyfill:first_module])

    def test_dynamic_interface_cleanup_loads_before_official_modules(self):
        """动态清理必须先于官方模块运行，并覆盖要求移除的入口。"""
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        cleanup = template.index("const modelNames")
        first_module = template.index('type="module"')
        self.assertLess(cleanup, first_module)
        for marker in (
            "MutationObserver", "Explore GPTs", "New project", "Logout",
            "Customize ChatGPT", "Share", "Use a tool", "Voice mode", "cleanSidebar",
            "chat2api.defaultModel", "chat2api-model-pin", "设为默认", "cleanModelPicker",
        ):
            self.assertIn(marker, template[cleanup:first_module])
        self.assertNotIn('data-testid="send-button"', template[cleanup:first_module])

    def test_default_model_survives_local_storage_cleanup(self):
        """页面初始化清理本地状态时必须保留用户选择的默认模型。"""
        gateway = Path("gateway/chatgpt.py").read_text(encoding="utf-8")
        self.assertEqual(gateway.count('localStorage.getItem("chat2api.defaultModel")'), 1)
        self.assertEqual(gateway.count('localStorage.setItem("chat2api.defaultModel"'), 1)


if __name__ == "__main__":
    unittest.main()
