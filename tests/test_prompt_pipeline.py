import unittest

from services.prompt_pipeline import (
    DEFAULT_MODEL,
    DEFAULT_SERVER_URL,
    ENDING_MODES,
    FULL_AUTO_DEFAULTS,
    LTX_PROMPT_PROFILES,
    SAFE_FALLBACK,
    PromptPipeline,
    canonical_ending_mode,
    canonical_prompt_profile,
    ending_control_block,
    prompt_profile_control_block,
    resolve_prompt_profile,
)
from services.templates import TEMPLATE_VERSION, load_template


class FakeClient:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return f"result-{len(self.calls)}"


def run_pipeline(client, **overrides):
    values = {
        "mode": "MANUAL",
        "encoded_images": [],
        "manual_prompt": "  exact prompt\\n",
        "short_idea": "turn toward the camera",
        "full_auto_settings": FULL_AUTO_DEFAULTS,
        "adult_confirmed": False,
        "model": DEFAULT_MODEL,
        "server_url": DEFAULT_SERVER_URL,
        "memory_profile": "24-32+ GB",
        "ending_mode": "AUTO",
        "ltx_prompt_profile": "LTX 2.3",
    }
    values.update(overrides)
    return PromptPipeline(client).run(**values)


class PromptPipelineTests(unittest.TestCase):
    def test_adult_templates_enforce_reference_anatomy_lock(self):
        analyzer = load_template("adult_scene_analyzer.txt")
        director = load_template("adult_action_director.txt")
        writer = load_template("adult_prompt_writer.txt")
        validator = load_template("adult_continuity_validator.txt")

        self.assertEqual(
            TEMPLATE_VERSION,
            "2026.08-v1.2.4-ltx25",
        )
        self.assertIn("body_proportion_lock", analyzer)
        self.assertIn("body_proportion_lock", director)
        self.assertIn("same apparent volume", writer)
        self.assertIn("same first-frame apparent volume", validator)
        for template in (analyzer, director, writer, validator):
            self.assertIn("base width", template)
            self.assertIn("projection", template)
            self.assertIn("ENDING CONTROL", template)

    def test_lifelike_performance_rules_reach_every_prompt_path(self):
        standard = load_template("standard_vision.txt")
        analyzer = load_template("adult_scene_analyzer.txt")
        director = load_template("adult_action_director.txt")
        writer = load_template("adult_prompt_writer.txt")
        validator = load_template("adult_continuity_validator.txt")
        defaults = load_template("full_auto_defaults.txt")

        self.assertIn("NON-MECHANICAL PERFORMANCE", standard)
        self.assertIn("ACTION-BOUND DIEGETIC AUDIO", standard)
        self.assertIn("IMAGE FIDELITY LOCK", analyzer)
        self.assertIn("This stage is an image reader, not a scene writer", analyzer)
        self.assertNotIn('"performance_baseline"', analyzer)
        self.assertNotIn('"diegetic_audio_sources"', analyzer)
        self.assertNotIn('"anti_mechanical_risks"', analyzer)
        self.assertIn('"performance_arc"', director)
        self.assertIn('"action_bound_audio"', director)
        self.assertIn("LIFELIKE PERFORMANCE WRITING", writer)
        self.assertIn("ACTION-BOUND AUDIO WRITING", writer)
        self.assertIn("LIFELIKE PERFORMANCE VALIDATION", validator)
        self.assertIn("mechanically uniform", validator)
        self.assertIn("PERFORMANCE STYLE: LIFELIKE AND REACTIVE", defaults)
        self.assertIn("SUPPORTING MOTION BUDGET", defaults)
        self.assertIn("VISUAL FIDELITY — NO SUBSTITUTE SCENE", standard)
        self.assertIn("EVIDENCE BOUNDARY — ANIMATE, DO NOT REINTERPRET", director)
        self.assertIn("CONTENT FIDELITY", writer)
        self.assertIn("FINAL IMAGE-FIDELITY CHECK", validator)

    def test_position_intelligence_supports_anatomy_neutral_adult_pairs(self):
        analyzer = load_template("adult_scene_analyzer.txt")
        director = load_template("adult_action_director.txt")
        writer = load_template("adult_prompt_writer.txt")
        validator = load_template("adult_continuity_validator.txt")
        taxonomy = load_template("adult_position_taxonomy.txt")
        defaults = load_template("full_auto_defaults.txt")

        for template in (analyzer, director):
            self.assertIn("POSITION INTELLIGENCE — SHARED GEOMETRY TAXONOMY", template)
            self.assertNotIn("{{ADULT_POSITION_TAXONOMY}}", template)
            self.assertIn("anatomy ownership", template.lower())
        self.assertIn("POSITION-SPECIFIC WRITING", writer)
        self.assertIn("POSITION AND ROLE VALIDATION", validator)
        self.assertIn("anatomy ownership", writer.lower())
        self.assertIn("anatomy ownership", validator.lower())
        self.assertIn('"position_signature"', analyzer)
        self.assertIn('"position_family"', analyzer)
        self.assertIn('"contact_graph"', analyzer)
        self.assertIn('"source_position_signature"', director)
        self.assertIn('"position_transition"', director)
        self.assertIn("CROSSED_OR_SCISSOR", taxonomy)
        self.assertIn("one to four adults", defaults.lower())
        self.assertIn("POSITION RECOGNITION: AUTO-DETECT", defaults)
        self.assertNotIn("ADULT_MAN_AND_WOMAN", analyzer)
        self.assertNotIn("same-sex contact", director)
        self.assertNotIn("ADULT_MAN_AND_WOMAN", director)

    def test_position_output_budgets_are_expanded_without_extra_calls(self):
        client = FakeClient()
        run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
        )
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(client.calls[0]["options"]["num_predict"], 1600)
        self.assertEqual(client.calls[1]["options"]["num_predict"], 1800)

    def test_ending_modes_are_explicit_and_canonical(self):
        self.assertEqual(
            ENDING_MODES,
            (
                "AUTO",
                "NO CLIMAX",
                "CLIMAX",
                "LOOP / CONTINUOUS ACTION",
            ),
        )
        self.assertEqual(canonical_ending_mode("no climax"), "NO_CLIMAX")
        self.assertEqual(
            canonical_ending_mode("loop / continuous action"),
            "LOOP",
        )
        with self.assertRaisesRegex(ValueError, "Unsupported ending mode"):
            canonical_ending_mode("surprise me twice")

    def test_no_climax_control_is_unambiguous(self):
        block = ending_control_block("NO CLIMAX")
        self.assertIn("ENDING_MODE: NO_CLIMAX", block)
        self.assertIn("Do not plan, describe, imply, or preserve", block)
        self.assertIn("cumshot", block)
        self.assertIn("overrides any conflicting ENDING line", block)

    def test_manual_is_exact_and_makes_zero_calls(self):
        client = FakeClient()
        result = run_pipeline(client)
        self.assertEqual(result.final_prompt, "  exact prompt\\n")
        self.assertEqual(client.calls, [])
        self.assertFalse(result.prompt_package["release_required"])
        self.assertEqual(result.prompt_package["ending_mode"], "AUTO")
        self.assertEqual(result.prompt_package["schema_version"], 5)
        self.assertEqual(
            result.prompt_package["ltx_prompt_profile"],
            "LTX 2.3",
        )

    def test_ltx_prompt_profiles_are_explicit_and_canonical(self):
        self.assertEqual(LTX_PROMPT_PROFILES, ("LTX 2.3", "LTX 2.5"))
        self.assertEqual(canonical_prompt_profile("2.3"), "LTX 2.3")
        self.assertEqual(canonical_prompt_profile("ltx2.5"), "LTX 2.5")
        with self.assertRaisesRegex(ValueError, "Unsupported LTX prompt"):
            canonical_prompt_profile("LTX 3")

    def test_missing_profile_is_inferred_from_current_workflow_metadata(self):
        ltx23 = {
            "workflow": {
                "extra": {"velvet_vice_ltx_profile": "2.3"}
            }
        }
        ltx25 = {
            "workflow": {
                "extra": {"velvet_vice_ltx_profile": "2.5"}
            }
        }
        self.assertEqual(
            resolve_prompt_profile(None, extra_pnginfo=ltx23),
            "LTX 2.3",
        )
        self.assertEqual(
            resolve_prompt_profile(None, extra_pnginfo=ltx25),
            "LTX 2.5",
        )

    def test_missing_profile_falls_back_to_runtime_model_markers(self):
        prompt = {
            "loader": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": (
                        "LTX 2.5/gemma4_e2b_it_bf16.safetensors"
                    )
                },
            }
        }
        self.assertEqual(
            resolve_prompt_profile(None, prompt=prompt),
            "LTX 2.5",
        )
        self.assertEqual(resolve_prompt_profile(None, prompt={}), "LTX 2.3")

    def test_explicit_profile_overrides_inferred_metadata(self):
        extra = {
            "workflow": {
                "extra": {"velvet_vice_ltx_profile": "2.5"}
            }
        }
        self.assertEqual(
            resolve_prompt_profile("LTX 2.3", extra_pnginfo=extra),
            "LTX 2.3",
        )

    def test_ltx23_profile_keeps_legacy_prompt_requests_unchanged(self):
        self.assertEqual(prompt_profile_control_block("LTX 2.3"), "")
        client = FakeClient()
        run_pipeline(
            client,
            mode="STANDARD VISION",
            encoded_images=["png"],
            ltx_prompt_profile="LTX 2.3",
        )
        self.assertEqual(
            client.calls[0]["system"],
            load_template("standard_vision.txt"),
        )

    def test_ltx25_standard_vision_uses_first_frame_motion_profile(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="STANDARD VISION",
            encoded_images=["png"],
            ltx_prompt_profile="LTX 2.5",
        )
        system = client.calls[0]["system"]
        self.assertIn("LTX 2.5 PROMPT PROFILE", system)
        self.assertIn("exact first frame", system)
        self.assertIn("describe primarily what changes", system)
        self.assertIn("roughly 4-8 descriptive sentences", system)
        self.assertIn("Gemma prompt enhancer", system)
        self.assertEqual(
            result.prompt_package["ltx_prompt_profile"],
            "LTX 2.5",
        )

    def test_ltx25_profile_reaches_all_four_adult_stages(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
            ltx_prompt_profile="LTX 2.5",
        )
        self.assertEqual(len(client.calls), 4)
        for index, call in enumerate(client.calls):
            self.assertIn("LTX 2.5 PROMPT PROFILE", call["prompt"])
            self.assertIn("one continuous image-to-video take", call["prompt"])
            if index < 2:
                self.assertIn("required JSON", call["prompt"])
        self.assertIn("prompt profile LTX 2.5", result.status)

    def test_standard_vision_makes_one_call(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="STANDARD VISION",
            encoded_images=["png"],
        )
        self.assertEqual(result.final_prompt, "result-1")
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["images"], ["png"])
        self.assertTrue(result.prompt_package["release_required"])

    def test_adult_gate_blocks_without_ollama_or_image(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            adult_confirmed=False,
        )
        self.assertEqual(result.final_prompt, SAFE_FALLBACK)
        self.assertEqual(client.calls, [])

    def test_adult_pipeline_runs_four_stages(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="ADULT ASSISTED",
            encoded_images=["png"],
            adult_confirmed=True,
            memory_profile="16 GB",
        )
        self.assertEqual(result.final_prompt, "result-4")
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(
            [call["options"]["num_ctx"] for call in client.calls],
            [24576, 20480, 10240, 16384],
        )
        self.assertEqual(
            [bool(call["images"]) for call in client.calls],
            [True, True, False, True],
        )
        self.assertEqual(
            [call["keep_alive"] for call in client.calls],
            ["1m", "1m", "1m", 0],
        )

    def test_ending_control_reaches_all_four_adult_stages(self):
        client = FakeClient()
        result = run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
            ending_mode="LOOP / CONTINUOUS ACTION",
        )
        self.assertEqual(result.prompt_package["ending_mode"], "LOOP")
        self.assertIn("ending mode LOOP", result.status)
        self.assertEqual(len(client.calls), 4)
        for call in client.calls:
            self.assertIn(
                "VELVET VICE ENDING CONTROL — HARD OVERRIDE",
                call["prompt"],
            )
            self.assertIn("ENDING_MODE: LOOP", call["prompt"])
            self.assertIn("Do not plan or describe a climax", call["prompt"])

    def test_auto_no_longer_globally_forces_climax(self):
        director = load_template("adult_action_director.txt")
        validator = load_template("adult_continuity_validator.txt")
        self.assertNotIn(
            "Unless ending_mode is NO_CLIMAX or LOOP, include",
            director,
        )
        self.assertIn(
            "climax must not be treated as the default",
            director,
        )
        self.assertIn(
            "do not invent a climax during validation",
            validator,
        )

    def test_manual_penile_stimulation_completion_rule_reaches_all_stages(self):
        expected = (
            "MANUAL PENILE STIMULATION COMPLETION RULE",
            "MANUAL PENILE STIMULATION COMPLETION RULE",
            "MANUAL PENILE STIMULATION COMPLETION RULE",
            "MANUAL PENILE STIMULATION — FINAL COMPLETION GATE",
        )
        templates = (
            load_template("adult_scene_analyzer.txt"),
            load_template("adult_action_director.txt"),
            load_template("adult_prompt_writer.txt"),
            load_template("adult_continuity_validator.txt"),
        )
        for template, marker in zip(templates, expected):
            self.assertIn(marker, template)
            self.assertIn("solo manual stimulation", template)
            self.assertIn("handjob", template)
            self.assertIn("visible ejaculation", template)
            self.assertIn("NO_CLIMAX", template)
            self.assertIn("LOOP", template)

    def test_auto_hard_override_contains_action_specific_completion(self):
        block = ending_control_block("AUTO")
        self.assertIn("ENDING_MODE: AUTO", block)
        self.assertIn("sustained direct manual stimulation", block)
        self.assertIn("exactly one visible ejaculation", block)
        self.assertIn("approach or first contact", block)

    def test_auto_completion_rule_reaches_all_four_adult_requests(self):
        client = FakeClient()
        run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
            ending_mode="AUTO",
        )
        self.assertEqual(len(client.calls), 4)
        for call in client.calls:
            self.assertIn(
                "Special completion rule: when sustained direct manual "
                "stimulation",
                call["prompt"],
            )
            self.assertIn(
                "exactly one visible ejaculation",
                call["prompt"],
            )

    def test_climax_hard_override_requires_ejaculation_for_manual_stimulation(self):
        block = ending_control_block("CLIMAX")
        self.assertIn("stimulated penis", block)
        self.assertIn("required single climax", block)
        self.assertIn("visible ejaculation", block)

    def test_no_climax_and_loop_disable_action_specific_completion(self):
        no_climax = ending_control_block("NO CLIMAX")
        loop = ending_control_block("LOOP / CONTINUOUS ACTION")
        for block in (no_climax, loop):
            self.assertIn(
                "manual-penile-stimulation completion rule is disabled",
                block.lower(),
            )
        self.assertIn("must not produce orgasm", no_climax.lower())
        self.assertIn("without orgasm", loop.lower())

    def test_full_auto_defaults_delegate_ending_to_selector(self):
        self.assertIn(
            "ENDING: CONTROLLED BY THE ENDING MODE SELECTOR",
            FULL_AUTO_DEFAULTS,
        )
        self.assertNotIn("ENDING: AUTO", FULL_AUTO_DEFAULTS)

    def test_low_memory_profile_caps_context_at_10240(self):
        client = FakeClient()
        run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
            memory_profile="8-12 GB",
        )
        self.assertEqual(
            [call["options"]["num_ctx"] for call in client.calls],
            [20480, 16384, 8192, 12288],
        )

    def test_high_memory_profile_expands_stage1_and_stage2_context(self):
        client = FakeClient()
        run_pipeline(
            client,
            mode="ADULT FULL AUTO",
            encoded_images=["png"],
            adult_confirmed=True,
            memory_profile="24-32+ GB",
        )
        self.assertEqual(
            [call["options"]["num_ctx"] for call in client.calls],
            [32768, 32768, 12288, 20480],
        )

    def test_telemetry_wraps_each_adult_stage(self):
        client = FakeClient()
        events = []
        values = {
            "mode": "ADULT FULL AUTO",
            "encoded_images": ["png"],
            "manual_prompt": "",
            "short_idea": "",
            "full_auto_settings": FULL_AUTO_DEFAULTS,
            "adult_confirmed": True,
            "model": DEFAULT_MODEL,
            "server_url": DEFAULT_SERVER_URL,
            "memory_profile": "8-12 GB",
            "ending_mode": "NO CLIMAX",
        }
        PromptPipeline(client, telemetry=events.append).run(**values)
        self.assertEqual(len(events), 8)
        self.assertTrue(events[0].startswith("before stage 1"))
        self.assertTrue(events[-1].startswith("after stage 4"))

    def test_vision_mode_requires_image(self):
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "reference image"):
            run_pipeline(client, mode="STANDARD VISION")


if __name__ == "__main__":
    unittest.main()
