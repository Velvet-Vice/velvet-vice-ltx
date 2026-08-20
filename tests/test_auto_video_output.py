import importlib.util
from datetime import datetime
from pathlib import Path
import numpy as np
import subprocess
import sys
import types
import unittest
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "nodes"
    / "auto_video_output.py"
)
SPEC = importlib.util.spec_from_file_location(
    "velvet_vice_auto_video_output_test_module",
    MODULE_PATH,
)
auto_video_output = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(auto_video_output)


class FakeVideoCombine:
    calls = []
    fail_nvenc = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "format": (
                    [
                        auto_video_output.NVENC_FORMAT,
                        auto_video_output.CPU_FORMAT,
                    ],
                )
            }
        }

    def combine_video(self, **kwargs):
        type(self).calls.append(kwargs)
        if (
            type(self).fail_nvenc
            and kwargs["format"] == auto_video_output.NVENC_FORMAT
        ):
            raise RuntimeError("simulated NVENC failure")
        return {
            "ui": {"gifs": [{"filename": "final.mp4"}]},
            "result": ((True, ["final.mp4"]),),
        }


class FakeTensor:
    def __init__(self, array):
        self.array = array

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.array


def run_output(mode):
    return auto_video_output.VelvetViceLTXAutoVideoCombine().combine_video(
        images=object(),
        frame_rate=48,
        loop_count=0,
        filename_prefix="video/test",
        encoder_mode=mode,
        nvenc_bitrate_mbps_at_24fps=60,
        cpu_crf=15,
        pix_fmt="yuv420p",
        pingpong=False,
        save_metadata=False,
        trim_to_audio=False,
        save_output=True,
    )


