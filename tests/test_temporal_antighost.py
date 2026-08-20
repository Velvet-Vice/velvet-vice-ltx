import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_root_package():
    name = "velvet_vice_ltx_antighost_test_package"
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
Analyzer = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceLTXGhostAnalyzer"]
AntiGhost = PACKAGE.NODE_CLASS_MAPPINGS[
    "VelvetViceLTXTemporalAntiGhost"
]
MODULE = sys.modules[
    "velvet_vice_ltx_antighost_test_package.nodes."
    "temporal_antighost"
]


class FakeImages:
    shape = (9, 720, 1280, 3)


class TemporalAntiGhostTests(unittest.TestCase):
    def test_nodes_have_experimental_display_names(self):
        names = PACKAGE.NODE_DISPLAY_NAME_MAPPINGS
        self.assertNotIn("[ALPHA]", names["VelvetViceLTXGhostAnalyzer"])
        self.assertNotIn(
            "[ALPHA]",
            names["VelvetViceLTXTemporalAntiGhost"],
        )

    def test_analyzer_defaults_to_safe_source_mode(self):
        inputs = Analyzer.INPUT_TYPES()["required"]
        self.assertEqual(inputs["mode"][1]["default"], "SOURCE 24 FPS")
        self.assertEqual(inputs["profile"][1]["default"], "SAFE")
        self.assertEqual(inputs["frame_rate"][1]["default"], 24.0)
        self.assertEqual(inputs["analysis_long_edge"][1]["default"], 256)
        self.assertEqual(inputs["memory_mode"][1]["default"], "AUTO")

    def test_source_mode_analyzes_every_interior_frame(self):
        self.assertEqual(
            MODULE.active_frame_indices(7, "SOURCE 24 FPS"),
            [1, 2, 3, 4, 5],
        )

    def test_rife_mode_protects_even_anchor_frames(self):
        self.assertEqual(
            MODULE.active_frame_indices(9, "RIFE INSERTED FRAMES"),
            [1, 3, 5, 7],
        )

    def test_short_sequences_have_no_active_frames(self):
        self.assertEqual(
            MODULE.active_frame_indices(2, "SOURCE 24 FPS"),
            [],
        )

    def test_analysis_dimensions_preserve_aspect_and_never_upscale(self):
        self.assertEqual(
            MODULE.analysis_dimensions(720, 1280, 256),
            (144, 256),
        )
        self.assertEqual(
            MODULE.analysis_dimensions(128, 192, 256),
            (128, 192),
        )

    def test_higher_sensitivity_lowers_detection_threshold(self):
        normal = MODULE.profile_threshold("SAFE", 1.0)
        sensitive = MODULE.profile_threshold("SAFE", 2.0)
        self.assertLess(sensitive, normal)
        self.assertGreater(
            MODULE.profile_threshold("SAFE", 1.0),
            MODULE.profile_threshold("STRONG", 1.0),
        )

    def test_disabled_repair_is_zero_copy_passthrough(self):
        images = object()
        self.assertEqual(
            AntiGhost().check_lazy_status(
                images,
                ghost_analysis=None,
                enabled=False,
            ),
            [],
        )
        result, report = AntiGhost().repair(
            images,
            ghost_analysis=None,
            enabled=False,
            strength=0.55,
            maximum_pixel_change=0.20,
            minimum_frame_score=1.0,
            memory_mode="AUTO",
        )
        self.assertIs(result, images)
        self.assertIn("bypassed", report)

    def test_enabled_repair_requests_analysis_lazily(self):
        self.assertEqual(
            AntiGhost().check_lazy_status(
                object(),
                ghost_analysis=None,
                enabled=True,
            ),
            ["ghost_analysis"],
        )
        self.assertEqual(
            AntiGhost().check_lazy_status(
                object(),
                ghost_analysis={"schema": "test"},
                enabled=True,
            ),
            [],
        )

    def test_analysis_shape_mismatch_is_rejected(self):
        analysis = {
            "schema": "VELVET_VICE_GHOST_ANALYSIS_V1",
            "frame_count": 8,
            "height": 720,
            "width": 1280,
        }
        with self.assertRaisesRegex(ValueError, "does not match"):
            MODULE._validate_analysis(FakeImages(), analysis)

    def test_report_converts_frame_indices_to_seconds(self):
        report = MODULE._format_report(
            mode="SOURCE 24 FPS",
            profile="SAFE",
            frame_rate=24.0,
            frame_scores=[0.0, 8.0, 0.0],
            active_indices=[1],
            skipped_scene_cuts=[],
            analysis_width=256,
            analysis_height=144,
            average_score=8.0,
            maximum_score=8.0,
        )
        self.assertIn("#1 (0.04s, 8.0)", report)
        self.assertIn("Scene-cut protected frames: none", report)


if __name__ == "__main__":
    unittest.main()
