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

    def test_scan_detects_hardcoded_model(self):
        skill_file = os.path.join(self.temp_dir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write("Run hermes chat --model claude-opus-5-5 for evaluation.\n")
        
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertTrue(len(offenders) >= 1)
        self.assertTrue(any("claude-opus-5-5" in tok for _, _, tok in offenders))

    def test_scan_ignores_drift_ok_annotation(self):
        skill_file = os.path.join(self.temp_dir, "SKILL.md")
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write("Historical note <!-- drift-ok: benchmark record -->: gpt-5.6-luna was tested.\n")
        
        offenders, scanned = scan(self.temp_dir, allow=[], use_allow=True)
        self.assertEqual(scanned, 1)
        self.assertEqual(len(offenders), 0)

    def test_scan_invalid_root_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            scan("/path/that/does/not/exist", allow=[], use_allow=True)
        self.assertEqual(ctx.exception.code, 2)

if __name__ == "__main__":
    unittest.main()
