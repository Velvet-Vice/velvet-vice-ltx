import json
import unittest
from pathlib import Path

NODE_PACK_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = NODE_PACK_ROOT.parents[1]
WORKFLOW_DIR = PACKAGE_ROOT / "01_WORKFLOW"
WORKFLOW = next(WORKFLOW_DIR.glob("*.json"))


def load():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


class QualityPathV124Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = load()
        cls.nodes = {n["id"]: n for n in cls.workflow["nodes"]}
        cls.subgraphs = {
            s["name"]: s for s in cls.workflow["definitions"]["subgraphs"]
        }

    def test_native_fp16_path_stays_at_native_scale(self):
        self.assertEqual(self.nodes[4000]["widgets_values"], ["bicubic", 1.0, 4])
        self.assertEqual(self.nodes[4030]["widgets_values"], ["area", 1.0, 4])

    def test_accepted_quality_stage_two_is_unchanged(self):
        nodes = {n["id"]: n for n in self.subgraphs["Rendering"]["nodes"]}
        self.assertEqual(nodes[3635]["widgets_values"], ["linear_quadratic", 4, 0.4])
        self.assertEqual(nodes[3649]["type"], "SamplerCustomAdvanced")

    def test_stage_one_cfg_is_unchanged(self):
        nodes = {n["id"]: n for n in self.subgraphs["Rendering"]["nodes"]}
        self.assertEqual(nodes[3640]["widgets_values"], [1])

    def test_full_negative_prompt_is_unchanged(self):
        self.assertEqual(
            self.nodes[3523]["widgets_values"][0],
            "morphing, identity drift, anatomy errors, duplicate limbs, flicker, abrupt motion, background instability, blurry details, coarse grain, temporal noise, texture crawling, shimmering distant details, oversharpened edges, compression artifacts",
        )

    def test_simple_prescale_branch_stays_disabled(self):
        nodes = {n["id"]: n for n in self.subgraphs["Post Processing"]["nodes"]}
        self.assertFalse(nodes[3381]["widgets_values"][0])
        self.assertEqual(nodes[3708]["mode"], 4)
        self.assertEqual(nodes[3708]["widgets_values"][4], 2)

    def test_optional_rtx_vsr_stays_x2_and_bypassed(self):
        nodes = {n["id"]: n for n in self.subgraphs["Post Processing"]["nodes"]}
        values = nodes[3405]["widgets_values"]
        self.assertEqual(
            values[:8],
            [True, "Ultra", True, "Ultra", "VSR", "Ultra", "Scale", 2],
        )
        self.assertEqual(values[11], "32")
        self.assertFalse(nodes[3406]["widgets_values"][0])

    def test_optional_ic_lora_uses_safe_default(self):
        studio = self.nodes[4050]
        self.assertEqual(studio["type"], "VelvetVicePowerLoraAV")
        stack = json.loads(studio["widgets_values"][0])
        detailer = next(item for item in stack if item["id"] == "detailer")
        self.assertFalse(detailer["enabled"])
        self.assertEqual(detailer["lora"], "ltx-2-19b-ic-lora-detailer.safetensors")
        self.assertAlmostEqual(detailer["video_strength"], 0.28)
        self.assertAlmostEqual(detailer["audio_strength"], 0.28)


if __name__ == "__main__":
    unittest.main()
