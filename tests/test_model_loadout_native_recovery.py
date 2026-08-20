import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModelLoadoutNativeRecoveryTests(unittest.TestCase):
    def test_model_loadout_stays_native_on_the_outer_subgraph_node(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        dispatch = script.split("function installVisiblePanel(node)", 1)[1].split("function reassertVisiblePanels", 1)[0]
        self.assertNotIn("installModelLoadoutPanel(node)", dispatch)
        self.assertIn("Keep MODEL LOADOUT native", dispatch)

    def test_model_loadout_gets_the_centered_canvas_header(self):
        script = (ROOT / "web" / "00_velvet_vice_design_system_v1115_drag_safe.js").read_text(encoding="utf-8")
        full_panel_block = script.split("const FULL_PANEL_TYPES", 1)[1].split("]);", 1)[0]
        self.assertNotIn("8c71665b-ab34-421b-96d5-fa30283a93a8", full_panel_block)
        self.assertIn('ctx.textAlign = "center"', script)
        self.assertIn("const HEADER_HEIGHT = 44", script)
        self.assertIn("const WIDGET_START_Y = 54", script)
        self.assertIn("node.widgets_start_y = Math.max", script)


if __name__ == "__main__":
    unittest.main()
