import importlib.util
import json
import sys
import unittest
from pathlib import Path

from services.duration_planner import (
    DurationContext,
    duration_profile,
    resolve_duration_context,
)
from services.prompt_pipeline import (
    DEFAULT_MODEL,
    DEFAULT_SERVER_URL,
    FULL_AUTO_DEFAULTS,
    PromptPipeline,
)
from services.scene_choreography import (
    analyze_scene_state,
    build_choreography_plan,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parents[1]

def _load_package():
    name = "velvet_vice_ltx_duration_test_package"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

PACKAGE = _load_package()
VelvetViceLTXPromptDirector = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceLTXPromptDirector"]
WORKFLOW_DIR = PACKAGE_ROOT / "01_WORKFLOW"
WORKFLOW = next(iter(sorted(WORKFLOW_DIR.glob("*.json"))))


class SequenceClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.outputs[len(self.calls) - 1]


class DurationScenePlannerTests(unittest.TestCase):
    def test_duration_is_read_from_ltxdirector_workflow_metadata(self):
        workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        context = resolve_duration_context(
            extra_pnginfo={"workflow": workflow},
            full_auto_settings="DURATION: 99 seconds",
        )
        self.assertEqual(context.frames, 192)
        self.assertEqual(context.fps, 24)
        self.assertEqual(context.seconds, 8)
        self.assertEqual(context.source, "workflow_metadata")

    def test_twelve_second_ltx_selection_becomes_developed_profile(self):
        workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        for node in workflow["nodes"]:
            if node.get("type") != "LTXDirector":
                continue
            values = node["widgets_values"]
            payload = json.loads(values[6])
            payload["normalDurationFrames"] = 288
            payload["segments"][0]["length"] = 288
            values[6] = json.dumps(payload)
            values[4] = 288
            values[5] = 288
            values[8] = "288"
        context = resolve_duration_context(
            extra_pnginfo={"workflow": workflow},
            full_auto_settings="DURATION: 8 seconds",
        )
        self.assertEqual(context.seconds, 12)
        self.assertEqual(context.profile, "DEVELOPED")
        self.assertEqual(context.nominal_beats, 4)

    def test_duration_profiles_scale_without_unbounded_beats(self):
        self.assertEqual(duration_profile(5), ("COMPACT", 2))
        self.assertEqual(duration_profile(8), ("STANDARD", 3))
        self.assertEqual(duration_profile(12), ("DEVELOPED", 4))
        self.assertEqual(duration_profile(20), ("EXTENDED", 5))
        self.assertEqual(duration_profile(60), ("LONG_FORM", 8))

    def test_prompt_director_has_hidden_workflow_metadata_inputs(self):
        hidden = VelvetViceLTXPromptDirector.INPUT_TYPES()["hidden"]
        self.assertEqual(hidden["prompt"], "PROMPT")
        self.assertEqual(hidden["extra_pnginfo"], "EXTRA_PNGINFO")
        self.assertEqual(hidden["unique_id"], "UNIQUE_ID")

    def test_scene_state_distinguishes_woman_and_futanari_per_owner(self):
        analyzer = {
            "gate": "PASS",
            "participant_count": 2,
            "participants": [
                {
                    "participant_id": "A",
                    "generation_anatomy_class": "FUTANARI",
                    "anatomy_confidence": 94,
                    "limb_registry": {
                        "left_hand": {"state": "VISIBLE_SUPPORT"},
                        "right_hand": {"state": "VISIBLE_FREE"},
                    },
                    "occlusion": "NONE",
                },
                {
                    "participant_id": "B",
                    "generation_anatomy_class": "WOMAN",
                    "anatomy_confidence": 96,
                    "limb_registry": {
                        "left_hand": {"state": "VISIBLE_CONTACT"},
                        "right_hand": {"state": "PARTIAL"},
                    },
                    "occlusion": "PARTIAL",
                },
            ],
            "position_family": "MOUNTED_OR_RIDER",
            "position_confidence": 88,
            "scene_stability": {
                "support_stability": "HIGH",
                "motion_freedom": "MEDIUM",
                "occlusion_risk": "MEDIUM",
                "identity_risk": "LOW",
            },
            "pairwise_geometry": [{
                "participants": "A-B",
                "facing_relation": "FACE_TO_FACE",
                "vertical_relation": "A_ABOVE_B",
                "depth_relation": "OVERLAPPING",
                "pelvis_relation": "ALIGNED",
                "support_relation": "A_KNEES_B_BACK",
                "confidence": 91
            }],
            "contact_registry": [{
                "contact_id": "c1",
                "source_owner": "A",
                "source_body_part": "PELVIS",
                "target_owner_or_object": "B",
                "target_surface": "VULVA",
                "target_opening": "VAGINAL_OPENING",
                "state": "ESTABLISHED",
                "confidence": 92
            }],
            "primary_action_signature": {
                "action_class": "BODY_CONTACT",
                "target_owner": "B",
                "target_opening_owner": "B",
                "target_opening": "VAGINAL_OPENING"
            },
        }
        state = analyze_scene_state(json.dumps(analyzer))
        self.assertEqual(state.anatomy_summary, "A=FUTANARI(94), B=WOMAN(96)")
        lock = state.lock_block()
        self.assertIn("A: anatomy=FUTANARI", lock)
        self.assertIn("B: anatomy=WOMAN", lock)
        self.assertIn("left_hand=VISIBLE_SUPPORT", lock)
        self.assertIn("A-B[91]", lock)
        self.assertIn("B=VAGINAL_OPENING", lock)
        self.assertIn("c1:A.PELVIS->B.VAGINAL_OPENING", lock)

    def test_complex_multi_participant_scene_reduces_action_budget(self):
        analyzer = {
            "gate": "PASS",
            "participant_count": 4,
            "participants": [
                {
                    "participant_id": participant,
                    "generation_anatomy_class": "UNCLEAR",
                    "anatomy_confidence": 30,
                    "limb_registry": {
                        "left_hand": {"state": "OCCLUDED"},
                        "right_hand": {"state": "OCCLUDED"},
                    },
                    "occlusion": "STRONG",
                }
                for participant in "ABCD"
            ],
            "position_family": "MULTI_PARTICIPANT_CUSTOM_GEOMETRY",
            "position_confidence": 48,
            "scene_stability": {
                "support_stability": "LOW",
                "motion_freedom": "LOW",
                "occlusion_risk": "HIGH",
                "identity_risk": "HIGH",
            },
            "contact_registry": [{}, {}, {}, {}],
            "primary_action_signature": {"action_class": "BODY_CONTACT"},
            "secondary_action_signature": {"action_class": "MANUAL"},
        }
        duration = DurationContext(16, 384, 24, "workflow_metadata", "DEVELOPED", 4)
        scene = analyze_scene_state(json.dumps(analyzer))
        plan = build_choreography_plan(duration, scene)
        self.assertEqual(scene.complexity, "VERY_HIGH")
        self.assertEqual(plan.beat_budget, 2)
        self.assertFalse(plan.secondary_action_allowed)
        self.assertTrue(plan.preserve_existing_secondary)
        self.assertEqual(plan.transition_budget, 0)

    def test_pipeline_injects_duration_and_deterministic_plan(self):
        analyzer = json.dumps(
            {
                "gate": "PASS",
                "participant_count": 2,
                "participants": [
                    {
                        "participant_id": "A",
                        "generation_anatomy_class": "FUTANARI",
                        "anatomy_confidence": 90,
                        "limb_registry": {
                            "left_hand": {"state": "VISIBLE_SUPPORT"},
                            "right_hand": {"state": "VISIBLE_FREE"},
                        },
                        "occlusion": "NONE",
                    },
                    {
                        "participant_id": "B",
                        "generation_anatomy_class": "WOMAN",
                        "anatomy_confidence": 90,
                        "limb_registry": {
                            "left_hand": {"state": "VISIBLE_CONTACT"},
                            "right_hand": {"state": "VISIBLE_FREE"},
                        },
                        "occlusion": "NONE",
                    },
                ],
                "position_family": "MOUNTED_OR_RIDER",
                "position_confidence": 90,
                "scene_stability": {
                    "support_stability": "HIGH",
                    "motion_freedom": "MEDIUM",
                    "occlusion_risk": "LOW",
                    "identity_risk": "LOW",
                },
                "contact_registry": [{"contact_id": "c1"}],
                "primary_action_signature": {"action_class": "BODY_CONTACT"},
            }
        )
        client = SequenceClient([analyzer, '{"plan":"ok"}', "draft prompt", "final prompt"])
        duration = DurationContext(12, 288, 24, "workflow_metadata", "DEVELOPED", 4)
        result = PromptPipeline(client).run(
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            manual_prompt="",
            short_idea="",
            full_auto_settings=FULL_AUTO_DEFAULTS,
            adult_confirmed=True,
            model=DEFAULT_MODEL,
            server_url=DEFAULT_SERVER_URL,
            memory_profile="24-32+ GB",
            ending_mode="NO CLIMAX",
            duration_context=duration,
        )
        self.assertEqual(len(client.calls), 4)
        for call in client.calls:
            self.assertIn("DETECTED_DURATION_SECONDS: 12", call["prompt"])
        for call in client.calls[1:]:
            self.assertIn("VELVET VICE DETERMINISTIC CHOREOGRAPHY BUDGET", call["prompt"])
            self.assertIn("A: anatomy=FUTANARI", call["prompt"])
            self.assertIn("B: anatomy=WOMAN", call["prompt"])
        self.assertEqual(result.prompt_package["duration"]["frames"], 288)
        self.assertEqual(result.prompt_package["scene_diagnostics"]["participant_count"], 2)
        self.assertIn("safe beats", result.status)

    def test_blocked_stage_one_stops_before_later_planning(self):
        client = SequenceClient(['{"gate":"BLOCKED_ADULT_SCENE"}'])
        duration = DurationContext(12, 288, 24, "workflow_metadata", "DEVELOPED", 4)
        result = PromptPipeline(client).run(
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            manual_prompt="",
            short_idea="",
            full_auto_settings=FULL_AUTO_DEFAULTS,
            adult_confirmed=True,
            model=DEFAULT_MODEL,
            server_url=DEFAULT_SERVER_URL,
            memory_profile="24-32+ GB",
            ending_mode="AUTO",
            duration_context=duration,
        )
        self.assertEqual(len(client.calls), 1)
        self.assertIn("BLOCKED", result.status)


if __name__ == "__main__":
    unittest.main()
