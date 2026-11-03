import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from hermes_model_roles.core import resolve_role, validate_roles_file
from hermes_model_roles.targets import apply_target, check_target


def write_roles(path, roles):
    Path(path).write_text(json.dumps({"version": 3, "roles": roles}), encoding="utf-8")
    return path


class ResolveRoleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = write_roles(self.tmp + "/model-roles.json", {
            "main": {"provider": "commandcode", "model": "deepseek/deepseek-v4.1-flash-fast"},
            "worker": {"provider": "commandcode", "model": "deepseek/deepseek-v4.1-flash-fast"},
            "vision": {"provider": "commandcode", "model": "deepseek/deepseek-v4-flash-vision-exp"},
            "cheap": [{"provider": "nous", "model": "upstage/solar-pro4:free"}],
        })

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_resolve_role_returns_provider_and_model(self):
        self.assertEqual(
            resolve_role(self.path, "main"),
            ("commandcode", "deepseek/deepseek-v4.1-flash-fast"),
        )

    def test_resolve_role_list_returns_first(self):
        self.assertEqual(resolve_role(self.path, "cheap"), ("nous", "upstage/solar-pro4:free"))

    def test_unknown_role_exits(self):
        with self.assertRaises(SystemExit):
            resolve_role(self.path, "nope")

    def test_validate_accepts_v3(self):
        errors = validate_roles_file(self.path)
        self.assertEqual(errors, [])

    def test_validate_rejects_missing_worker(self):
        p = write_roles(self.tmp + "/bad.json", {"main": {"provider": "x", "model": "y"}})
        errors = validate_roles_file(p)
        self.assertTrue(any("worker" in e for e in errors))

    def test_validate_rejects_endpoint_without_model(self):
        p = write_roles(self.tmp + "/bad.json", {
            "main": {"provider": "x"},
            "worker": {"provider": "x", "model": "y"},
            "vision": {"provider": "x", "model": "y"},
        })
        errors = validate_roles_file(p)
        self.assertTrue(any("main" in e for e in errors))


class ClaudeTargetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.roles = write_roles(self.tmp + "/model-roles.json", {
            "main": {"provider": "anthropic", "model": "claude-opus-5-5"},
            "worker": {"provider": "anthropic", "model": "claude-opus-5-5"},
            "vision": {"provider": "anthropic", "model": "claude-opus-5-5"},
        })
        self.settings = self.tmp + "/settings.json"
        with open(self.settings, "w") as f:
            json.dump({"model": "old-model"}, f)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_apply_claude_writes_model_and_backs_up(self):
        apply_target("claude", roles_path=self.roles, target_path=self.settings)
        out = json.load(open(self.settings))
        self.assertEqual(out["model"], "claude-opus-5-5")
        backups = [f for f in os.listdir(self.tmp) if f.startswith("settings.json.bak-roles-")]
        self.assertEqual(len(backups), 1)

    def test_check_claude_in_sync(self):
        apply_target("claude", roles_path=self.roles, target_path=self.settings)
        self.assertEqual(check_target("claude", roles_path=self.roles, target_path=self.settings), [])

    def test_check_claude_drift(self):
        with open(self.settings, "w") as f:
            json.dump({"model": "something-else"}, f)
        drift = check_target("claude", roles_path=self.roles, target_path=self.settings)
        self.assertTrue(any("claude-opus-5-5" in d for d in drift))

    def test_apply_refuses_missing_target(self):
        with self.assertRaises(SystemExit):
            apply_target("claude", roles_path=self.roles, target_path=self.tmp + "/nope.json")


class OpencodeTargetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.roles = write_roles(self.tmp + "/model-roles.json", {
            "main": {"provider": "openrouter", "model": "deepseek/deepseek-v4.1-flash-fast"},
            "worker": {"provider": "openrouter", "model": "deepseek/deepseek-v4.1-flash-fast"},
            "vision": {"provider": "openrouter", "model": "qwen/qwen3-vl"},
        })
        self.cfg = self.tmp + "/opencode.json"
        with open(self.cfg, "w") as f:
            json.dump({"provider": {"openrouter": {"model": "old"}}}, f)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_apply_opencode_writes_main_model(self):
        apply_target("opencode", roles_path=self.roles, target_path=self.cfg)
        out = json.load(open(self.cfg))
        self.assertEqual(out["provider"]["openrouter"]["model"], "deepseek/deepseek-v4.1-flash-fast")


if __name__ == "__main__":
    unittest.main()
