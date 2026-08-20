import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "resources" / "prompt_templates"


class HandPathTargetOpeningTests(unittest.TestCase):
    def read(self, name):
        return (TPL / name).read_text(encoding="utf-8")

    def test_taxonomy_separates_vaginal_and_anal_openings(self):
        text = self.read("adult_action_taxonomy.txt")
        self.assertIn("VAGINAL_OPENING", text)
        self.assertIn("ANAL_OPENING", text)
        self.assertIn("target_opening_lock", text)
        self.assertIn("External vulva or anus contact is not penetration", text)

    def test_analyzer_records_hand_anchors_and_opening_confidence(self):
        text = self.read("adult_scene_analyzer.txt")
        self.assertIn('"hand_anchors"', text)
        self.assertIn('"target_opening_confidence"', text)
        self.assertIn("Do not default to vaginal or anal", text)

    def test_director_requires_continuous_hand_route(self):
        text = self.read("adult_action_director.txt")
        self.assertIn("CONTINUOUS HAND AND ARM TRANSITION — NO POP-IN", text)
        self.assertIn('"supportive_limb_transitions"', text)
        self.assertIn("Never write only the destination state", text)

    def test_writer_and_validator_reject_hand_pop_in_and_opening_drift(self):
        writer = self.read("adult_prompt_writer.txt")
        validator = self.read("adult_continuity_validator.txt")
        self.assertIn("HAND/ARM PATH CONTINUITY", writer)
        self.assertIn("Never allow a hand to pop into frame", writer)
        self.assertIn("HAND AND ARM TRANSITION VALIDATION", validator)
        self.assertIn("vaginal-to-anal", validator.lower())


if __name__ == "__main__":
    unittest.main()
