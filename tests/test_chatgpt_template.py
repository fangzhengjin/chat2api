import unittest
from pathlib import Path


class ChatgptTemplateTests(unittest.TestCase):
    def test_random_uuid_polyfill_loads_before_official_modules(self):
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        polyfill = template.index("if (!crypto.randomUUID)")
        first_module = template.index('type="module"')
        self.assertLess(polyfill, first_module)
        self.assertIn("crypto.getRandomValues", template[polyfill:first_module])

    def test_sidebar_shortcuts_and_projects_are_hidden(self):
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        sidebar_styles = template[template.index("<style>"):template.index("</style>")]
        for selector in ('a[title="ChatGPT"]', 'a[title="Sora"]', 'explore-gpts-button', 'snorlax-heading'):
            self.assertIn(selector, sidebar_styles)

    def test_share_and_non_logout_account_actions_are_hidden(self):
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        styles = template[template.index("<style>"):template.index("</style>")]
        self.assertIn('data-testid="share-chat-button"', styles)
        self.assertIn('data-testid="logout-button"', styles)
        self.assertIn('[role="menuitem"]:not(', styles)

    def test_more_tools_and_voice_mode_are_hidden(self):
        template = Path("templates/chatgpt.html").read_text(encoding="utf-8")
        styles = template[template.index("<style>"):template.index("</style>")]
        self.assertIn("--vt-composer-system-hint-action", styles)
        self.assertIn('data-testid="composer-speech-button"', styles)
        self.assertNotIn('data-testid="send-button"', styles)


if __name__ == "__main__":
    unittest.main()
