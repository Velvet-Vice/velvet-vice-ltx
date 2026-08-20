import json
import unittest
from pathlib import Path

from services.duration_planner import DurationContext
from services.prompt_pipeline import (
    DEFAULT_MODEL,
    DEFAULT_SERVER_URL,
    FULL_AUTO_DEFAULTS,
    PromptPipeline,
)
from services.scene_choreography import analyze_scene_state, build_choreography_plan


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "resources" / "prompt_templates"


def two_futanari_anal_scene() -> dict:
    return {
        "gate": "PASS",
        "participant_count": 2,
        "participants": [
            {
                "participant_id": "A",
                "generation_anatomy_class": "FUTANARI",
                "anatomy_confidence": 98,
                "genital_evidence": {
                    "penis": "CLEARLY_VISIBLE",
                    "penis_existence": "PRESENT_LOCKED",
                    "penis_visibility": "VISIBLE",
                },
                "limb_registry": {
                    "left_hand": {
                        "state": "VISIBLE_SUPPORT",
                        "visibility": "VISIBLE",
                        "finger_visibility": "CLEARLY_VISIBLE",
                        "visible_digit_count": 5,
                        "wrist_forearm_continuity": "CLEAR",
                        "confidence": 92,
                    },
                    "right_hand": {
                        "state": "VISIBLE_FREE",
                        "visibility": "VISIBLE",
                        "finger_visibility": "CLEARLY_VISIBLE",
                        "visible_digit_count": 5,
                        "wrist_forearm_continuity": "CLEAR",
                        "confidence": 92,
                    },
                },
                "pose": "behind and above B",
                "occlusion": "PARTIAL",
            },
            {
                "participant_id": "B",
                "generation_anatomy_class": "FUTANARI",
                "anatomy_confidence": 97,
                "genital_evidence": {
                    "penis": "PARTIAL",
                    "penis_existence": "PRESENT_LOCKED",
                    "penis_visibility": "OCCLUDED",
                },
                "limb_registry": {
                    "left_hand": {
                        "state": "PARTIAL",
                        "visibility": "PARTIAL",
                        "palm_visibility": "PARTIAL",
                        "finger_visibility": "OCCLUDED",
                        "visible_digit_count": None,
                        "wrist_forearm_continuity": "PARTIAL",
                        "confidence": 47,
                    },
                    "right_hand": {
                        "state": "VISIBLE_SUPPORT",
                        "visibility": "VISIBLE",
                        "finger_visibility": "UNCLEAR",
                        "visible_digit_count": None,
                        "wrist_forearm_continuity": "CLEAR",
                        "confidence": 72,
                    },
                },
                "pose": "receiving below A",
                "occlusion": "STRONG",
            },
        ],
        "position_family": "CUSTOM_VISIBLE_GEOMETRY",
        "position_confidence": 88,
        "scene_stability": {
            "support_stability": "HIGH",
            "motion_freedom": "MEDIUM",
            "occlusion_risk": "HIGH",
            "identity_risk": "MEDIUM",
        },
        "contact_registry": [
            {
                "contact_id": "anal_primary",
                "source_owner": "A",
                "source_body_part": "PENIS",
                "target_owner_or_object": "B",
                "target_surface": "ANUS",
                "target_opening": "ANAL_OPENING",
                "state": "RHYTHMIC",
                "confidence": 95,
            }
        ],
        "primary_action_signature": {
            "action_slot": "PRIMARY",
            "action_class": "PENETRATIVE",
            "active_effector": "A_PENIS",
            "source_owner": "A",
            "target_owner": "B",
            "target_surface": "ANUS",
            "target_opening": "ANAL_OPENING",
            "target_opening_owner": "B",
            "contact_phase": "RHYTHMIC_CONTACT",
            "action_confidence": 95,
        },
        "secondary_action_signature": None,
        "concurrency_plan": {"compatible": False},
    }


class SequenceClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.outputs[len(self.calls) - 1]


