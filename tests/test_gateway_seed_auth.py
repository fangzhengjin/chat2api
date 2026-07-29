import os
import tempfile
import unittest

from fastapi import HTTPException

import utils.globals as globals
from chatgpt.authorization import GATEWAY_COOKIE_NAME, generate_gateway_seed, resolve_gateway_seed


class _Request:
    def __init__(self, seed=""):
        self.cookies = {GATEWAY_COOKIE_NAME: seed} if seed else {}


class GatewaySeedAuthTests(unittest.TestCase):
    def setUp(self):
        self.original_seed_map = globals.seed_map
        self.original_token_list = globals.token_list
        self.original_seed_file = globals.SEED_MAP_FILE
        self.temp_dir = tempfile.TemporaryDirectory()
        globals.seed_map = {}
        globals.token_list = ["rt.1.test-account"]
        globals.SEED_MAP_FILE = os.path.join(self.temp_dir.name, "seed_map.json")

    def tearDown(self):
        globals.seed_map = self.original_seed_map
        globals.token_list = self.original_token_list
        globals.SEED_MAP_FILE = self.original_seed_file
        self.temp_dir.cleanup()

    def test_generated_seed_is_required_and_rotation_invalidates_old_seed(self):
        first = generate_gateway_seed("rt.1.test-account")
        seed_key = resolve_gateway_seed(_Request(first))
        self.assertNotIn(first, globals.seed_map)
        globals.seed_map[seed_key]["conversations"] = ["conversation-1"]

        second = generate_gateway_seed("rt.1.test-account")
        second_key = resolve_gateway_seed(_Request(second))
        self.assertEqual(globals.seed_map[second_key]["conversations"], ["conversation-1"])
        with self.assertRaises(HTTPException):
            resolve_gateway_seed(_Request(first))
        with self.assertRaises(HTTPException):
            resolve_gateway_seed(_Request("user-defined-seed"))


if __name__ == "__main__":
    unittest.main()
