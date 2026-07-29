import os
import tempfile
import unittest

from fastapi import HTTPException

import utils.globals as globals
from chatgpt.authorization import (
    GATEWAY_COOKIE_NAME,
    delete_gateway_seed,
    generate_gateway_seed,
    list_gateway_seeds,
    reset_gateway_seed,
    resolve_gateway_seed,
)


class _Request:
    def __init__(self, seed=""):
        self.cookies = {GATEWAY_COOKIE_NAME: seed} if seed else {}


class GatewaySeedAuthTests(unittest.TestCase):
    def setUp(self):
        self.original_seed_map = globals.seed_map
        self.original_conversation_map = globals.conversation_map
        self.original_token_list = globals.token_list
        self.original_seed_file = globals.SEED_MAP_FILE
        self.original_conversation_file = globals.CONVERSATION_MAP_FILE
        self.temp_dir = tempfile.TemporaryDirectory()
        globals.seed_map = {}
        globals.conversation_map = {}
        globals.token_list = ["rt.1.test-account"]
        globals.SEED_MAP_FILE = os.path.join(self.temp_dir.name, "seed_map.json")
        globals.CONVERSATION_MAP_FILE = os.path.join(self.temp_dir.name, "conversation_map.json")

    def tearDown(self):
        globals.seed_map = self.original_seed_map
        globals.conversation_map = self.original_conversation_map
        globals.token_list = self.original_token_list
        globals.SEED_MAP_FILE = self.original_seed_file
        globals.CONVERSATION_MAP_FILE = self.original_conversation_file
        self.temp_dir.cleanup()

    def test_multiple_seeds_are_isolated_and_reset_preserves_metadata(self):
        first = generate_gateway_seed("rt.1.test-account", note="张三")
        second = generate_gateway_seed("rt.1.test-account", note="李四")
        first_key = resolve_gateway_seed(_Request(first))
        second_key = resolve_gateway_seed(_Request(second))
        self.assertNotIn(first, globals.seed_map)
        globals.seed_map[first_key]["conversations"] = ["conversation-1"]
        globals.seed_map[second_key]["conversations"] = ["conversation-2"]
        globals.conversation_map = {
            "conversation-1": {"id": "conversation-1"},
            "conversation-2": {"id": "conversation-2"},
        }
        first_metadata = globals.seed_map[first_key].copy()
        self.assertNotEqual(first_key, second_key)
        self.assertEqual({item["note"] for item in list_gateway_seeds("rt.1.test-account")}, {"张三", "李四"})

        replacement = reset_gateway_seed(first_key)
        replacement_key = resolve_gateway_seed(_Request(replacement))
        self.assertEqual(globals.seed_map[replacement_key], first_metadata)
        self.assertEqual(resolve_gateway_seed(_Request(second)), second_key)
        with self.assertRaises(HTTPException):
            resolve_gateway_seed(_Request(first))

        delete_gateway_seed(replacement_key)
        with self.assertRaises(HTTPException):
            resolve_gateway_seed(_Request(replacement))
        self.assertNotIn("conversation-1", globals.conversation_map)
        self.assertIn("conversation-2", globals.conversation_map)
        self.assertEqual(resolve_gateway_seed(_Request(second)), second_key)
        with self.assertRaises(HTTPException):
            resolve_gateway_seed(_Request("user-defined-seed"))
        with self.assertRaises(HTTPException) as error:
            generate_gateway_seed("rt.1.test-account", note="x" * 201)
        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
