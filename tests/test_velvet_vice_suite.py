import json
import unittest
from pathlib import Path

from test_release_barrier import PACKAGE, ROOT


ControlHub = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceControlHub"]
OutputStudio = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceOutputStudio"]
LoraStudio = PACKAGE.NODE_CLASS_MAPPINGS["VelvetVicePowerLoraAV"]
Preflight = PACKAGE.NODE_CLASS_MAPPINGS["VelvetVicePreflightConsole"]
WatermarkOverlay = PACKAGE.NODE_CLASS_MAPPINGS["VelvetViceWatermarkOverlay"]

PACKAGE_ROOT = ROOT.parents[1]
WORKFLOW_DIR = PACKAGE_ROOT / "01_WORKFLOW"


class VelvetViceSuiteTests(unittest.TestCase):
    def test_workflows_pin_separate_autonomous_prompt_profiles(self):
        expected = {
            "VELVET_VICE_LTX23_v1.2.7.json": ("2.3", "LTX 2.3"),
            "VELVET_VICE_LTX25_v1.2.7.json": ("2.5", "LTX 2.5"),
        }
        for filename, (workflow_profile, prompt_profile) in expected.items():
            workflow = json.loads(
                (WORKFLOW_DIR / filename).read_text(encoding="utf-8")
            )
            director = next(
                node for node in workflow["nodes"] if node["id"] == 4035
            )
            self.assertEqual(len(director["widgets_values"]), 10)
            self.assertEqual(director["widgets_values"][-1], prompt_profile)
            self.assertEqual(
                workflow["extra"]["velvet_vice_ltx_profile"],
                workflow_profile,
            )
            self.assertEqual(
                workflow["extra"]["velvet_vice_version"],
                "1.2.7",
            )

    def test_new_nodes_are_registered(self):
        self.assertIsNotNone(ControlHub)
        self.assertIsNotNone(OutputStudio)
        self.assertIsNotNone(Preflight)
        self.assertIsNotNone(LoraStudio)
        self.assertIsNotNone(WatermarkOverlay)

    def test_profiles_drive_real_boolean_outputs(self):
        node = ControlHub()
        test = node.route_controls(
            "ANTIGHOST", "TEST", True, True, True, True, "My Test", "Velvet_Vice_Watermark.png", "bottom-right", 0.18, 0.65, 24, 24
        )
        self.assertEqual(test[:4], (False, False, False, False))
        balanced = node.route_controls(
            "ANTIGHOST", "BALANCED", True, False, True, True, "My Test", "Velvet_Vice_Watermark.png", "bottom-right", 0.18, 0.65, 24, 24
        )
        self.assertEqual(balanced[:4], (False, True, False, False))
        final = node.route_controls(
            "ANTIGHOST", "FINAL", False, False, False, True, "My Test", "Velvet_Vice_Watermark.png", "bottom-right", 0.18, 0.65, 24, 24
        )
        self.assertEqual(final[:4], (True, True, True, False))
        custom = node.route_controls(
            "ANTIGHOST", "CUSTOM", True, False, True, True, "My Test", "Velvet_Vice_Watermark.png", "bottom-right", 0.18, 0.65, 24, 24
        )
        self.assertEqual(custom[:4], (True, False, True, True))
        self.assertEqual(custom[4], "My Test")

    def test_output_studio_keeps_single_encode_contract(self):
        self.assertTrue(OutputStudio.OUTPUT_NODE)
        self.assertEqual(OutputStudio.RETURN_TYPES, ("VHS_FILENAMES",))
        required = OutputStudio.INPUT_TYPES()["required"]
        self.assertIn("images", required)
        self.assertIn("frame_rate", required)
        self.assertIn("filename_prefix", required)

    def test_frontend_uses_official_extension_and_api_hooks(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("app.registerExtension", script)
        self.assertIn("api.fetchApi", script)
        self.assertIn("api.addEventListener", script)
        self.assertIn("addDOMWidget", script)
        self.assertIn("VelvetVice.LTX.FullPanelSystemV1115DraggableSingleHeader", script)
        self.assertIn("object-fit:contain", script)
        self.assertIn("velvet_vice_preview", script)
        self.assertIn("ResizeObserver", script)
        self.assertIn("Player raster and complete node now follow", script)
        self.assertIn('videoFrame.style.setProperty("inline-size"', script)
        self.assertIn('videoFrame.style.aspectRatio', script)
        self.assertIn('forceNodeSize', script)
        self.assertIn('const previewLayout =', script)
        self.assertIn('installModelLoadoutPanel', script)
        self.assertIn('installRenderEnginePanel', script)
        self.assertIn('installLoraStudio', script)
        self.assertIn('+ ADD LORA', script)
        self.assertIn('CLEAR', script)
        self.assertIn('lora_stack_json', script)
        self.assertIn('FULL', script)
        self.assertIn('VIDEO', script)
        self.assertIn('AUDIO', script)
        self.assertIn('/velvet_vice/ltx/lora/analyze', script)
        self.assertIn('addAdaptiveDOM', script)
        self.assertIn('.vv-power-row', script)
        self.assertIn('installCableSafePanel', script)
        self.assertIn('applyQuietCableTheme', script)
        self.assertIn('PANEL_STYLE_ID', script)
        self.assertIn('input.placeholder = "Search LoRA…"', script)
        self.assertIn('createLoraPicker(slot, index)', script)
        self.assertIn('matchingLoras = (query', script)
        self.assertIn('terms.every((term)', script)
        self.assertIn('terms.every((term)', script)
        self.assertIn('.vv-power-combo-input', script)


    def test_output_studio_stops_ghost_audio_players(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn("function hardStopOutputMedia(media)", script)
        self.assertIn("media.pause?.()", script)
        self.assertIn("media.removeAttribute?.(\"src\")", script)
        self.assertIn("function purgeLegacyOutputPreview(node)", script)
        self.assertIn('\"velvet_vice_final_video_preview\"', script)
        self.assertIn("stopNodeOutputMedia(node, { hard: true });", script)
        self.assertIn('video.addEventListener("play", () => stopOtherOutputMedia(video))', script)
        self.assertIn('video.addEventListener("pause", () => stopOtherOutputMedia(video))', script)
        self.assertIn("try { video.pause(); } catch (_) {}", script)

    def test_power_lora_catalog_search_is_inline_and_multi_word(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('const matchingLoras = (query, limit = 80, allowEmpty = false) =>', script)
        self.assertIn('terms.every((term) => haystack.includes(term))', script)
        self.assertIn('input.placeholder = "Search LoRA…"', script)
        self.assertIn('input.addEventListener("input"', script)
        self.assertIn('createLoraPicker(slot, index)', script)
        self.assertIn('pendingFocusSlotId=slot.id', script)


    def test_full_signature_design_system_is_dynamic_and_global(self):
        script = (ROOT / "web" / "00_velvet_vice_design_system_v1115_drag_safe.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("VelvetVice.LTX.FullSignatureDesignSystemV1115DragSafe", script)
        self.assertIn("drawHeader", script)
        self.assertIn("drawBody", script)
        self.assertIn("__vvExecutionState", script)
        self.assertIn('api.addEventListener("executing"', script)
        self.assertIn("themeGroups", script)
        self.assertIn("vv_design_system", script)
        self.assertIn("const HEADER_HEIGHT = 44", script)
        self.assertIn("const WIDGET_START_Y = 54", script)
        self.assertIn("node.widgets_start_y = Math.max", script)
        self.assertIn("reserveNativeWidgetLane(node)", script)

    def test_v1115_full_dom_panels_sever_cached_canvas_headers(self):
        web = ROOT / "web"
        design = (web / "00_velvet_vice_design_system_v1115_drag_safe.js").read_text(
            encoding="utf-8"
        )
        suite = (web / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(
            encoding="utf-8"
        )
        self.assertFalse((web / "00_velvet_vice_design_system.js").exists())
        self.assertIn('const STYLE_ID = "vv-ltx-design-system-v1115"', design)
        self.assertIn("const isFullDOMPanel = fullPanel(node);", design)
        self.assertIn(
            "const originalBackground = isFullDOMPanel ? null : node.onDrawBackground;",
            design,
        )
        self.assertIn(
            "const originalForeground = isFullDOMPanel ? null : node.onDrawForeground;",
            design,
        )
        self.assertIn("if (!marked(this) || fullPanel(this)) return;", design)
        self.assertIn("node?.__vvSuppressCanvasChromeV1115", design)
        self.assertIn("function enforceSingleDOMHeader(shell)", suite)
        self.assertIn('shell.querySelectorAll(":scope > .vv-head")', suite)
        self.assertIn("for (const duplicate of headers.slice(1))", suite)
        self.assertIn("node.__vvSuppressCanvasChromeV1115 = true", suite)
        self.assertIn("setTimeout(reassertVisiblePanels, 8000)", suite)

    def test_v1115_full_panel_headers_are_real_drag_handles(self):
        suite = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(
            encoding="utf-8"
        )
        preview = (ROOT / "web" / "zzzzzzzzzzzzzz_native_ltx_live_preview_v1115.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function makePanelDraggable(node, handle)", suite)
        self.assertIn('handle.addEventListener("pointerdown"', suite)
        self.assertIn('window.addEventListener("pointermove"', suite)
        self.assertIn("node.pos = [nextX, nextY]", suite)
        self.assertIn('createHeader("VELVET VICE · POWER LoRA AV", "0 ACTIVE", node)', suite)
        self.assertIn('createHeader("VELVET VICE · OUTPUT STUDIO", "READY", node)', suite)
        self.assertIn("function makePreviewDraggable(node, handle)", preview)

    def test_v1115_release_contains_only_current_frontend_files(self):
        names = sorted(path.name for path in (ROOT / "web").glob("*.js"))
        self.assertEqual(
            names,
            sorted(
                [
                    "00_velvet_vice_design_system_v1115_drag_safe.js",
                    "auto_video_output.js",
                    "final_prompt_preview.js",
                    "prompt_director.js",
                    "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js",
                    "zzzzzzzzzzzzzz_native_ltx_live_preview_v1115.js",
                ]
            ),
        )

    def test_workflows_wire_hub_to_real_controls(self):
        for path in sorted(WORKFLOW_DIR.glob("*v1.*.json")):
            workflow = json.loads(path.read_text(encoding="utf-8"))
            nodes = {node["id"]: node for node in workflow["nodes"]}
            links = {link[0]: link for link in workflow["links"]}
            self.assertEqual(nodes[3730]["type"], "VelvetViceControlHub")
            self.assertEqual(nodes[3729]["type"], "VelvetVicePreflightConsole")
            self.assertEqual(nodes[2196]["type"], "VelvetViceOutputStudio")
            outputs = nodes[3730]["outputs"]
            self.assertEqual(len(outputs[0]["links"]), 2)
            self.assertEqual(len(outputs[1]["links"]), 1)
            self.assertEqual(len(outputs[2]["links"]), 1)
            self.assertEqual(len(outputs[3]["links"]), 1)
            targets = {
                (links[lid][3], links[lid][4])
                for output in outputs[:4]
                for lid in output["links"]
            }
            self.assertIn((3747, 2), targets)
            self.assertIn((3748, 2), targets)
            self.assertIn((4031, 2), targets)
            self.assertIn((4051, 1), targets)
            self.assertIn((3420, 6), targets)

    def test_final_watermark_is_after_fps_router_and_before_encode(self):
        workflow = json.loads(next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json")).read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in workflow["nodes"]}
        links = {link[0]: link for link in workflow["links"]}
        self.assertEqual(nodes[4051]["type"], "VelvetViceWatermarkOverlay")
        self.assertEqual(links[9062][1:5], [3747, 0, 4051, 0])
        self.assertEqual(links[9071][1:5], [3730, 2, 4051, 1])
        self.assertNotIn(9073, links)
        self.assertIsNone(nodes[4051]["inputs"][2]["link"])
        self.assertEqual(links[9079][1:5], [4051, 0, 4042, 0])
        self.assertIsNone(nodes[3420]["inputs"][5]["link"])

    def test_power_lora_disabled_stack_is_exact_passthrough(self):
        model = object()
        clip = object()
        result = LoraStudio().apply_loras(model, clip, '[{"enabled": false, "lora": "None", "mode": "AUDIO"}]')
        self.assertIs(result[0], model)
        self.assertIs(result[1], clip)

    def test_power_lora_stack_is_ordered_and_sanitized(self):
        parsed = LoraStudio._parse_stack(
            '[{"enabled": true, "lora": "A.safetensors", "mode": "audio", "video_strength": 9, "audio_strength": 0.8, "clip_strength": -9}]'
        )
        self.assertEqual(parsed[0]["mode"], "AUDIO")
        self.assertEqual(parsed[0]["video_strength"], 4.0)
        self.assertEqual(parsed[0]["audio_strength"], 0.8)
        self.assertEqual(parsed[0]["clip_strength"], -4.0)
        self.assertEqual(LoraStudio._parse_stack("not-json"), [])

    def test_ltx_key_classifier_separates_directional_cross_attention(self):
        self.assertEqual(LoraStudio._key_family("blocks.0.audio_attn1.to_q.lora_up.weight"), "audio")
        self.assertEqual(LoraStudio._key_family("blocks.0.video_to_audio_attn.to_q.lora_up.weight"), "audio")
        self.assertEqual(LoraStudio._key_family("blocks.0.audio_to_video_attn.to_q.lora_up.weight"), "video")
        self.assertEqual(LoraStudio._key_family("blocks.0.attn1.to_q.lora_up.weight"), "video")
        report = LoraStudio.analyze_keys([
            "blocks.0.attn1.to_q.lora_up.weight",
            "blocks.0.audio_attn1.to_q.lora_up.weight",
        ])
        self.assertEqual(report["kind"], "A+V")
        self.assertTrue(report["audio_supported"])

    def test_adaptive_output_service_nodes_do_not_block_portrait_growth(self):
        path = next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json"))
        workflow = json.loads(path.read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in workflow["nodes"]}
        self.assertEqual(nodes[2182]["pos"], [7080, 1920])
        self.assertEqual(nodes[4039]["pos"], [7080, 2000])
        self.assertLess(nodes[2182]["pos"][0] + nodes[2182]["size"][0], nodes[2196]["pos"][0])

    def test_v11_replaces_foreign_lora_chain(self):
        path = next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json"))
        workflow = json.loads(path.read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in workflow["nodes"]}
        self.assertEqual(nodes[4050]["type"], "VelvetVicePowerLoraAV")
        self.assertNotIn(3705, nodes)
        self.assertNotIn(3723, nodes)
        self.assertNotIn(3724, nodes)
        self.assertEqual(nodes[4050]["outputs"][0]["links"], [8113])
        self.assertEqual(nodes[4050]["outputs"][1]["links"], [8114, 8115])

    def test_output_backend_emits_authoritative_geometry(self):
        module = __import__(OutputStudio.__module__, fromlist=["_image_preview_metadata"])
        class FakeImages:
            shape = (97, 1920, 1080, 3)
        meta = module._image_preview_metadata(FakeImages(), 24)
        self.assertEqual(meta["width"], 1080)
        self.assertEqual(meta["height"], 1920)
        self.assertEqual(meta["orientation"], "PORTRAIT")
        self.assertAlmostEqual(meta["ratio"], 1080 / 1920)

    def test_director_and_render_core_remain_registered(self):
        for path in sorted(WORKFLOW_DIR.glob("*v1.*.json")):
            workflow = json.loads(path.read_text(encoding="utf-8"))
            nodes = {node["id"]: node for node in workflow["nodes"]}
            self.assertEqual(nodes[4035]["type"], "VelvetViceLTXPromptDirector")
            self.assertEqual(nodes[3678]["type"], "LTXDirector")
            self.assertEqual(
                nodes[3676]["type"],
                "7df62195-cb50-4fb2-bd93-7bcfde31b12d",
            )

    def test_workflow_links_have_registered_endpoints(self):
        for path in sorted(WORKFLOW_DIR.glob("*v1.*.json")):
            workflow = json.loads(path.read_text(encoding="utf-8"))
            node_ids = {node["id"] for node in workflow["nodes"]}
            link_ids = {link[0] for link in workflow["links"]}
            for link in workflow["links"]:
                self.assertIn(link[1], node_ids, f"{path.name}: origin of link {link[0]}")
                self.assertIn(link[3], node_ids, f"{path.name}: target of link {link[0]}")
            for node in workflow["nodes"]:
                for item in node.get("inputs", []):
                    if item.get("link") is not None:
                        self.assertIn(item["link"], link_ids, f"{path.name}: input on node {node['id']}")
                for item in node.get("outputs", []):
                    for link_id in item.get("links") or []:
                        self.assertIn(link_id, link_ids, f"{path.name}: output on node {node['id']}")

            for graph in workflow.get("definitions", {}).get("subgraphs", []):
                graph_node_ids = {node["id"] for node in graph.get("nodes", [])} | {-10, -20}
                graph_link_ids = {link["id"] for link in graph.get("links", [])}
                for link in graph.get("links", []):
                    self.assertIn(link["origin_id"], graph_node_ids, f"{path.name}: subgraph origin")
                    self.assertIn(link["target_id"], graph_node_ids, f"{path.name}: subgraph target")
                for node in graph.get("nodes", []):
                    for item in node.get("inputs", []):
                        if item.get("link") is not None:
                            self.assertIn(item["link"], graph_link_ids, f"{path.name}: subgraph input")
                    for item in node.get("outputs", []):
                        for link_id in item.get("links") or []:
                            self.assertIn(link_id, graph_link_ids, f"{path.name}: subgraph output")

    def test_ltx25_uses_official_gemma4_prompt_enhancer_after_velvet_director(self):
        path = next(WORKFLOW_DIR.glob("VELVET_VICE_LTX25_v1.2.7.json"))
        workflow = json.loads(path.read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in workflow["nodes"]}
        links = {link[0]: link for link in workflow["links"]}
        loadout = nodes[3319]
        loadout_graph = next(
            graph
            for graph in workflow["definitions"]["subgraphs"]
            if graph["id"] == loadout["type"]
        )
        loadout_nodes = {node["id"]: node for node in loadout_graph["nodes"]}
        loadout_links = {link["id"]: link for link in loadout_graph["links"]}

        self.assertEqual(nodes[4035]["type"], "VelvetViceLTXPromptDirector")
        self.assertNotIn(4053, nodes)
        self.assertEqual(nodes[4054]["type"], "TextGenerateLTX2Prompt")
        self.assertEqual(nodes[4055]["type"], "ComfySwitchNode")
        self.assertEqual(loadout_nodes[4034]["type"], "CLIPLoader")
        self.assertEqual(
            loadout_nodes[4034]["widgets_values"][0],
            "LTX 2.5\\gemma4_e2b_it_bf16.safetensors",
        )
        self.assertNotIn("proxyWidgets", loadout["properties"])
        self.assertEqual(len(loadout["inputs"]), 19)
        self.assertEqual(loadout["inputs"][17]["name"], "clip_name_1")
        self.assertEqual(loadout["inputs"][17]["label"], "Prompt Enhancer Model")
        self.assertEqual(
            loadout["widgets_values"][17],
            "LTX 2.5\\gemma4_e2b_it_bf16.safetensors",
        )
        self.assertEqual(loadout["inputs"][18]["name"], "prompt_enhancer_enabled")
        self.assertEqual(loadout["inputs"][18]["label"], "Prompt Enhancer ON / OFF")
        self.assertTrue(loadout["widgets_values"][18])
        self.assertEqual(len(loadout_graph["inputs"]), 19)
        self.assertEqual(loadout_graph["inputs"][17]["name"], "clip_name_1")
        self.assertEqual(loadout_graph["inputs"][17]["linkIds"], [9103])
        self.assertEqual(loadout_graph["inputs"][18]["name"], "prompt_enhancer_enabled")
        self.assertEqual(loadout_graph["inputs"][18]["linkIds"], [9104])
        self.assertEqual(loadout_nodes[4034]["inputs"][0]["link"], 9103)
        self.assertEqual(loadout_links[9103]["origin_id"], -10)
        self.assertEqual(loadout_links[9103]["origin_slot"], 17)
        self.assertEqual(loadout_links[9103]["target_id"], 4034)
        self.assertEqual(loadout_links[9103]["target_slot"], 0)
        self.assertEqual(loadout["outputs"][9]["name"], "PROMPT_ENHANCER_CLIP")
        self.assertEqual(loadout["outputs"][9]["links"], [9080])
        self.assertEqual(loadout_graph["outputs"][9]["linkIds"], [9034])
        self.assertEqual(loadout_links[9034]["origin_id"], 4034)
        self.assertEqual(loadout_links[9034]["target_id"], -20)
        self.assertEqual(loadout_links[9034]["target_slot"], 9)
        self.assertEqual(loadout_nodes[4200]["type"], "PrimitiveBoolean")
        self.assertEqual(loadout_nodes[4200]["inputs"][0]["type"], "BOOLEAN")
        self.assertEqual(loadout_nodes[4200]["inputs"][0]["widget"], {"name": "value"})
        self.assertEqual(
            loadout_nodes[4200]["properties"]["Node name for S&R"],
            "PrimitiveBoolean",
        )
        self.assertTrue(loadout_nodes[4200]["widgets_values"][0])
        self.assertEqual(loadout_nodes[4200]["inputs"][0]["link"], 9104)
        self.assertEqual(loadout_nodes[4200]["outputs"][0]["links"], [9105])
        self.assertEqual(loadout_links[9104]["origin_id"], -10)
        self.assertEqual(loadout_links[9104]["origin_slot"], 18)
        self.assertEqual(loadout_links[9104]["target_id"], 4200)
        self.assertEqual(loadout_links[9105]["origin_id"], 4200)
        self.assertEqual(loadout_links[9105]["target_id"], -20)
        self.assertEqual(loadout_links[9105]["target_slot"], 10)
        self.assertEqual(loadout["outputs"][10]["name"], "PROMPT_ENHANCER_ENABLED")
        self.assertEqual(loadout["outputs"][10]["links"], [9086])
        self.assertEqual(loadout_graph["outputs"][10]["linkIds"], [9105])
        self.assertTrue(nodes[4055]["widgets_values"][0])
        self.assertEqual(links[9080][1:5], [3319, 9, 4054, 0])
        self.assertEqual(links[9081][1:5], [3751, 0, 4054, 1])
        self.assertEqual(links[9082][1:5], [4036, 0, 4054, 4])
        self.assertEqual(links[9083][1:5], [4054, 0, 4055, 1])
        self.assertEqual(links[9084][1:5], [4036, 0, 4055, 0])
        self.assertEqual(links[9085][1:5], [4055, 0, 4043, 0])
        self.assertEqual(links[9086][1:5], [3319, 10, 4055, 2])
        self.assertEqual(nodes[4055]["inputs"][2]["link"], 9086)
        self.assertTrue(nodes[4055]["flags"]["collapsed"])
        self.assertEqual(nodes[3523]["type"], "CLIPTextEncode")
        self.assertNotIn(9080, nodes[3523]["inputs"][0].values())

    def test_ltx25_profile_requires_prompt_enhancer_model(self):
        profiles = __import__(
            f"{PACKAGE.__name__}.model_profiles",
            fromlist=["required_models"],
        )
        entries = list(profiles.required_models("2.5"))
        self.assertIn(
            (
                "Prompt enhancer",
                "LTX 2.5/gemma4_e2b_it_bf16.safetensors",
                ("text_encoders", "clip"),
                True,
            ),
            entries,
        )



    def test_power_lora_search_v131_replaces_stale_panel(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('const uiVersion = "1.1.15-draggable-single-header"', script)
        self.assertIn('startsWith("vv_power_lora_surface")', script)
        self.assertIn('node.__vvPowerLoraVersion === uiVersion', script)
        self.assertIn('vv_power_lora_surface_v1115', script)
        self.assertIn('surfaceWidgets(node, "vv_power_lora_surface").length === 1', script)
        self.assertIn('::-webkit-inner-spin-button', script)
        self.assertIn('min-width:70px', script)
        self.assertIn('input.placeholder = "Search LoRA…"', script)


    def test_single_header_and_port_gutter_v131(self):
        design = (ROOT / "web" / "00_velvet_vice_design_system_v1115_drag_safe.js").read_text(encoding="utf-8")
        suite = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        workflow = json.loads(next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json")).read_text(encoding="utf-8"))
        self.assertIn('FULL_PANEL_TYPES', design)
        self.assertIn('type.includes("note")', design)
        self.assertIn('node.getTitle = function() { return "\u200B"; }', design)
        self.assertIn('const noTitle = globalThis.LiteGraph?.NO_TITLE ?? 1', design)
        self.assertIn('Object.defineProperty(node, "title_mode"', design)
        self.assertIn('node.slot_start_y = Math.max', suite)
        self.assertIn('result[0] += isInput ? -24 : 24', suite)
        self.assertIn('const safeHeaderY = 72', suite)
        self.assertIn('const minimumY = safeHeaderY', suite)
        self.assertIn('PROMPT_DIRECTOR_TYPE', suite)
        for node in workflow["nodes"]:
            if node.get("type") == "MarkdownNote":
                text = (node.get("widgets_values") or [""])[0]
                self.assertFalse(str(text).lstrip().startswith("#"))


    def test_power_lora_inline_search_v131(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('const uiVersion = "1.1.15-draggable-single-header"', script)
        self.assertIn('vv-lora-picker-popup', script)
        self.assertIn('function render()', script)
        self.assertIn('const createLoraPicker = (slot, index) =>', script)
        self.assertIn('event.key === "ArrowDown"', script)
        self.assertIn('event.key === "Enter"', script)
        self.assertIn('document.body.appendChild(popup)', script)
        self.assertNotIn('searchIcon.textContent = "SEARCH"', script)


    def test_live_lora_catalog_backend_and_frontend_contract(self):
        module = __import__(LoraStudio.__module__, fromlist=["get_lora_catalog"])
        report = module.get_lora_catalog()
        self.assertTrue(report["ok"])
        self.assertIsInstance(report["items"], list)
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('/velvet_vice/ltx/lora/catalog', script)
        self.assertIn('refreshCatalog', script)
        self.assertIn('renderPicker(true, "")', script)
        self.assertIn('input.addEventListener("focus", async', script)
        self.assertIn('input.addEventListener("input", async', script)

    def test_power_lora_cache_is_bounded(self):
        self.assertLessEqual(LoraStudio.MAX_CACHE_ITEMS, 8)
        self.assertGreaterEqual(LoraStudio.MAX_CACHE_ITEMS, 0)

    def test_public_rc_has_valid_default_reference_asset(self):
        workflow = json.loads(next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json")).read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in workflow["nodes"]}
        self.assertEqual(nodes[3751]["widgets_values"][0], "Velvet_Vice_Reference_Demo.png")
        self.assertTrue((PACKAGE_ROOT / "03_ASSETS" / "Velvet_Vice_Reference_Demo.png").is_file())

    def test_preflight_accepts_selected_models_and_active_loras(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('selected_models: graphSelectedModels()', script)
        self.assertIn('add("Prompt enhancer", 17, ["text_encoders", "clip"], true)', script)
        self.assertIn('add("Spatial upscaler", 4, ["latent_upscale_models", "upscale_models"], true)', script)
        self.assertIn('add("Audio VAE", 5, ["vae", "audio_encoders"], true)', script)
        self.assertIn('add("Full video VAE", 6, ["vae"], true)', script)
        self.assertNotIn('filename: "LTX 2.5/gemma4_e2b_it_bf16.safetensors"', script)
        self.assertIn('active_loras: graphActiveLoras()', script)
        self.assertIn('ollama_required: graphPromptMode() !== "MANUAL"', script)

    def test_output_uses_centered_player_shell(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('playerShell.className = "vv-player-shell"', script)
        self.assertIn('playerShell.appendChild(videoFrame)', script)
        self.assertIn('playerShell.style.setProperty("block-size"', script)
    def test_watermark_source_is_mirrored_to_control_hub(self):
        js_path = ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js"
        source = js_path.read_text(encoding="utf-8")
        self.assertIn('const WATERMARK_SOURCE_EVENT = "velvet-vice-watermark-source-changed"', source)
        self.assertIn('setWidget(hub, "watermark_file", selected)', source)
        self.assertIn('sourceCaption.textContent = "Selected watermark"', source)
        self.assertIn('syncWatermarkSource(selected);', source)


    def test_adaptive_player_v135_replaces_stale_frontends_and_uses_mp4_geometry(self):
        script = (ROOT / "web" / "zzzzzzzzzzzzz_velvet_vice_suite_v1115.js").read_text(encoding="utf-8")
        self.assertIn('const OUTPUT_STUDIO_VERSION = "1.1.15-draggable-single-header"', script)
        self.assertIn('function removeStaleOutputStudio(node)', script)
        self.assertIn('node.__vvOutputVersion === OUTPUT_STUDIO_VERSION', script)
        self.assertIn('"vv_output_studio_surface_v1115"', script)
        self.assertIn('currentSurfaces.length === 1', script)
        self.assertIn('setTimeout(reassertVisiblePanels, 6000)', script)
        self.assertNotIn('if (node.__vvOutputInstalled) return;', script)
        self.assertIn('node.__vvPendingPreviewMeta = null', script)
        self.assertIn('The MP4 container is the final authority', script)
        self.assertIn('? browserMeta', script)
        self.assertIn('domWidget.previewMeta = authoritative', script)
        self.assertIn('video.addEventListener("resize"', script)
        self.assertIn('"min-width", "max-width", "min-height", "max-height"', script)
        self.assertIn('setTimeout(() => applyPreviewGeometry(authoritative), 700)', script)


    def test_output_group_contains_maximum_adaptive_player_width(self):
        workflow = json.loads(next(WORKFLOW_DIR.glob("VELVET_VICE_LTX23_v1.2.7.json")).read_text(encoding="utf-8"))
        groups = {group["id"]: group for group in workflow["groups"]}
        nodes = {node["id"]: node for node in workflow["nodes"]}
        output_group = groups[7]["bounding"]
        output_node = nodes[2196]
        group_right = output_group[0] + output_group[2]
        maximum_player_node_right = output_node["pos"][0] + 840
        self.assertGreaterEqual(group_right, maximum_player_node_right + 40)


if __name__ == "__main__":
    unittest.main()
