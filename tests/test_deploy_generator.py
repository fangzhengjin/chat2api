import importlib.util
import unittest
from pathlib import Path


GENERATOR_PATH = Path(__file__).parents[1] / "deploy" / "multi" / "generate.py"
SPEC = importlib.util.spec_from_file_location("deploy_multi_generate", GENERATOR_PATH)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class DeployGeneratorTests(unittest.TestCase):
    """验证多实例部署配置中的公共路由。"""

    def test_cdn_prefix_is_forwarded_without_credentials(self):
        """CDN 路径剥离 /cdn/ 前缀，并且不转发账号凭据。"""
        nginx = GENERATOR.render_nginx([])
        self.assertIn("location /cdn/ {", nginx)
        self.assertIn("proxy_pass https://cdn.oaistatic.com/;", nginx)
        self.assertIn('proxy_set_header Authorization "";', nginx)
        self.assertIn('proxy_set_header Cookie "";', nginx)


if __name__ == "__main__":
    unittest.main()
