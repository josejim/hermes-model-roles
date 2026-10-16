import json
import os
import shutil
import tempfile
import unittest
import yaml

from hermes_model_roles.core import desired_map, load_roles

class TestModelRolesCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        roles_data = {
            "version": 2,
            "roles": {
                "main": {"provider": "testprov", "model": "test-main-model"},
                "main_fallbacks": [{"provider": "nous", "model": "free-1"}],
                "worker": {"provider": "testprov", "model": "test-worker-model"},
                "worker_fallbacks": [{"provider": "nous", "model": "free-2"}],
                "vision": {"provider": "testprov", "model": "test-vision-model"},
            }
        }
        roles_path = os.path.join(self.temp_dir, "model-roles.json")
        with open(roles_path, "w", encoding="utf-8") as f:
            json.dump(roles_data, f)

        cfg_data = {
            "model": {"default": "old-model", "provider": "old-prov"},
            "auxiliary": {"compression": {}, "review": {}},
        }
        cfg_path = os.path.join(self.temp_dir, "config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg_data, f)

        os.environ["HERMES_HOME"] = self.temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if "HERMES_HOME" in os.environ:
            del os.environ["HERMES_HOME"]

    def test_load_roles(self):
        roles = load_roles()
        self.assertEqual(roles["main"]["model"], "test-main-model")
        self.assertEqual(roles["worker"]["model"], "test-worker-model")
        self.assertEqual(len(roles["worker_fallbacks"]), 1)

    def test_desired_map_structure(self):
        roles = load_roles()
        mapping = desired_map(roles)
        self.assertEqual(mapping["model.default"], "test-main-model")
        self.assertEqual(mapping["delegation.model"], "test-worker-model")
        self.assertEqual(mapping["auxiliary.compression.model"], "test-main-model")
        self.assertEqual(mapping["auxiliary.vision.model"], "test-vision-model")

if __name__ == "__main__":
    unittest.main()
