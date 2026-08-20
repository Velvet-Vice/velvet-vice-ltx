import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from services import interrupt_cleanup


class FakePromptExecutor:
    def __init__(self, event="execution_success"):
        self.event = event
        self.status_messages = []

    async def execute_async(self, prompt, prompt_id, *args, **kwargs):
        self.status_messages = [(self.event, {"prompt_id": prompt_id})]
        return "original-result"


class InterruptCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assert_hook = interrupt_cleanup.install_interruption_cleanup_hook(
            FakePromptExecutor
        )

    def test_hook_installs_once(self):
        self.assertTrue(self.assert_hook)
        wrapped = FakePromptExecutor.execute_async
        self.assertTrue(
            interrupt_cleanup.install_interruption_cleanup_hook(
                FakePromptExecutor
            )
        )
        self.assertIs(FakePromptExecutor.execute_async, wrapped)

    def test_interrupted_velvet_prompt_triggers_cleanup(self):
        prompt = {
            "4035": {"class_type": "VelvetViceLTXPromptDirector"},
            "sampler": {"class_type": "KSampler"},
        }
        executor = FakePromptExecutor("execution_interrupted")
        with patch.object(
            interrupt_cleanup,
            "cleanup_comfy_models_after_interruption",
        ) as cleanup:
            result = asyncio.run(
                executor.execute_async(prompt, "prompt-vv")
            )
        self.assertEqual(result, "original-result")
        cleanup.assert_called_once_with()

    def test_successful_velvet_prompt_is_untouched(self):
        prompt = {
            "4035": {"class_type": "VelvetViceLTXPromptDirector"},
        }
        executor = FakePromptExecutor("execution_success")
        with patch.object(
            interrupt_cleanup,
            "cleanup_comfy_models_after_interruption",
        ) as cleanup:
            result = asyncio.run(
                executor.execute_async(prompt, "prompt-success")
            )
        self.assertEqual(result, "original-result")
        cleanup.assert_not_called()

    def test_other_workflow_interruption_is_untouched(self):
        prompt = {"sampler": {"class_type": "KSampler"}}
        executor = FakePromptExecutor("execution_interrupted")
        with patch.object(
            interrupt_cleanup,
            "cleanup_comfy_models_after_interruption",
        ) as cleanup:
            result = asyncio.run(
                executor.execute_async(prompt, "prompt-other")
            )
        self.assertEqual(result, "original-result")
        cleanup.assert_not_called()

    def test_prompt_detection_is_strict_to_velvet_nodes(self):
        self.assertTrue(
            interrupt_cleanup.prompt_uses_velvet_vice(
                {"1": {"class_type": "VelvetViceLTXLazyModelGate"}}
            )
        )

    def test_real_comfy_executor_emits_interrupt_and_runs_cleanup(self):
        package_root = str(Path(__file__).resolve().parents[1])
        removed_paths = [
            path for path in sys.path if path == package_root
        ]
        sys.path[:] = [
            path for path in sys.path if path != package_root
        ]
        try:
            import comfy.model_management as model_management
            import execution
            import nodes
        except ImportError as error:
            self.skipTest(f"ComfyUI runtime is unavailable: {error}")
        finally:
            sys.path[:0] = removed_paths

        class VelvetViceTestInterrupt:
            @classmethod
            def INPUT_TYPES(cls):
                return {"required": {}}

            RETURN_TYPES = ("STRING",)
            FUNCTION = "run"
            OUTPUT_NODE = True

            def run(self):
                model_management.interrupt_current_processing(True)
                model_management.throw_exception_if_processing_interrupted()
                return ("unreachable",)

        class FakeServer:
            client_id = None
            last_node_id = None

            def __init__(self):
                self.messages = []

            def send_sync(self, event, data, client_id=None):
                self.messages.append((event, data, client_id))

        nodes.NODE_CLASS_MAPPINGS[
            "VelvetViceTestInterrupt"
        ] = VelvetViceTestInterrupt
        try:
            self.assertTrue(
                interrupt_cleanup.install_interruption_cleanup_hook(
                    execution.PromptExecutor
                )
            )
            server = FakeServer()
            executor = execution.PromptExecutor(
                server,
                cache_type=execution.CacheType.CLASSIC,
                cache_args={"lru": 0, "ram": 2, "ram_inactive": 2},
            )
            prompt = {
                "1": {
                    "class_type": "VelvetViceTestInterrupt",
                    "inputs": {},
                }
            }
            with patch.object(
                interrupt_cleanup,
                "cleanup_comfy_models_after_interruption",
            ) as cleanup:
                executor.execute(prompt, "real-interrupt", {}, ["1"])
            cleanup.assert_called_once_with()
            self.assertTrue(
                any(
                    event == "execution_interrupted"
                    for event, _ in executor.status_messages
                )
            )
            self.assertFalse(executor.success)
        finally:
            nodes.NODE_CLASS_MAPPINGS.pop(
                "VelvetViceTestInterrupt",
                None,
            )
            model_management.interrupt_current_processing(False)
        self.assertFalse(
            interrupt_cleanup.prompt_uses_velvet_vice(
                {"1": {"class_type": "KSampler"}}
            )
        )


if __name__ == "__main__":
    unittest.main()