class OccludedHandPersistentAnatomyTests(unittest.TestCase):
    def test_futanari_receiver_penis_remains_present_when_occluded(self):
        scene = analyze_scene_state(json.dumps(two_futanari_anal_scene()))
        participant_b = next(p for p in scene.participants if p.participant_id == "B")
        self.assertEqual(participant_b.anatomy_class, "FUTANARI")
        self.assertEqual(participant_b.penis_existence, "PRESENT_LOCKED")
        self.assertEqual(participant_b.penis_visibility, "OCCLUDED")
        self.assertEqual(participant_b.penis_resource_state, "PRESENT_LOCKED_OCCLUDED")
        self.assertTrue(any("B.ANATOMY_CLASS=FUTANARI_LOCKED" in x for x in scene.persistent_anatomy_locks))
        self.assertTrue(any("B.PENIS:owner=B;existence=PRESENT_LOCKED" in x for x in scene.persistent_anatomy_locks))
        lock = scene.lock_block()
        self.assertIn("PERSISTENT_ANATOMY_INVENTORY", lock)
        self.assertIn("receiving roles", lock)
        self.assertIn("never removes the receiver's penis", lock)


    def test_user_futanari_label_survives_occluded_pelvis(self):
        data = two_futanari_anal_scene()
        data["participants"][1]["user_label"] = "futanari"
        data["participants"][1]["generation_anatomy_class"] = "WOMAN"
        data["participants"][1]["genital_evidence"]["penis"] = "UNCLEAR"
        scene = analyze_scene_state(json.dumps(data))
        participant_b = next(p for p in scene.participants if p.participant_id == "B")
        self.assertEqual(participant_b.anatomy_class, "FUTANARI")
        self.assertEqual(participant_b.penis_existence, "PRESENT_LOCKED")

    def test_partial_hand_is_not_completed_or_reassigned(self):
        scene = analyze_scene_state(json.dumps(two_futanari_anal_scene()))
        self.assertGreaterEqual(scene.high_risk_hand_count, 1)
        left_lock = next(x for x in scene.hand_reconstruction_locks if x.startswith("B.LEFT_HAND"))
        self.assertIn("reconstruction=PRESERVE_OCCLUSION_NO_COMPLETION", left_lock)
        self.assertIn("visible_digits=UNRESOLVED", left_lock)
        duration = DurationContext(12, 288, 24, "workflow_metadata", "DEVELOPED", 4)
        plan = build_choreography_plan(duration, scene)
        self.assertNotIn("GRIP_ADJUSTMENT", plan.variation_priority)

    def test_clear_five_digit_free_hand_remains_eligible(self):
        scene = analyze_scene_state(json.dumps(two_futanari_anal_scene()))
        right_lock = next(x for x in scene.hand_reconstruction_locks if x.startswith("A.RIGHT_HAND"))
        self.assertIn("reconstruction=FIVE_DIGITS_LOCKED", right_lock)
        self.assertTrue(scene.has_visible_free_hand)

    def test_pipeline_injects_both_lock_families_without_render_changes(self):
        analyzer_json = json.dumps(two_futanari_anal_scene())
        client = SequenceClient([analyzer_json, '{"plan":"ok"}', "draft", "final"])
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
            self.assertIn("PERSISTENT_ANATOMY_INVENTORY", call["prompt"])
            self.assertIn("HAND_RECONSTRUCTION_LOCKS", call["prompt"])
            self.assertIn("B.PENIS:owner=B;existence=PRESENT_LOCKED", call["prompt"])
            self.assertIn("PRESERVE_OCCLUSION_NO_COMPLETION", call["prompt"])
        diagnostics = result.prompt_package["scene_diagnostics"]
        self.assertGreaterEqual(diagnostics["high_risk_hand_count"], 1)
        self.assertTrue(diagnostics["persistent_anatomy_locks"])
        self.assertTrue(diagnostics["hand_reconstruction_locks"])

    def test_all_prompt_stages_contain_new_hard_locks(self):
        analyzer = (TEMPLATES / "adult_scene_analyzer.txt").read_text(encoding="utf-8")
        director = (TEMPLATES / "adult_action_director.txt").read_text(encoding="utf-8")
        writer = (TEMPLATES / "adult_prompt_writer.txt").read_text(encoding="utf-8")
        validator = (TEMPLATES / "adult_continuity_validator.txt").read_text(encoding="utf-8")
        self.assertIn("PERSISTENT ANATOMY INVENTORY", analyzer)
        self.assertIn("PRESERVE_OCCLUSION_NO_COMPLETION", analyzer)
        self.assertIn("PERSISTENT FUTANARI ANATOMY THROUGH RECEIVING ROLES", director)
        self.assertIn("OCCLUDED HAND RESOURCE LOCK", director)
        self.assertIn("PERSISTENT ANATOMY + PRIMARY ENGAGED ANATOMY WRITING LOCK", writer)
        self.assertIn("FINGER-COMPLETION LOCK", writer)
        self.assertIn("existence separately from visibility", validator)
        self.assertIn("six fingers", validator)


if __name__ == "__main__":
    unittest.main()
