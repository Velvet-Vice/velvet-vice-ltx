from ..services.memory_lifecycle import (
    log_memory_snapshot,
    start_render_memory_monitor,
)


class VelvetViceLTXLazyModelGate:
    """Loads the LTX render inputs only after Ollama has been released."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"forceInput": True}),
                "model": ("MODEL", {"lazy": True}),
                "clip": ("CLIP", {"lazy": True}),
                "audio_vae": ("VAE", {"lazy": True}),
                "custom_width": ("INT", {"lazy": True}),
                "custom_height": ("INT", {"lazy": True}),
            },
            "optional": {
                "memory_policy": (
                    "VELVET_VICE_MEMORY_POLICY",
                    {"forceInput": True},
                ),
            }
        }

    RETURN_TYPES = (
        "STRING",
        "MODEL",
        "CLIP",
        "VAE",
        "INT",
        "INT",
    )
    RETURN_NAMES = (
        "prompt",
        "model",
        "clip",
        "audio_vae",
        "custom_width",
        "custom_height",
    )
    FUNCTION = "release_render_inputs"
    CATEGORY = "VELVET VICE/LTX"
    DESCRIPTION = (
        "Enforces prompt-first execution. The LTX model, CLIP, VAE, and "
        "render dimensions remain lazy until Ollama/Qwen has been "
        "released and verified."
    )

    def check_lazy_status(
        self,
        prompt,
        model=None,
        clip=None,
        audio_vae=None,
        custom_width=None,
        custom_height=None,
        memory_policy=None,
    ):
        del prompt
        if any(
            value is None
            for value in (
                model,
                clip,
                audio_vae,
                custom_width,
                custom_height,
            )
        ) and not getattr(self, "_monitor_started", False):
            policy = (
                memory_policy
                if isinstance(memory_policy, dict)
                and memory_policy.get("schema")
                == "VELVET_VICE_MEMORY_POLICY"
                else {}
            )
            start_render_memory_monitor(
                policy.get("monitor_interval_seconds", 1.0),
                policy.get("warning_ram_percent", 90.0),
                policy.get("critical_ram_percent", 96.0),
            )
            self._monitor_started = True
            log_memory_snapshot("before lazy LTX input resolution")
        values = {
            "model": model,
            "clip": clip,
            "audio_vae": audio_vae,
            "custom_width": custom_width,
            "custom_height": custom_height,
        }
        return [
            name for name, value in values.items() if value is None
        ]

    def release_render_inputs(
        self,
        prompt,
        model,
        clip,
        audio_vae,
        custom_width,
        custom_height,
        memory_policy=None,
    ):
        del memory_policy
        log_memory_snapshot("after lazy LTX input resolution")
        print(
            "[VELVET VICE] Prompt-first gate completed. "
            "LTX render inputs may load now."
        )
        self._monitor_started = False
        return (
            prompt,
            model,
            clip,
            audio_vae,
            custom_width,
            custom_height,
        )
