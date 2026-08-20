import unittest
from services.templates import TEMPLATE_VERSION, load_template

class ActionIntelligenceTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(TEMPLATE_VERSION, "2026.08-v1.2.4-ltx25")

    def test_shared_taxonomy_expands(self):
        for name in ["adult_scene_analyzer.txt", "adult_action_director.txt", "adult_prompt_writer.txt", "adult_continuity_validator.txt"]:
            text = load_template(name)
            self.assertIn("ACTION INTELLIGENCE — SHARED ACTION / POSITION SEPARATION", text)
            self.assertNotIn("{{ADULT_ACTION_TAXONOMY}}", text)

    def test_classes_and_position_independence(self):
        text = load_template("adult_action_taxonomy.txt")
        for token in ["MANUAL", "ORAL", "PENETRATIVE", "active_effector", "target_surface", "RIDER_ABOVE_FACE_TO_FACE"]:
            self.assertIn(token, text)
        self.assertIn("A position variant never overrides", text)

    def test_analyzer_schema(self):
        text = load_template("adult_scene_analyzer.txt")
        self.assertIn('"primary_action_signature"', text)
        self.assertIn('"secondary_action_signature"', text)
        self.assertIn('"concurrency_plan"', text)
        self.assertIn('"position_variant"', text)
        self.assertIn('"requested_action_label"', text)

    def test_director_preserves_action_class(self):
        text = load_template("adult_action_director.txt")
        self.assertIn("ACTION SIGNATURE PRESERVATION", text)
        self.assertIn("Never switch action class mid-clip", text)

    def test_validator_rejects_class_drift(self):
        text = load_template("adult_continuity_validator.txt")
        self.assertIn("ACTION CLASS REGRESSION CHECK", text)
        self.assertIn("Reject MANUAL-to-ORAL", text)

if __name__ == '__main__':
    unittest.main()
