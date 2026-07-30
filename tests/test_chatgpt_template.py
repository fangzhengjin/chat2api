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
        cleanup = template.index("const cleanInterface")
        first_module = template.index('type="module"')
        self.assertLess(cleanup, first_module)
        for marker in (
            "MutationObserver", "Explore GPTs", "New project", "Logout",
            "Customize ChatGPT", "Share", "Use a tool", "Voice mode",
        ):
            self.assertIn(marker, template[cleanup:first_module])
        self.assertNotIn('data-testid="send-button"', template[cleanup:first_module])


if __name__ == "__main__":
    unittest.main()
