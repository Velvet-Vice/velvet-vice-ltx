from .nodes import (
    VelvetViceControlHub,
    VelvetViceLoraStudio,
    VelvetVicePowerLoraAV,
    VelvetViceOutputStudio,
    VelvetVicePreflightConsole,
    VelvetViceWatermarkOverlay,
    VelvetViceLTXAudioMemoryCheckpoint,
    VelvetViceLTXAutoVideoCombine,
    VelvetViceLTXAutoVideoCombineV0110,
    VelvetViceLTXAutoVideoCombineV0112,
    VelvetViceLTXAutoVideoCombineV019,
    VelvetViceLTXChunkedImageScaleBy,
    VelvetViceLTXFP16ChunkedImageScaleBy,
    VelvetViceLTXFP16VAEDecode,
    VelvetViceLTXFinalMemoryCleanup,
    VelvetViceLTXFinalPromptPreview,
    VelvetViceLTXLivePreviewDisplay,
    VelvetViceLTXNativePreviewBridge,
    VelvetViceLTXGhostAnalyzer,
    VelvetViceLTXImageMemoryCheckpoint,
    VelvetViceLTXLazyModelGate,
    VelvetViceLTXPreDecodeMemoryGate,
    VelvetViceLTXPromptDirector,
    VelvetViceLTXSingleOutputCleanup,
    VelvetViceLTXSystemCheck,
    VelvetViceLTXTemporalAntiGhost,
    VelvetViceOllamaRelease,
    VelvetViceOllamaReleaseBarrier,
)
from .version import PACK_VERSION, SUPPORTED_LTX_VERSIONS
from .services.interrupt_cleanup import install_interruption_cleanup_hook


