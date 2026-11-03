import os
import tempfile
import shutil
import unittest
from hermes_model_roles.drift import scan


class TestModelRolesDrift(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _write(self, name, text):
        path = os.path.join(self.temp_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_scan_detects_hardcoded_model(self):
        self._write("SKILL.md", "Run hermes chat --model claude-opus-5-5 for evaluation.\n")
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertTrue(any("claude-opus-5-5" in tok for _, _, tok in offenders))

    def test_scan_ignores_drift_ok_annotation(self):
        self._write(
            "SKILL.md",
            "Historical note <!-- drift-ok: benchmark record -->: gpt-5.6-luna was tested.\n",
        )
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertEqual(len(offenders), 0)

    def test_scan_invalid_root_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            scan("/path/that/does/not/exist", allow=[], use_allow=True)
        self.assertEqual(ctx.exception.code, 2)

    def test_scan_ignores_python_dash_m_modules(self):
        self._write(
            "SKILL.md",
            "python3 -m json.tool file.json\npython3 -m pytest -q\npython -m venv .venv\npython3 -m pip install x\npython3 -m debugpy --listen 5678\n",
        )
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertEqual(len(offenders), 0)

    def test_scan_flags_dash_m_real_model_ids(self):
        self._write(
            "SKILL.md",
            "opencode run -m commandcode/deepseek/deepseek-v4.1-flash-fast 'hi'\nhermes -m gpt-6-luna 'hi'\n",
        )
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertGreaterEqual(len(offenders), 2)

    def test_scan_flags_bare_family_names(self):
        self._write("SKILL.md", "Will GPT-5 do this for free?\n")
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertTrue(any("GPT-5" in tok for _, _, tok in offenders))

    def test_scan_flags_config_set_model(self):
        self._write("SKILL.md", "hermes config set model.default somemodel\n")
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertTrue(offenders)

    def test_scan_ignores_git_commit_dash_m(self):
        self._write("SKILL.md", 'git commit -m "feat: add specific feature"\n')
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(len(offenders), 0)

    def test_scan_ignores_placeholder_ids(self):
        self._write(
            "SKILL.md",
            "run opus opencode run -m opencode/<id-opus> \"$(cat p)\" &\n"
            "devin -p --model <id-devin>\n"
            "hermes config set model.default <bare>\n",
        )
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertEqual(len(offenders), 0)


if __name__ == "__main__":
    unittest.main()
