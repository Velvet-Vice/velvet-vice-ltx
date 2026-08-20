import json
import unittest
from pathlib import Path

from services.duration_planner import DurationContext
from services.scene_choreography import analyze_scene_state, build_choreography_plan
from services.prompt_pipeline import (
    DEFAULT_MODEL,
    DEFAULT_SERVER_URL,
    FULL_AUTO_DEFAULTS,
    PromptPipeline,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "resources" / "prompt_templates"


def mounted_two_futanari_scene(*, free_top_target: bool = True) -> dict:
    top_penis = "CLEARLY_VISIBLE" if free_top_target else "PARTIAL"
    return {
        "gate": "PASS",
        "participant_count": 2,
        "participants": [
            {
                "participant_id": "A",
                "generation_anatomy_class": "FUTANARI",
                "anatomy_confidence": 96,
                "genital_evidence": {
                    "penis": top_penis,
                    "vulva": "CLEARLY_VISIBLE",
                },
                "limb_registry": {
                    "left_hand": {"state": "VISIBLE_SUPPORT"},
                    "right_hand": {"state": "VISIBLE_FREE"},
                },
                "pose": "mounted above B",
                "occlusion": "NONE",
            },
            {
                "participant_id": "B",
                "generation_anatomy_class": "FUTANARI",
                "anatomy_confidence": 97,
                "genital_evidence": {
                    "penis": "CLEARLY_VISIBLE",
                    "vulva": "CLEARLY_VISIBLE",
                },
                "limb_registry": {
                    "left_hand": {"state": "VISIBLE_SUPPORT"},
                    "right_hand": {"state": "VISIBLE_FREE"},
                },
                "pose": "seated below A",
                "occlusion": "NONE",
            },
        ],
        "position_family": "MOUNTED_OR_RIDER",
        "position_confidence": 95,
        "scene_stability": {
            "support_stability": "HIGH",
            "motion_freedom": "MEDIUM",
            "occlusion_risk": "LOW",
            "identity_risk": "LOW",
        },
        "contact_registry": [
            {
                "contact_id": "primary_contact",
                "source_owner": "B",
                "source_body_part": "PENIS",
                "target_owner_or_object": "A",
                "target_surface": "VULVA",
                "target_opening": "VAGINAL_OPENING",
                "state": "RHYTHMIC",
                "confidence": 96,
            }
        ],
        "primary_action_signature": {
            "action_slot": "PRIMARY",
            "action_class": "PENETRATIVE",
            "active_effector": "B_PELVIS_ACTIVE_ANATOMY",
            "source_owner": "B",
            "target_owner": "A",
            "target_surface": "VULVA",
            "target_opening": "VAGINAL_OPENING",
            "target_opening_owner": "A",
            "contact_phase": "RHYTHMIC_CONTACT",
            "action_confidence": 96,
        },
        "secondary_action_signature": None,
        "concurrency_plan": {"compatible": True},
    }


class SequenceClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.outputs[len(self.calls) - 1]


class PrimaryEngagedAnatomyLockTests(unittest.TestCase):
    def test_primary_penetrative_penis_is_immutable_and_not_manual_target(self):
        state = analyze_scene_state(json.dumps(mounted_two_futanari_scene()))
        self.assertIn("B.PENIS", state.primary_engaged_resources)
        self.assertIn("B.PENIS", state.forbidden_manual_penis_targets)
        self.assertNotIn("B.PENIS", state.free_manual_penis_targets)
        self.assertIn("A.PENIS", state.free_manual_penis_targets)
        lock = state.lock_block()
        self.assertIn("B.PENIS=ENGAGED_PRIMARY", lock)
        self.assertIn("PRIMARY_ENGAGED_ANATOMY: B.PENIS", lock)
        self.assertIn("FREE_MANUAL_PENIS_TARGETS: A.PENIS", lock)
        self.assertIn("FORBIDDEN_MANUAL_PENIS_TARGETS: B.PENIS", lock)

    def test_manual_secondary_requires_separate_clearly_free_target(self):
        duration = DurationContext(12, 288, 24, "workflow_metadata", "DEVELOPED", 4)
        free_scene = analyze_scene_state(json.dumps(mounted_two_futanari_scene()))
        free_plan = build_choreography_plan(duration, free_scene)
        self.assertTrue(free_plan.manual_penis_secondary_allowed)
        self.assertIn("NEW_MANUAL_PENIS_SECONDARY_PERMITTED: YES", free_plan.control_block(duration))

        uncertain_scene = analyze_scene_state(
            json.dumps(mounted_two_futanari_scene(free_top_target=False))
        )
        uncertain_plan = build_choreography_plan(duration, uncertain_scene)
        self.assertFalse(uncertain_plan.manual_penis_secondary_allowed)
        self.assertEqual(uncertain_scene.free_manual_penis_targets, ())
        self.assertIn("NEW_MANUAL_PENIS_SECONDARY_PERMITTED: NO", uncertain_plan.control_block(duration))

    def test_pipeline_injects_engaged_and_free_target_locks_into_later_stages(self):
        analyzer_json = json.dumps(mounted_two_futanari_scene())
        client = SequenceClient(
            [analyzer_json, '{"plan":"ok"}', "draft prompt", "final prompt"]
        )
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
        for call in client.calls[1:]:
            self.assertIn("PRIMARY_ENGAGED_ANATOMY: B.PENIS", call["prompt"])
            self.assertIn("FREE_MANUAL_PENIS_TARGETS: A.PENIS", call["prompt"])
            self.assertIn(
                "NEW_MANUAL_PENIS_SECONDARY_PERMITTED: YES", call["prompt"]
            )
        diagnostics = result.prompt_package["scene_diagnostics"]
        self.assertEqual(diagnostics["primary_engaged_resources"], ["B.PENIS"])
        self.assertEqual(diagnostics["free_manual_penis_targets"], ["A.PENIS"])
        self.assertTrue(
            result.prompt_package["choreography"][
                "new_manual_penis_secondary_allowed"
            ]
        )

    def test_all_prompt_stages_carry_primary_resource_preservation(self):
        analyzer = (TEMPLATES / "adult_scene_analyzer.txt").read_text(encoding="utf-8")
        director = (TEMPLATES / "adult_action_director.txt").read_text(encoding="utf-8")
        writer = (TEMPLATES / "adult_prompt_writer.txt").read_text(encoding="utf-8")
        validator = (TEMPLATES / "adult_continuity_validator.txt").read_text(encoding="utf-8")
        taxonomy = (TEMPLATES / "adult_action_taxonomy.txt").read_text(encoding="utf-8")

        self.assertIn("PRIMARY ENGAGED ANATOMY RESOLUTION", analyzer)
        self.assertIn("genital_resource_registry", analyzer)
        self.assertIn("PENIS RESOURCE STATE MACHINE", taxonomy)
        self.assertIn("PRIMARY ENGAGED ANATOMY PRESERVATION", director)
        self.assertIn("PRIMARY ENGAGED ANATOMY WRITING LOCK", writer)
        self.assertIn("PRIMARY ENGAGED ANATOMY VALIDATION", validator)
        for text in (taxonomy, director, writer, validator):
            self.assertIn("FREE_MANUAL_PENIS_TARGETS", text)
            self.assertIn("ENGAGED_PRIMARY", text)


if __name__ == "__main__":
    unittest.main()