class AutoVideoOutputTests(unittest.TestCase):
    def setUp(self):
        FakeVideoCombine.calls = []
        FakeVideoCombine.fail_nvenc = False
        self.fake_nodes = types.SimpleNamespace(
            NODE_CLASS_MAPPINGS={
                "VHS_VideoCombine": FakeVideoCombine,
            }
        )

    def test_nvenc_bitrate_scales_with_selected_fps(self):
        self.assertEqual(
            auto_video_output.scaled_nvenc_bitrate(60, 12),
            60,
        )
        self.assertEqual(
            auto_video_output.scaled_nvenc_bitrate(60, 24),
            60,
        )
        self.assertEqual(
            auto_video_output.scaled_nvenc_bitrate(60, 48),
            120,
        )

    def test_probe_runs_a_real_one_frame_nvenc_encode(self):
        auto_video_output.probe_nvenc.cache_clear()
        completed = subprocess.CompletedProcess([], 0, b"", b"")
        with patch.object(
            auto_video_output.subprocess,
            "run",
            return_value=completed,
        ) as run:
            available, detail = auto_video_output.probe_nvenc(
                "ffmpeg"
            )

        self.assertTrue(available)
        self.assertEqual(detail, "hardware probe succeeded")
        self.assertIn("h264_nvenc", run.call_args.args[0])
        self.assertIn("lavfi", run.call_args.args[0])
        self.assertIn(
            "color=c=black:s=256x256:r=24",
            run.call_args.args[0],
        )
        self.assertIn("yuv420p", run.call_args.args[0])

    def test_date_prefix_is_expanded_and_windows_safe(self):
        resolved = auto_video_output.resolve_filename_prefix(
            "video/%date:yyyy-MM-dd%/"
            "%date:hhmmss%-LTX23-FINAL",
            now=datetime(2026, 7, 26, 15, 40, 1),
        )
        self.assertEqual(
            resolved,
            "video/2026-07-26/154001-LTX23-FINAL",
        )
        self.assertNotIn(":", resolved)

    def test_v019_output_has_a_unique_implementation_marker(self):
        output = auto_video_output.VelvetViceLTXAutoVideoCombineV019
        self.assertEqual(output.IMPLEMENTATION_VERSION, "0.1.9")
        self.assertTrue(issubclass(
            output,
            auto_video_output.VelvetViceLTXAutoVideoCombine,
        ))

    def test_v0110_output_has_a_unique_implementation_marker(self):
        output = auto_video_output.VelvetViceLTXAutoVideoCombineV0110
        self.assertEqual(output.IMPLEMENTATION_VERSION, "0.1.10")
        self.assertTrue(issubclass(
            output,
            auto_video_output.VelvetViceLTXAutoVideoCombine,
        ))

    def test_v0112_output_has_a_unique_implementation_marker(self):
        output = auto_video_output.VelvetViceLTXAutoVideoCombineV0112
        self.assertEqual(output.IMPLEMENTATION_VERSION, "0.1.12")
        self.assertTrue(issubclass(
            output,
            auto_video_output.VelvetViceLTXAutoVideoCombine,
        ))

    def test_v0112_frontend_adds_preview_after_widget_restore(self):
        frontend = (
            MODULE_PATH.parents[1]
            / "web"
            / "auto_video_output.js"
        ).read_text(encoding="utf-8")
        self.assertIn("loadedGraphNode(node)", frontend)
        self.assertIn("addPreviewAfterCurrentConfiguration(node)", frontend)
        self.assertIn("serialize: false", frontend)
        self.assertNotIn("onNodeCreated", frontend)

    def test_fp16_fast_converter_rounds_to_expected_rgb8(self):
        source = np.array(
            [0.0, 0.1, 0.5, 0.999, 1.0],
            dtype=np.float16,
        )
        converted = auto_video_output._fp16_tensor_to_rgb8(
            FakeTensor(source)
        )
        expected = np.clip(
            source.astype(np.float32) * 255.0 + 0.5,
            0.0,
            255.0,
        ).astype(np.uint8)
        np.testing.assert_array_equal(converted, expected)

    def test_fast_converter_defers_non_fp16_input(self):
        source = FakeTensor(np.array([0.5], dtype=np.float32))
        self.assertIsNone(
            auto_video_output._fp16_tensor_to_rgb8(source)
        )

    def test_accelerated_vhs_converter_is_scoped_and_restored(self):
        module = types.SimpleNamespace()

        def original(_tensor):
            return np.array([99], dtype=np.uint8)

        module.tensor_to_bytes = original
        fake_class = type("ScopedVideoCombine", (), {})
        fake_class.__module__ = "fake_vhs_scoped_module"
        source = FakeTensor(
            np.array([0.0, 0.5, 1.0], dtype=np.float16)
        )
        with patch.dict(
            sys.modules,
            {"fake_vhs_scoped_module": module},
        ):
            with auto_video_output.accelerated_vhs_rgb8(
                fake_class
            ) as stats:
                converted = module.tensor_to_bytes(source)
                self.assertIsNot(module.tensor_to_bytes, original)

        self.assertIs(module.tensor_to_bytes, original)
        np.testing.assert_array_equal(
            converted,
            np.array([0, 128, 255], dtype=np.uint8),
        )
        self.assertTrue(stats["enabled"])
        self.assertEqual(stats["frames"], 1)

    def test_default_prefix_is_windows_safe_without_runtime_expansion(self):
        inputs = (
            auto_video_output.VelvetViceLTXAutoVideoCombineV019
            .INPUT_TYPES()["required"]
        )
        default_prefix = inputs["filename_prefix"][1]["default"]
        self.assertEqual(default_prefix, "video/LTX23-FINAL")
        self.assertNotRegex(default_prefix, r'[<>:"|?*]')

    def test_literal_invalid_windows_path_characters_are_sanitized(self):
        resolved = auto_video_output.resolve_filename_prefix(
            'video/bad:name?/final*'
        )
        self.assertEqual(resolved, "video/bad-name-/final-")

    def test_auto_mode_delegates_one_nvenc_encode(self):
        with patch.dict(sys.modules, {"nodes": self.fake_nodes}), (
            patch.object(
                auto_video_output,
                "_ffmpeg_path",
                return_value="ffmpeg",
            )
        ), patch.object(
            auto_video_output,
            "probe_nvenc",
            return_value=(True, "available"),
        ):
            result = run_output(auto_video_output.AUTO_MODE)

        self.assertEqual(
            result["result"],
            ((True, ["final.mp4"]),),
        )
        self.assertEqual(len(FakeVideoCombine.calls), 1)
        call = FakeVideoCombine.calls[0]
        self.assertEqual(
            call["format"],
            auto_video_output.NVENC_FORMAT,
        )
        self.assertEqual(call["bitrate"], 120)
        self.assertTrue(call["megabit"])

    def test_output_delegate_receives_resolved_date_prefix(self):
        with patch.dict(sys.modules, {"nodes": self.fake_nodes}), (
            patch.object(
                auto_video_output,
                "_ffmpeg_path",
                return_value="ffmpeg",
            )
        ), patch.object(
            auto_video_output,
            "probe_nvenc",
            return_value=(True, "available"),
        ), patch.object(
            auto_video_output,
            "datetime",
        ) as current_datetime:
            current_datetime.now.return_value = datetime(
                2026, 7, 26, 15, 40, 1
            )
            auto_video_output.VelvetViceLTXAutoVideoCombine().combine_video(
                images=object(),
                frame_rate=24,
                loop_count=0,
                filename_prefix=(
                    "video/%date:yyyy-MM-dd%/"
                    "%date:hhmmss%-LTX23-FINAL"
                ),
                encoder_mode=auto_video_output.AUTO_MODE,
                nvenc_bitrate_mbps_at_24fps=60,
                cpu_crf=15,
                pix_fmt="yuv420p",
                pingpong=False,
                save_metadata=False,
                trim_to_audio=False,
                save_output=True,
            )

        self.assertEqual(
            FakeVideoCombine.calls[0]["filename_prefix"],
            "video/2026-07-26/154001-LTX23-FINAL",
        )

    def test_auto_mode_uses_cpu_when_probe_fails(self):
        with patch.dict(sys.modules, {"nodes": self.fake_nodes}), (
            patch.object(
                auto_video_output,
                "_ffmpeg_path",
                return_value="ffmpeg",
            )
        ), patch.object(
            auto_video_output,
            "probe_nvenc",
            return_value=(False, "unavailable"),
        ):
            run_output(auto_video_output.AUTO_MODE)

        self.assertEqual(len(FakeVideoCombine.calls), 1)
        call = FakeVideoCombine.calls[0]
        self.assertEqual(
            call["format"],
            auto_video_output.CPU_FORMAT,
        )
        self.assertEqual(call["crf"], 15)

    def test_auto_mode_retries_cpu_after_nvenc_runtime_failure(self):
        FakeVideoCombine.fail_nvenc = True
        with patch.dict(sys.modules, {"nodes": self.fake_nodes}), (
            patch.object(
                auto_video_output,
                "_ffmpeg_path",
                return_value="ffmpeg",
            )
        ), patch.object(
            auto_video_output,
            "probe_nvenc",
            return_value=(True, "available"),
        ):
            run_output(auto_video_output.AUTO_MODE)

        self.assertEqual(
            [call["format"] for call in FakeVideoCombine.calls],
            [
                auto_video_output.NVENC_FORMAT,
                auto_video_output.CPU_FORMAT,
            ],
        )


if __name__ == "__main__":
    unittest.main()
