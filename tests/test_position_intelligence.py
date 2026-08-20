import unittest

from services.templates import load_template


class PositionIntelligenceTests(unittest.TestCase):
    def test_shared_taxonomy_expands_in_analysis_stages(self):
        for name in (
            "adult_scene_analyzer.txt",
            "adult_action_director.txt",
        ):
            text = load_template(name)
            self.assertIn("POSITION SIGNATURE", text)
            self.assertIn("ROLE AND COMPATIBILITY", text)
            self.assertNotIn("{{ADULT_POSITION_TAXONOMY}}", text)
        self.assertIn(
            "POSITION-SPECIFIC WRITING",
            load_template("adult_prompt_writer.txt"),
        )
        self.assertIn(
            "POSITION AND ROLE VALIDATION",
            load_template("adult_continuity_validator.txt"),
        )

    def test_geometry_families_and_owner_lock_exist(self):
        taxonomy = load_template("adult_position_taxonomy.txt")
        for value in (
            "UPRIGHT_FACE_TO_FACE",
            "ONE_UPRIGHT_ONE_LOWERED",
            "SUPINE_OVER_UNDER",
            "SIDE_LYING_SAME_DIRECTION",
            "CROSSED_OR_SCISSOR",
            "CUSTOM_VISIBLE_GEOMETRY",
        ):
            self.assertIn(value, taxonomy)
        self.assertIn(
            "Never erase, duplicate, transfer or redesign",
            taxonomy,
        )


if __name__ == "__main__":
    unittest.main()
