import unittest

from chatgpt.services._helpers import _sanitize_fingerprint_headers
from gateway.reverseProxy import _is_public_resource


class FingerprintHeaderTests(unittest.TestCase):
    def test_internal_values_are_removed_and_header_values_are_strings(self):
        headers = _sanitize_fingerprint_headers({
            "user-agent": "Browser",
            "sec-ch-ua": {"brands": ["Chromium"]},
            "screen": {"width": 1920},
            "group": "Group A",
            "proxy_name": "WARP",
            "empty": None,
        })

        self.assertEqual(headers["user-agent"], "Browser")
        self.assertEqual(headers["sec-ch-ua"], '{"brands":["Chromium"]}')
        self.assertNotIn("screen", headers)
        self.assertNotIn("group", headers)
        self.assertNotIn("proxy_name", headers)
        self.assertNotIn("empty", headers)

    def test_public_resources_do_not_receive_account_authorization(self):
        self.assertTrue(_is_public_resource("assets/app.js", "https://cdn.oaistatic.com"))
        self.assertTrue(_is_public_resource("favicon.ico", "https://chatgpt.com"))
        self.assertTrue(_is_public_resource("sw.js", "https://chatgpt.com"))
        self.assertFalse(_is_public_resource("backend-api/models", "https://chatgpt.com"))


if __name__ == "__main__":
    unittest.main()
