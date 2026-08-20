import json
import unittest
from pathlib import Path


NODE_PACK_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = NODE_PACK_ROOT.parents[1]
WORKFLOW_DIR = PACKAGE_ROOT / "01_WORKFLOW"

def find_variant(suffix):
    matches = sorted(WORKFLOW_DIR.glob(f"*{suffix}*.json"))
    return matches[0] if matches else None

ALPHA_WORKFLOW = find_variant("ANTIGHOST")
ORIGINAL_WORKFLOW = find_variant("STANDARD")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class AntiGhostWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ALPHA_WORKFLOW is None:
            raise unittest.SkipTest("Anti-Ghost workflow is not included in this package variant.")
        cls.workflow = load(ALPHA_WORKFLOW)
        cls.nodes = {
            node["id"]: node for node in cls.workflow["nodes"]
        }
        cls.links = {
            link[0]: link for link in cls.workflow["links"]
        }

    def test_standard_release_has_no_antighost_nodes(self):
        if ORIGINAL_WORKFLOW is None:
            self.assertEqual(list(WORKFLOW_DIR.glob("*STANDARD*.json")), [])
            return
        original = load(ORIGINAL_WORKFLOW)
        self.assertEqual(len(original["nodes"]), 39)
        self.assertEqual(len(original["links"]), 62)
        original_nodes = {node["id"]: node for node in original["nodes"]}
        self.assertEqual(
            original_nodes[4035]["widgets_values"][8],
            "AUTO",
        )
        self.assertNotIn(
            "VelvetViceLTXGhostAnalyzer",
            {node["type"] for node in original["nodes"]},
        )

    def test_alpha_keeps_v103_ending_control(self):
        prompt_director = self.nodes[4035]
        self.assertEqual(len(prompt_director["widgets_values"]), 9)
        self.assertEqual(prompt_director["widgets_values"][8], "AUTO")
        self.assertIn(
            "ENDING MODE",
            prompt_director["widgets_values"][3],
        )

    def test_lifelike_prompter_defaults_are_serialized(self):
        prompt_director = self.nodes[4035]
        full_auto_settings = prompt_director["widgets_values"][3]
        self.assertIn(
            "PERFORMANCE STYLE: LIFELIKE AND REACTIVE",
            full_auto_settings,
        )
        self.assertIn(
            "MOTION TIMING: ORGANIC, NON-METRONOMIC",
            full_auto_settings,
        )
        self.assertIn(
            "SUPPORTING MOTION BUDGET: 1-2 RELEVANT CUES PER BEAT",
            full_auto_settings,
        )

    def test_position_intelligence_defaults_are_serialized(self):
        prompt_director = self.nodes[4035]
        full_auto_settings = prompt_director["widgets_values"][3]
        self.assertIn("POSITION RECOGNITION: AUTO-DETECT", full_auto_settings)
        self.assertIn("ROLE ASSIGNMENT: GEOMETRY-BASED", full_auto_settings)

    def test_mixed_anatomy_lock_defaults_are_serialized(self):
        prompt_director = self.nodes[4035]
        full_auto_settings = prompt_director["widgets_values"][3]
        self.assertIn("FUTANARI ANATOMY LOCK", full_auto_settings)
        self.assertIn("GENITAL REINTERPRETATION: FORBIDDEN", full_auto_settings)
        self.assertIn("two or more futanari participants", full_auto_settings.lower())

    def test_alpha_workflow_contains_registered_nodes(self):
        self.assertEqual(
            self.nodes[4044]["type"],
            "VelvetViceLTXGhostAnalyzer",
        )
        self.assertEqual(
            self.nodes[4045]["type"],
            "VelvetViceLTXTemporalAntiGhost",
        )
        self.assertEqual(len(self.workflow["nodes"]), 42)
        self.assertEqual(len(self.workflow["links"]), 68)
        self.assertEqual(self.nodes[3730]["type"], "VelvetViceControlHub")
        self.assertEqual(self.nodes[3729]["type"], "VelvetVicePreflightConsole")
        self.assertEqual(self.nodes[2196]["type"], "VelvetViceOutputStudio")

    def test_repair_and_mask_preview_are_safe_by_default(self):
        self.assertFalse(self.nodes[4045]["widgets_values"][0])
        self.assertEqual(self.nodes[4046]["mode"], 2)
        self.assertEqual(
            self.nodes[4044]["widgets_values"][:2],
            ["SOURCE 24 FPS", "SAFE"],
        )

    def test_post_smooth_route_passes_through_lazy_repair(self):
        self.assertEqual(
            self.nodes[4041]["outputs"][0]["links"],
            [9064, 9065],
        )
        self.assertEqual(self.links[9064][1:5], [4041, 0, 4044, 0])
        self.assertEqual(self.links[9065][1:5], [4041, 0, 4045, 0])
        self.assertEqual(self.links[9066][1:5], [4044, 0, 4045, 1])

    def test_repair_output_feeds_both_24fps_and_rife_paths(self):
        self.assertEqual(self.links[9059][1:5], [4045, 0, 3747, 0])
        self.assertEqual(self.links[9060][1:5], [4045, 0, 3731, 0])
        self.assertEqual(
            self.nodes[4045]["outputs"][0]["links"],
            [9059, 9060],
        )


if __name__ == "__main__":
    unittest.main()
