from __future__ import annotations

import importlib
import unittest
import tempfile
from pathlib import Path
from PIL import Image

import numpy as np

from test_release_barrier import PACKAGE

torch = importlib.import_module("torch")
watermark_module = importlib.import_module(
    PACKAGE.__name__ + ".nodes.watermark_overlay"
)
compose_watermark_tensor = watermark_module.compose_watermark_tensor
VelvetViceWatermarkOverlay = watermark_module.VelvetViceWatermarkOverlay


def _mark():
    rgba = np.zeros((20, 40, 4), dtype=np.float32)
    rgba[..., 0] = 1.0
    rgba[..., 3] = 1.0
    return rgba


class WatermarkOverlayTests(unittest.TestCase):
    def test_watermark_bottom_right_changes_only_expected_corner(self):
        images = torch.zeros((2, 100, 200, 3), dtype=torch.float32)
        out = compose_watermark_tensor(
            images,
            _mark(),
            position="bottom-right",
            scale=0.20,
            opacity=1.0,
            margin_x=10,
            margin_y=10,
        )
        self.assertEqual(tuple(out.shape), tuple(images.shape))
        self.assertGreater(float(out[:, -20:-10, -50:-10, 0].max()), 0.9)
        self.assertEqual(float(out[:, :20, :20].max()), 0.0)

    def test_watermark_center_uses_alpha_and_opacity(self):
        images = torch.zeros((1, 120, 120, 3), dtype=torch.float32)
        out = compose_watermark_tensor(
            images,
            _mark(),
            position="center",
            scale=0.5,
            opacity=0.5,
            margin_x=0,
            margin_y=0,
        )
        self.assertGreaterEqual(float(out[..., 0].max()), 0.45)
        self.assertLessEqual(float(out[..., 0].max()), 0.51)
        self.assertEqual(float(out[..., 1].max()), 0.0)

    def test_watermark_file_is_a_local_upload_combo(self):
        required = VelvetViceWatermarkOverlay.INPUT_TYPES()["required"]
        self.assertIsInstance(required["watermark_file"][0], list)
        self.assertTrue(required["watermark_file"][1].get("image_upload"))
        self.assertEqual(required["position"][0], "STRING")


    def test_apply_uses_selected_custom_file_instead_of_default(self):
        images = torch.zeros((1, 80, 120, 3), dtype=torch.float32)
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "my_custom_watermark.png"
            rgba = np.zeros((12, 24, 4), dtype=np.uint8)
            rgba[..., 1] = 255
            rgba[..., 3] = 255
            Image.fromarray(rgba, mode="RGBA").save(custom)
            out, = VelvetViceWatermarkOverlay().apply(
                images, True, str(custom), "top-left", 0.2, 1.0, 0, 0
            )
        self.assertGreater(float(out[..., 1].max()), 0.9)
        self.assertEqual(float(out[..., 0].max()), 0.0)

    def test_unknown_position_falls_back_safely(self):
        images = torch.zeros((1, 100, 200, 3), dtype=torch.float32)
        out = compose_watermark_tensor(
            images,
            _mark(),
            position="not-a-real-position",
            scale=0.20,
            opacity=1.0,
            margin_x=10,
            margin_y=10,
        )
        # Unknown values deliberately fall back to bottom-right.
        self.assertGreater(float(out[:, -20:-10, -50:-10, 0].max()), 0.9)


if __name__ == "__main__":
    unittest.main()
