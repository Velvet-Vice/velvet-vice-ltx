import sys
import types
import unittest
from unittest.mock import patch

from services import memory_lifecycle


class FakeModelManagement(types.ModuleType):
    def __init__(self):
        super().__init__("comfy.model_management")
        self.calls = []

    def loaded_models(self):
        self.calls.append("loaded_models")
        return [object(), object()]

    def unload_all_models(self):
        self.calls.append("unload_all_models")

    def soft_empty_cache(self, *args, **kwargs):
        self.calls.append("soft_empty_cache")


class MemoryLifecycleTests(unittest.TestCase):
    def test_pre_qwen_unload_uses_comfy_model_management(self):
        fake_comfy = types.ModuleType("comfy")
        fake_management = FakeModelManagement()
        fake_comfy.model_management = fake_management

        with patch.dict(
            sys.modules,
            {
                "comfy": fake_comfy,
                "comfy.model_management": fake_management,
            },
        ), patch.object(
            memory_lifecycle,
            "log_memory_snapshot",
            side_effect=lambda label: memory_lifecycle.MemorySnapshot(
                label,
                None,
                None,
                None,
                None,
                None,
            ),
        ), patch.object(memory_lifecycle.gc, "collect") as collect:
            result = (
                memory_lifecycle.unload_comfy_models_before_ollama()
            )

        self.assertEqual(result.loaded_model_count, 2)
        self.assertEqual(
            fake_management.calls,
            [
                "loaded_models",
                "unload_all_models",
                "soft_empty_cache",
            ],
        )
        collect.assert_called_once_with()

    def test_final_cleanup_uses_comfy_model_management(self):
        fake_comfy = types.ModuleType("comfy")
        fake_management = FakeModelManagement()
        fake_comfy.model_management = fake_management

        with patch.dict(
            sys.modules,
            {
                "comfy": fake_comfy,
                "comfy.model_management": fake_management,
            },
        ), patch.object(
            memory_lifecycle,
            "log_memory_snapshot",
            side_effect=lambda label: memory_lifecycle.MemorySnapshot(
                label,
                None,
                None,
                None,
                None,
                None,
            ),
        ), patch.object(memory_lifecycle.gc, "collect") as collect:
            result = memory_lifecycle.cleanup_comfy_models_after_render()

        self.assertEqual(result.loaded_model_count, 2)
        self.assertEqual(
            fake_management.calls,
            [
                "loaded_models",
                "unload_all_models",
                "soft_empty_cache",
            ],
        )
        collect.assert_called_once_with()

    def test_pre_decode_unload_uses_comfy_model_management(self):
        fake_comfy = types.ModuleType("comfy")
        fake_management = FakeModelManagement()
        fake_comfy.model_management = fake_management

        with patch.dict(
            sys.modules,
            {
                "comfy": fake_comfy,
                "comfy.model_management": fake_management,
            },
        ), patch.object(
            memory_lifecycle,
            "log_memory_snapshot",
            side_effect=lambda label: memory_lifecycle.MemorySnapshot(
                label,
                None,
                None,
                None,
                None,
                None,
            ),
        ), patch.object(memory_lifecycle.gc, "collect") as collect:
            result = (
                memory_lifecycle.unload_sampling_models_before_decode()
            )

        self.assertEqual(result.loaded_model_count, 2)
        self.assertEqual(
            fake_management.calls,
            [
                "loaded_models",
                "unload_all_models",
                "soft_empty_cache",
            ],
        )
        collect.assert_called_once_with()

    def test_interruption_cleanup_forces_full_vram_release(self):
        fake_comfy = types.ModuleType("comfy")
        fake_management = FakeModelManagement()
        fake_comfy.model_management = fake_management

        with patch.dict(
            sys.modules,
            {
                "comfy": fake_comfy,
                "comfy.model_management": fake_management,
            },
        ), patch.object(
            memory_lifecycle,
            "log_memory_snapshot",
            side_effect=lambda label: memory_lifecycle.MemorySnapshot(
                label,
                None,
                None,
                None,
                None,
                None,
            ),
        ), patch.object(
            memory_lifecycle,
            "stop_render_memory_monitor",
        ) as stop_monitor, patch.object(
            memory_lifecycle.gc,
            "collect",
        ) as collect:
            result = (
                memory_lifecycle.cleanup_comfy_models_after_interruption()
            )

        self.assertEqual(result.loaded_model_count, 2)
        self.assertEqual(
            fake_management.calls,
            [
                "loaded_models",
                "unload_all_models",
                "soft_empty_cache",
            ],
        )
        stop_monitor.assert_called_once_with()
        collect.assert_called_once_with()

    def test_render_monitor_summary_tracks_peaks(self):
        snapshots = [
            memory_lifecycle.MemorySnapshot(
                "one", 72.0, 18.0, 2.0, 20.0, 31.8
            ),
            memory_lifecycle.MemorySnapshot(
                "two", 96.5, 2.2, 40.0, 4.0, 31.8
            ),
        ]
        monitor = memory_lifecycle.RenderMemoryMonitor(10, 90, 96)
        with patch.object(
            memory_lifecycle,
            "take_memory_snapshot",
            side_effect=snapshots,
        ):
            monitor._sample("one")
            monitor._sample("two")

        with monitor._lock:
            self.assertEqual(monitor._peak_ram_percent, 96.5)
            self.assertEqual(monitor._minimum_ram_available_gib, 2.2)
            self.assertEqual(monitor._minimum_vram_free_gib, 4.0)


if __name__ == "__main__":
    unittest.main()
