import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "resources" / "prompt_templates"

class ConcurrentActionGraphTests(unittest.TestCase):
    def test_shared_taxonomy_defines_two_slot_graph(self):
        text = (TEMPLATES / "adult_action_taxonomy.txt").read_text(encoding="utf-8")
        self.assertIn("CONCURRENT ACTION GRAPH", text)
        self.assertIn("PRIMARY_PLUS_SECONDARY", text)
        self.assertIn("resource_lock", text)
        self.assertIn("Never add more than two concurrent action signatures", text)

    def test_analyzer_emits_primary_secondary_and_plan(self):
        text = (TEMPLATES / "adult_scene_analyzer.txt").read_text(encoding="utf-8")
        self.assertIn("primary_action_signature", text)
        self.assertIn("secondary_action_signature", text)
        self.assertIn("concurrency_plan", text)
        self.assertIn("genuinely free hand", text)

    def test_director_schedules_secondary_after_primary(self):
        text = (TEMPLATES / "adult_action_director.txt").read_text(encoding="utf-8")
        self.assertIn("CONCURRENT ACTION PLANNING", text)
        self.assertIn("after the primary action has stabilized", text)
        self.assertIn("phase offset", text)

    def test_writer_and_validator_preserve_resource_locks(self):
        writer = (TEMPLATES / "adult_prompt_writer.txt").read_text(encoding="utf-8")
        validator = (TEMPLATES / "adult_continuity_validator.txt").read_text(encoding="utf-8")
        self.assertIn("CONCURRENT ACTION WRITING", writer)
        self.assertIn("CONCURRENT ACTION VALIDATION", validator)
        self.assertIn("Never add a third action", writer)
        self.assertIn("remove only the secondary", validator)

if __name__ == "__main__":
    unittest.main()
