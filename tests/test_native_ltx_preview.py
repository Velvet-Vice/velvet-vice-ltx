import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from test_release_barrier import PACKAGE, ROOT


Bridge = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceLTXNativePreviewBridge"]
Display = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceLTXLivePreviewDisplay"]
module = sys.modules[Bridge.__module__]
WORKFLOW_DIR = ROOT.parents[1] / "01_WORKFLOW"


class NativeLTXPreviewTests(unittest.TestCase):
    def test_nodes_are_registered(self):
        self.assertTrue(Display.OUTPUT_NODE)
        self.assertEqual(Display.RETURN_TYPES, ())
        self.assertEqual(Bridge.RETURN_TYPES, ("MODEL",))

    def test_bridge_contract_preserves_old_optional_links(self):
        inputs = Bridge.INPUT_TYPES()
        self.assertIn("model", inputs["required"])
        self.assertIn("preview_rate", inputs["required"])
        self.assertIn("latent_upscale_model", inputs["optional"])
        self.assertIn("vae", inputs["optional"])
        self.assertEqual(inputs["required"]["preview_rate"][1]["default"], 24.0)
        self.assertEqual(inputs["required"]["preview_rate"][1]["min"], 24.0)
        self.assertEqual(inputs["required"]["jpeg_quality"][1]["default"], 95)
        self.assertEqual(inputs["required"]["max_preview_edge"][1]["default"], 768)

    def test_wrapper_clamps_playback_to_minimum_24fps(self):
        wrapper = module._NativePreviewOuterWrapper(
            preview_rate=1,
            jpeg_quality=60,
            max_edge=128,
        )
        self.assertEqual(wrapper.preview_rate, 24.0)
        self.assertEqual(wrapper.jpeg_quality, 85)
        self.assertEqual(wrapper.max_edge, 512)

    def test_pass_mapping_uses_the_three_protected_samplers(self):
        self.assertEqual(module._pass_number("3676:3650"), 1)
        self.assertEqual(module._pass_number("3676:3649"), 2)
        self.assertEqual(module._pass_number("3676:3656"), 3)
        self.assertIsNone(module._pass_number("3676"))

    def test_bridge_clones_model_and_installs_only_outer_sample_wrapper(self):
        class FakeClone:
            def __init__(self):
                self.calls = []

            def add_wrapper_with_key(self, wrapper_type, key, wrapper):
                self.calls.append((wrapper_type, key, wrapper))

        class FakeModel:
            def __init__(self):
                self.clone_result = FakeClone()

            def clone(self):
                return self.clone_result

        fake_comfy = types.ModuleType("comfy")
        fake_comfy.__path__ = []
        fake_patcher = types.ModuleType("comfy.patcher_extension")
        fake_patcher.WrappersMP = types.SimpleNamespace(OUTER_SAMPLE="OUTER_SAMPLE")
        fake_comfy.patcher_extension = fake_patcher

        model = FakeModel()
        with patch.dict(
            sys.modules,
            {"comfy": fake_comfy, "comfy.patcher_extension": fake_patcher},
        ):
            result = Bridge().apply_preview_bridge(model, 24.0, 95, 768, None, None)

        self.assertIs(result[0], model.clone_result)
        self.assertEqual(len(model.clone_result.calls), 1)
        wrapper_type, key, wrapper = model.clone_result.calls[0]
        self.assertEqual(wrapper_type, "OUTER_SAMPLE")
        self.assertEqual(key, module.WRAPPER_KEY)
        self.assertEqual(wrapper.preview_rate, 24.0)

    def test_wrapper_uses_connected_preview_vae_and_sends_24fps_frame_buffer(self):
        events = []
        original_callbacks = []

        class FakePreviewVAE:
            def __init__(self):
                self.decode_calls = []

            def decode(self, latent):
                self.decode_calls.append(tuple(latent.shape))
                image = latent[:, :3, 0]
                image = torch.nn.functional.interpolate(
                    image,
                    size=(90, 160),
                    mode="bilinear",
                    align_corners=False,
                ).sigmoid()
                return image.movedim(1, -1).unsqueeze(1)

        class FakeServerInstance:
            last_node_id = "3676:3649"
            client_id = "client"

            def send_sync(self, event, payload, client_id):
                events.append((event, payload, client_id))

        fake_server = types.ModuleType("server")
        fake_server.PromptServer = types.SimpleNamespace(instance=FakeServerInstance())
        factors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.2, 0.2, 0.2],
        ]
        latent_format = types.SimpleNamespace(
            latent_rgb_factors=factors,
            latent_rgb_factors_bias=[0.0, 0.0, 0.0],
            latent_rgb_factors_reshape=None,
        )
        guider = types.SimpleNamespace(
            model_patcher=types.SimpleNamespace(
                model=types.SimpleNamespace(latent_format=latent_format)
            ),
            conds={"positive": []},
        )

        class FakeExecutor:
            class_obj = guider

            def __call__(
                self,
                noise,
                latent_image,
                sampler,
                sigmas,
                denoise_mask,
                callback,
                disable_pbar,
                seed,
                latent_shapes,
            ):
                x0 = torch.rand((1, 4, 2, 45, 80), dtype=torch.float32)
                callback(0, x0, x0, 1)
                return "ok"

        vae = FakePreviewVAE()
        wrapper = module._NativePreviewOuterWrapper(
            preview_rate=24,
            jpeg_quality=95,
            max_edge=768,
            latent_upscale_model=object(),
            vae=vae,
        )
        with patch.dict(sys.modules, {"server": fake_server}):
            result = wrapper(
                FakeExecutor(),
                None,
                None,
                None,
                torch.tensor([1.0, 0.0]),
                None,
                lambda *args: original_callbacks.append(args),
                False,
                1,
                [],
            )

        self.assertEqual(result, "ok")
        self.assertEqual(len(original_callbacks), 1)
        self.assertEqual(len(events), 1)
        event, payload, client = events[0]
        self.assertEqual(event, module.EVENT_NAME)
        self.assertEqual(client, "client")
        self.assertEqual(payload["pass"], 2)
        self.assertGreaterEqual(payload["playback_fps"], 24)
        self.assertEqual(payload["timeline_fps"], 24)
        self.assertEqual(payload["timeline_frame_count"], 9)
        self.assertEqual(payload["temporal_compression"], 8)
        self.assertAlmostEqual(payload["timeline_duration_seconds"], 9 / 24)
        self.assertAlmostEqual(payload["source_playback_fps"], 2 * 24 / 9)
        self.assertEqual(payload["frame_count"], 2)
        self.assertEqual(len(payload["images"]), 2)
        self.assertEqual(payload["image"], payload["images"][0])
        self.assertTrue(all(payload["images"]))
        self.assertTrue(payload["used_preview_vae"])
        self.assertFalse(payload["used_latent_upscaler"])
        self.assertEqual(max(payload["width"], payload["height"]), 768)
        self.assertAlmostEqual(payload["width"] / payload["height"], 80 / 45, delta=0.03)
        self.assertEqual(vae.decode_calls, [(2, 4, 1, 45, 80)])

    def test_preview_vae_failure_falls_back_at_requested_edge(self):
        class FailingVAE:
            def decode(self, _latent):
                raise RuntimeError("test decode failure")

        latent_format = types.SimpleNamespace(
            latent_rgb_factors=[
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.2, 0.2, 0.2],
            ],
            latent_rgb_factors_bias=[0.0, 0.0, 0.0],
            latent_rgb_factors_reshape=None,
        )
        wrapper = module._NativePreviewOuterWrapper(
            preview_rate=24,
            jpeg_quality=95,
            max_edge=768,
            vae=FailingVAE(),
        )
        decoded, used_vae = wrapper._decode_frames(
            torch.rand((1, 4, 2, 16, 24)), latent_format
        )
        self.assertFalse(used_vae)
        self.assertEqual(tuple(decoded.shape), (2, 512, 768, 3))

    def test_preview_failure_never_stops_sampling_or_original_callback(self):
        original_callbacks = []
        latent_format = types.SimpleNamespace(
            latent_rgb_factors=[[1.0, 0.0, 0.0]],
            latent_rgb_factors_bias=[0.0, 0.0, 0.0],
            latent_rgb_factors_reshape=None,
        )
        guider = types.SimpleNamespace(
            model_patcher=types.SimpleNamespace(
                model=types.SimpleNamespace(latent_format=latent_format)
            ),
            conds={"positive": []},
        )

        class FakeExecutor:
            class_obj = guider

            def __call__(
                self,
                noise,
                latent_image,
                sampler,
                sigmas,
                denoise_mask,
                callback,
                disable_pbar,
                seed,
                latent_shapes,
            ):
                x0 = torch.rand((1, 1, 1, 4, 4))
                callback(0, x0, x0, 1)
                return "render-result"

        wrapper = module._NativePreviewOuterWrapper(
            preview_rate=24,
            jpeg_quality=95,
            max_edge=768,
        )
        with patch.object(wrapper, "_emit_preview", side_effect=RuntimeError("preview")):
            result = wrapper(
                FakeExecutor(),
                None,
                None,
                None,
                torch.tensor([1.0, 0.0]),
                None,
                lambda *args: original_callbacks.append(args),
                False,
                1,
                [],
            )

        self.assertEqual(result, "render-result")
        self.assertEqual(len(original_callbacks), 1)

    def test_workflow_replaces_only_preview_override_and_adds_display(self):
        workflow_files = list(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json"))
        self.assertEqual(len(workflow_files), 1)
        workflow = json.loads(workflow_files[0].read_text(encoding="utf-8"))

        display = next(node for node in workflow["nodes"] if node["id"] == 4052)
        self.assertEqual(display["type"], "VelvetViceLTXLivePreviewDisplay")
        self.assertEqual(display["pos"], [5360, 1770])
        self.assertEqual(display["size"], [700, 491])

        loader = next(
            subgraph
            for subgraph in workflow["definitions"]["subgraphs"]
            if subgraph["id"] == "8c71665b-ab34-421b-96d5-fa30283a93a8"
        )
        bridge = next(node for node in loader["nodes"] if node["id"] == 3339)
        self.assertEqual(bridge["type"], "VelvetViceLTXNativePreviewBridge")
        self.assertEqual(bridge["widgets_values"], [24.0, 95, 768])
        self.assertEqual(bridge["inputs"][0]["link"], 7598)
        self.assertEqual(bridge["inputs"][1]["link"], 7039)
        self.assertEqual(bridge["inputs"][2]["link"], 7038)
        self.assertEqual(bridge["outputs"][0]["links"], [7045])
        self.assertFalse(
            any(node["type"] == "LTX2SamplingPreviewOverride" for node in loader["nodes"])
        )
        main_groups = [group for group in workflow["groups"] if group["bounding"][1] == 840]
        self.assertEqual(len(main_groups), 7)

    def test_frontend_is_aspect_safe_and_uses_current_dom_layout_api(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzzz_native_ltx_live_preview_v1115.js").read_text(
            encoding="utf-8"
        )
        self.assertIn('const EVENT_NAME = "velvet_vice.ltx_live_preview"', script)
        self.assertIn("api.addEventListener(EVENT_NAME", script)
        self.assertIn("object-fit:contain", script)
        self.assertIn("computeLayoutSize", script)
        self.assertIn("getMinHeight", script)
        self.assertIn("pointer-events:none", script)
        self.assertIn("requestAnimationFrame", script)
        self.assertIn("MIN_TIMELINE_FPS = 24", script)
        self.assertIn("MIN_SOURCE_PLAYBACK_FPS = 0.5", script)
        self.assertIn("detail?.source_playback_fps", script)
        self.assertIn("detail?.timeline_fps", script)
        self.assertIn("FPS TIMELINE", script)
        self.assertIn("REAL TIME", script)
        self.assertIn("detail?.images", script)
        self.assertIn("function removeStaleDisplay(node)", script)
        self.assertIn("vv_native_ltx_live_preview_v1115", script)
        self.assertIn("Sampler is running, but no preview buffer has arrived yet.", script)
        self.assertIn("used_preview_vae", script)
        self.assertIn("function previewGeometry(width, height)", script)
        self.assertIn("TAE HIGH RES", script)
        self.assertNotIn("VHS_latentpreview", script)
        self.assertNotIn("$$canvas-image-preview", script)

    def test_panel_suite_uses_current_dom_layout_api_and_centered_headers(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("domWidget.computeLayoutSize", script)
        self.assertIn("getMinHeight", script)
        self.assertIn("place-items:center", script)
        self.assertIn("text-align:center", script)
        self.assertIn("height:32px", script)
        self.assertIn('const OUTPUT_STUDIO_VERSION = "1.1.15-draggable-single-header"', script)
        self.assertIn("setOutputWidgetHeight", script)
        self.assertIn('shell.style.removeProperty("min-height")', script)
        self.assertNotIn('shell.style.minHeight = `${outputLayout.height}px`', script)
        self.assertIn('closest?.(".dom-widget")?.remove?.()', script)
        self.assertIn("72px 72px 72px", script)
        self.assertIn("min-width:70px", script)
        self.assertIn("::-webkit-inner-spin-button", script)
        self.assertIn("overflow-x:hidden", script)
        self.assertIn("setTimeout(reassertVisiblePanels, 6000)", script)
        self.assertIn("setTimeout(reassertVisiblePanels, 8000)", script)
        self.assertIn("document.head.lastElementChild !== existing", script)


if __name__ == "__main__":
    unittest.main()
