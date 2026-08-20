import unittest
from services.templates import load_template


class MixedAnatomyLockTests(unittest.TestCase):
    def test_taxonomy_defines_futanari_as_valid_combined_anatomy(self):
        text = load_template("adult_position_taxonomy.txt")
        self.assertIn("MIXED / FUTANARI ANATOMY RESOLUTION", text)
        self.assertIn("feminine face, breasts, wide hips", text)
        self.assertIn("A_PENIS_REMAINS_VISIBLE_AND_ATTACHED_TO_A_PELVIS", text)
        self.assertIn("For two futanari participants", text)

    def test_analyzer_has_separate_genital_evidence_per_participant(self):
        text = load_template("adult_scene_analyzer.txt")
        self.assertIn("generation_anatomy_class", text)
        self.assertIn("genital_evidence", text)
        self.assertIn("USER_LABEL_SUPPORTED_PARTIAL", text)
        self.assertIn("mixed_anatomy_resolution", text)

    def test_all_later_stages_reject_penis_to_vulva_normalization(self):
        director = load_template("adult_action_director.txt")
        writer = load_template("adult_prompt_writer.txt")
        validator = load_template("adult_continuity_validator.txt")
        self.assertIn("MIXED / FUTANARI ANATOMY CROSS-CHECK", director)
        self.assertIn("MIXED / FUTANARI ANATOMY WRITING LOCK", writer)
        self.assertIn("vulva/vagina-only body", validator)
        self.assertIn("two or more confirmed futanari participants", validator.lower())

    def test_full_auto_defaults_expose_hard_lock(self):
        text = load_template("full_auto_defaults.txt")
        self.assertIn("FUTANARI ANATOMY LOCK", text)
        self.assertIn("GENITAL REINTERPRETATION: FORBIDDEN", text)


if __name__ == "__main__":
    unittest.main()