NODE_CLASS_MAPPINGS = {
    "VelvetViceControlHub": VelvetViceControlHub,
    "VelvetViceLoraStudio": VelvetViceLoraStudio,
    "VelvetVicePowerLoraAV": VelvetVicePowerLoraAV,
    "VelvetViceOutputStudio": VelvetViceOutputStudio,
    "VelvetVicePreflightConsole": VelvetVicePreflightConsole,
    "VelvetViceWatermarkOverlay": VelvetViceWatermarkOverlay,
    "VelvetViceLTXAudioMemoryCheckpoint": (
        VelvetViceLTXAudioMemoryCheckpoint
    ),
    "VelvetViceLTXAutoVideoCombine": VelvetViceLTXAutoVideoCombine,
    "VelvetViceLTXAutoVideoCombineV0110": (
        VelvetViceLTXAutoVideoCombineV0110
    ),
    "VelvetViceLTXAutoVideoCombineV0112": (
        VelvetViceLTXAutoVideoCombineV0112
    ),
    "VelvetViceLTXAutoVideoCombineV019": (
        VelvetViceLTXAutoVideoCombineV019
    ),
    "VelvetViceLTXChunkedImageScaleBy": (
        VelvetViceLTXChunkedImageScaleBy
    ),
    "VelvetViceLTXFP16ChunkedImageScaleBy": (
        VelvetViceLTXFP16ChunkedImageScaleBy
    ),
    "VelvetViceLTXFP16VAEDecode": VelvetViceLTXFP16VAEDecode,
    "VelvetViceLTXFinalMemoryCleanup": (
        VelvetViceLTXFinalMemoryCleanup
    ),
    "VelvetViceLTXFinalPromptPreview": (
        VelvetViceLTXFinalPromptPreview
    ),
    "VelvetViceLTXLivePreviewDisplay": (
        VelvetViceLTXLivePreviewDisplay
    ),
    "VelvetViceLTXNativePreviewBridge": (
        VelvetViceLTXNativePreviewBridge
    ),
    "VelvetViceLTXGhostAnalyzer": VelvetViceLTXGhostAnalyzer,
    "VelvetViceLTXImageMemoryCheckpoint": (
        VelvetViceLTXImageMemoryCheckpoint
    ),
    "VelvetViceLTXLazyModelGate": VelvetViceLTXLazyModelGate,
    "VelvetViceLTXPreDecodeMemoryGate": (
        VelvetViceLTXPreDecodeMemoryGate
    ),
    "VelvetViceLTXPromptDirector": VelvetViceLTXPromptDirector,
    "VelvetViceLTXSingleOutputCleanup": (
        VelvetViceLTXSingleOutputCleanup
    ),
    "VelvetViceLTXSystemCheck": VelvetViceLTXSystemCheck,
    "VelvetViceLTXTemporalAntiGhost": VelvetViceLTXTemporalAntiGhost,
    "VelvetViceOllamaReleaseBarrier": VelvetViceOllamaReleaseBarrier,
    "VelvetViceOllamaRelease": VelvetViceOllamaRelease,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VelvetViceControlHub": "VELVET VICE — Control Hub",
    "VelvetViceLoraStudio": "VELVET VICE — Legacy LoRA Studio",
    "VelvetVicePowerLoraAV": "VELVET VICE — Power LoRA AV",
    "VelvetViceOutputStudio": "VELVET VICE — Output Studio",
    "VelvetVicePreflightConsole": "VELVET VICE — Preflight Console",
    "VelvetViceWatermarkOverlay": "VELVET VICE — Final Watermark Overlay",
    "VelvetViceLTXAudioMemoryCheckpoint": (
        "VELVET VICE LTX — Audio Memory Checkpoint"
    ),
    "VelvetViceLTXAutoVideoCombine": (
        "VELVET VICE LTX — Auto NVENC Video Output"
    ),
    "VelvetViceLTXAutoVideoCombineV0110": (
        "VELVET VICE LTX — v0.1.10 Fast NVENC Output + Preview"
    ),
    "VelvetViceLTXAutoVideoCombineV0112": (
        "VELVET VICE LTX — v0.1.12 Stable NVENC Output + Preview"
    ),
    "VelvetViceLTXAutoVideoCombineV019": (
        "VELVET VICE LTX — v0.1.9 Verified Auto NVENC Output"
    ),
    "VelvetViceLTXChunkedImageScaleBy": (
        "VELVET VICE LTX — Chunked Image Scale By"
    ),
    "VelvetViceLTXFP16ChunkedImageScaleBy": (
        "VELVET VICE LTX — FP16 Chunked Image Scale By"
    ),
    "VelvetViceLTXFP16VAEDecode": (
        "VELVET VICE LTX — FP16 Full VAE Decode"
    ),
    "VelvetViceLTXFinalMemoryCleanup": (
        "VELVET VICE LTX — Final Memory Cleanup"
    ),
    "VelvetViceLTXFinalPromptPreview": (
        "VELVET VICE LTX — Final Prompt Preview"
    ),
    "VelvetViceLTXLivePreviewDisplay": (
        "VELVET VICE LTX — Live Preview Display"
    ),
    "VelvetViceLTXNativePreviewBridge": (
        "VELVET VICE LTX — Native Preview Bridge"
    ),
    "VelvetViceLTXGhostAnalyzer": (
        "VELVET VICE LTX — Ghost Analyzer"
    ),
    "VelvetViceLTXImageMemoryCheckpoint": (
        "VELVET VICE LTX — Image Memory Checkpoint"
    ),
    "VelvetViceLTXLazyModelGate": (
        "VELVET VICE LTX — Prompt-First Model Gate"
    ),
    "VelvetViceLTXPreDecodeMemoryGate": (
        "VELVET VICE LTX — Pre-Decode Memory Gate"
    ),
    "VelvetViceLTXPromptDirector": (
        "VELVET VICE LTX — Prompt Director"
    ),
    "VelvetViceLTXSingleOutputCleanup": (
        "VELVET VICE LTX — Single Output Cleanup"
    ),
    "VelvetViceLTXSystemCheck": (
        "VELVET VICE LTX — BF16 System Check"
    ),
    "VelvetViceLTXTemporalAntiGhost": (
        "VELVET VICE LTX — Temporal Anti-Ghost"
    ),
    "VelvetViceOllamaReleaseBarrier": (
        "VELVET VICE LTX — Ollama Release Barrier"
    ),
    "VelvetViceOllamaRelease": (
        "VELVET VICE LTX — Ollama RAM/VRAM Release (Legacy)"
    ),
}

WEB_DIRECTORY = "./web"

INTERRUPT_CLEANUP_HOOK_INSTALLED = install_interruption_cleanup_hook()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "PACK_VERSION",
    "SUPPORTED_LTX_VERSIONS",
    "INTERRUPT_CLEANUP_HOOK_INSTALLED",
]
