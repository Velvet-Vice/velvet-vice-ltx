import importlib.util
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_root_package():
    name = "velvet_vice_ltx_test_package"
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PACKAGE = load_root_package()
Barrier = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceOllamaReleaseBarrier"
]
Gate = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceLTXLazyModelGate"]
SystemCheck = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXSystemCheck"
]
FinalCleanup = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXFinalMemoryCleanup"
]
SingleOutputCleanup = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXSingleOutputCleanup"
]
PreDecodeGate = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXPreDecodeMemoryGate"
]
ImageCheckpoint = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXImageMemoryCheckpoint"
]
AudioCheckpoint = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXAudioMemoryCheckpoint"
]
ChunkedScale = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXChunkedImageScaleBy"
]
FP16ChunkedScale = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXFP16ChunkedImageScaleBy"
]
FP16VAEDecode = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXFP16VAEDecode"
]
VersionedVideoOutput = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXAutoVideoCombineV019"
]
FastVersionedVideoOutput = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXAutoVideoCombineV0110"
]
StableVersionedVideoOutput = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXAutoVideoCombineV0112"
]
FinalPromptPreview = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXFinalPromptPreview"
]
PromptDirector = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXPromptDirector"
]


class ReleaseBarrierTests(unittest.TestCase):
    def test_prompt_profile_is_optional_for_workflow_compatibility(self):
        required = list(PromptDirector.INPUT_TYPES()["required"])
        self.assertEqual(
            required,
            [
                "mode",
                "manual_prompt",
                "short_idea",
                "full_auto_settings",
                "adult_confirmed",
                "ollama_model",
                "ollama_url",
                "ollama_context_profile",
                "ending_mode",
            ],
        )
        self.assertEqual(
            PromptDirector.INPUT_TYPES()["required"]["ending_mode"][1][
                "default"
            ],
            "AUTO",
        )
        self.assertEqual(
            PromptDirector.INPUT_TYPES()["optional"]
            ["ltx_prompt_profile"][0],
            ("LTX 2.3", "LTX 2.5"),
        )
        self.assertEqual(
            PromptDirector.INPUT_TYPES()["optional"]
            ["ltx_prompt_profile"][1]["default"],
            "LTX 2.3",
        )
        self.assertNotIn("ltx_prompt_profile", required)

    def test_prompt_frontend_labels_hard_ending_override(self):
        script = (
            ROOT / "web" / "prompt_director.js"
        ).read_text(encoding="utf-8")
        self.assertIn("ENDING MODE — HARD OVERRIDE", script)
        self.assertIn("EDITABLE FULL AUTO DEFAULTS", script)

    def test_current_workflows_run_when_profile_input_is_omitted(self):
        director = PromptDirector()
        for workflow_profile, expected in (
            ("2.3", "LTX 2.3"),
            ("2.5", "LTX 2.5"),
        ):
            response = director.direct(
                "MANUAL",
                "exact prompt",
                "",
                "DURATION: 8",
                False,
                "",
                "http://127.0.0.1:11434",
                "8-12 GB",
                "AUTO",
                extra_pnginfo={
                    "workflow": {
                        "extra": {
                            "velvet_vice_ltx_profile": workflow_profile,
                        }
                    }
                },
            )
            package = response["result"][0]
            self.assertEqual(package["ltx_prompt_profile"], expected)
            self.assertEqual(package["final_prompt"], "exact prompt")

    def test_final_prompt_preview_is_exact_passthrough(self):
        prompt = "Keep this exact final prompt, including punctuation."
        response = FinalPromptPreview().preview(prompt)
        self.assertEqual(response["result"], (prompt,))
        self.assertEqual(response["ui"]["final_prompt"], [prompt])
        self.assertIn("exact LTXDirector input", response["ui"]["stats"][0])

    def test_final_prompt_preview_frontend_is_copyable(self):
        preview_script = (
            ROOT / "web" / "final_prompt_preview.js"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "FINAL PROMPT SENT TO LTXDIRECTOR",
            preview_script,
        )
        self.assertIn("navigator.clipboard.writeText", preview_script)

    def test_fast_output_preview_loads_saved_file_without_transcode(self):
        preview_script = (
            ROOT / "web" / "auto_video_output.js"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "VelvetViceLTXAutoVideoCombineV0112",
            preview_script,
        )
        self.assertIn(
            "api.apiURL(",
            preview_script,
        )
        self.assertIn('"/view?"', preview_script)
        self.assertNotIn("/vhs/viewvideo", preview_script)

    def test_v019_output_mapping_cannot_resolve_to_legacy_class(self):
        self.assertEqual(
            VersionedVideoOutput.__name__,
            "VelvetViceLTXAutoVideoCombineV019",
        )
        self.assertEqual(
            VersionedVideoOutput.IMPLEMENTATION_VERSION,
            "0.1.9",
        )

    def test_v0110_output_mapping_cannot_resolve_to_legacy_class(self):
        self.assertEqual(
            FastVersionedVideoOutput.__name__,
            "VelvetViceLTXAutoVideoCombineV0110",
        )
        self.assertEqual(
            FastVersionedVideoOutput.IMPLEMENTATION_VERSION,
            "0.1.10",
        )

    def test_v0112_output_mapping_cannot_resolve_to_legacy_class(self):
        self.assertEqual(
            StableVersionedVideoOutput.__name__,
            "VelvetViceLTXAutoVideoCombineV0112",
        )
        self.assertEqual(
            StableVersionedVideoOutput.IMPLEMENTATION_VERSION,
            "0.1.12",
        )

    def test_barrier_is_always_changed(self):
        self.assertTrue(math.isnan(Barrier.IS_CHANGED()))

    def test_manual_package_skips_network(self):
        package = {
            "schema": "VELVET_VICE_PROMPT_PACKAGE",
            "final_prompt": "exact",
            "used_models": [],
            "release_required": False,
        }
        with patch.object(
            sys.modules[
                "velvet_vice_ltx_test_package.nodes."
                "ollama_release"
            ].OllamaClient,
            "release_models",
        ) as release:
            self.assertEqual(
                Barrier().release(package, True, 20),
                ("exact",),
            )
            release.assert_not_called()

    def test_prompt_first_gate_requests_render_inputs_lazily(self):
        gate = Gate()
        gate_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.lazy_model_gate"
        ]
        with patch.object(
            gate_module,
            "start_render_memory_monitor",
        ), patch.object(gate_module, "log_memory_snapshot"):
            needed = gate.check_lazy_status(
                "released prompt",
                model=None,
                clip=None,
                audio_vae=None,
                custom_width=None,
                custom_height=None,
            )
        self.assertEqual(
            needed,
            [
                "model",
                "clip",
                "audio_vae",
                "custom_width",
                "custom_height",
            ],
        )

    def test_prompt_first_gate_passthrough_is_exact(self):
        values = (
            "released prompt",
            object(),
            object(),
            object(),
            768,
            512,
        )
        gate_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.lazy_model_gate"
        ]
        with patch.object(gate_module, "log_memory_snapshot"):
            self.assertEqual(
                Gate().release_render_inputs(*values),
                values,
            )

    def test_pre_decode_gate_releases_models_and_preserves_latents(self):
        video_latent = {"samples": object()}
        audio_latent = {"samples": object()}
        gate_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.decode_memory"
        ]
        with patch.object(
            gate_module,
            "log_memory_snapshot",
        ), patch.object(
            gate_module,
            "unload_sampling_models_before_decode",
        ) as unload:
            result = PreDecodeGate().release_before_decode(
                video_latent,
                audio_latent,
                True,
            )

        self.assertEqual(result, (video_latent, audio_latent))
        unload.assert_called_once_with()

    def test_image_checkpoint_is_exact_passthrough(self):
        image = object()
        checkpoint_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.decode_memory"
        ]
        with patch.object(
            checkpoint_module,
            "log_memory_snapshot",
        ) as snapshot:
            result = ImageCheckpoint().checkpoint(image, "after video")

        self.assertEqual(result, (image,))
        snapshot.assert_called_once_with("after video")

    def test_audio_checkpoint_is_exact_passthrough(self):
        audio = object()
        checkpoint_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.decode_memory"
        ]
        with patch.object(
            checkpoint_module,
            "log_memory_snapshot",
        ) as snapshot:
            result = AudioCheckpoint().checkpoint(audio, "after audio")

        self.assertEqual(result, (audio,))
        snapshot.assert_called_once_with("after audio")

    def test_chunked_scale_defaults_to_native_quality_profile(self):
        inputs = ChunkedScale.INPUT_TYPES()["required"]
        self.assertEqual(inputs["upscale_method"][1]["default"], "bicubic")
        self.assertEqual(inputs["scale_by"][1]["default"], 1.0)
        self.assertEqual(inputs["frame_chunk_size"][1]["default"], 4)

    def test_chunked_scale_uses_complete_frame_ranges(self):
        scale_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes."
            "chunked_image_scale"
        ]
        self.assertEqual(
            list(scale_module.frame_ranges(10, 4)),
            [(0, 4), (4, 8), (8, 10)],
        )

    def test_chunked_scale_matches_comfy_dimension_rounding(self):
        scale_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes."
            "chunked_image_scale"
        ]
        self.assertEqual(scale_module.scaled_dimension(1792, 0.75), 1344)
        self.assertEqual(scale_module.scaled_dimension(2688, 0.75), 2016)

    def test_fp16_chunked_scale_keeps_native_quality_defaults(self):
        inputs = FP16ChunkedScale.INPUT_TYPES()["required"]
        self.assertEqual(inputs["upscale_method"][1]["default"], "bicubic")
        self.assertEqual(inputs["scale_by"][1]["default"], 1.0)
        self.assertEqual(inputs["frame_chunk_size"][1]["default"], 4)

    def test_fp16_full_vae_requests_half_output_and_restores_vae(self):
        fp16_token = object()

        class FakeImage:
            dtype = fp16_token
            shape = (193, 64, 96, 3)

        class FakeVAE:
            def __init__(self):
                self.requested_dtypes = []

            def vae_output_dtype(self):
                return "original"

            def decode(self, latent):
                self.requested_dtypes.append(self.vae_output_dtype())
                return FakeImage()

        vae = FakeVAE()
        decode_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.decode_memory"
        ]
        fake_torch = SimpleNamespace(float16=fp16_token)
        fake_latent = SimpleNamespace(is_nested=False)

        with patch.dict(sys.modules, {"torch": fake_torch}), patch.object(
            decode_module,
            "log_memory_snapshot",
        ):
            result = FP16VAEDecode().decode(
                {"samples": fake_latent},
                vae,
            )

        self.assertIsInstance(result[0], FakeImage)
        self.assertEqual(vae.requested_dtypes, [fp16_token])
        self.assertEqual(vae.vae_output_dtype(), "original")
        self.assertNotIn("vae_output_dtype", vae.__dict__)

    def test_fp16_full_vae_rejects_old_comfy_output_api(self):
        decode_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.decode_memory"
        ]
        fake_torch = SimpleNamespace(float16=object())

        with patch.dict(sys.modules, {"torch": fake_torch}), patch.object(
            decode_module,
            "log_memory_snapshot",
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Update ComfyUI",
            ):
                FP16VAEDecode().decode(
                    {"samples": SimpleNamespace(is_nested=False)},
                    SimpleNamespace(),
                )

    def test_system_check_stops_before_ltx_when_flags_missing(self):
        system_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.system_check"
        ]
        snapshot = sys.modules[
            "velvet_vice_ltx_test_package.services."
            "memory_lifecycle"
        ].MemorySnapshot(
            "preflight", 20.0, 50.0, 2.0, 30.0, 31.8
        )
        with patch.object(system_module.sys, "argv", ["main.py"]), (
            patch.object(
                system_module,
                "log_memory_snapshot",
                return_value=snapshot,
            )
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "fp8_e4m3fn-text-enc",
            ):
                SystemCheck().check(
                    "prompt",
                    True,
                    90.0,
                    12.0,
                    1.0,
                    90.0,
                    96.0,
                )

    def test_system_check_passes_with_required_flags(self):
        system_module = sys.modules[
            "velvet_vice_ltx_test_package.nodes.system_check"
        ]
        snapshot = sys.modules[
            "velvet_vice_ltx_test_package.services."
            "memory_lifecycle"
        ].MemorySnapshot(
            "preflight", 20.0, 50.0, 2.0, 30.0, 31.8
        )
        argv = [
            "main.py",
            "--fp8_e4m3fn-text-enc",
            "--fast-disk",
        ]
        with patch.object(system_module.sys, "argv", argv), patch.object(
            system_module,
            "log_memory_snapshot",
            return_value=snapshot,
        ):
            prompt, policy, status = SystemCheck().check(
                "prompt",
                True,
                90.0,
                12.0,
                1.0,
                90.0,
                96.0,
            )
        self.assertEqual(prompt, "prompt")
        self.assertTrue(policy["startup_flags_ok"])
        self.assertIn("passed", status)

    def test_final_cleanup_is_output_node(self):
        self.assertTrue(FinalCleanup.OUTPUT_NODE)
        self.assertTrue(math.isnan(FinalCleanup.IS_CHANGED()))

    def test_single_output_cleanup_has_one_video_dependency(self):
        required = SingleOutputCleanup.INPUT_TYPES()["required"]
        self.assertEqual(
            list(required),
            ["final_video", "unload_render_models"],
        )
        self.assertTrue(SingleOutputCleanup.OUTPUT_NODE)
        self.assertTrue(math.isnan(SingleOutputCleanup.IS_CHANGED()))


if __name__ == "__main__":
    unittest.main()
