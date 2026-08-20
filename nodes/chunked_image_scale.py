from __future__ import annotations

from collections.abc import Iterator

from ..services.memory_lifecycle import log_memory_snapshot


UPSCALE_METHODS = (
    "nearest-exact",
    "bilinear",
    "area",
    "bicubic",
    "lanczos",
)


def scaled_dimension(size: int, scale_by: float) -> int:
    """Match ComfyUI ImageScaleBy dimension rounding."""
    return max(1, round(int(size) * float(scale_by)))


def frame_ranges(
    frame_count: int,
    frame_chunk_size: int,
) -> Iterator[tuple[int, int]]:
    chunk_size = max(1, int(frame_chunk_size))
    for start in range(0, max(0, int(frame_count)), chunk_size):
        yield (start, min(start + chunk_size, int(frame_count)))


class VelvetViceLTXChunkedImageScaleBy:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"forceInput": True}),
                "upscale_method": (UPSCALE_METHODS, {"default": "bicubic"}),
                "scale_by": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.01,
                        "max": 8.0,
                        "step": 0.01,
                    },
                ),
                "frame_chunk_size": (
                    "INT",
                    {
                        "default": 4,
                        "min": 1,
                        "max": 64,
                        "step": 1,
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "upscale"
    CATEGORY = "VELVET VICE/LTX"
    DESCRIPTION = (
        "Scales complete frames in small batches with ComfyUI's native "
        "common_upscale routine. It preallocates one output tensor and "
        "never spatially tiles or temporally interpolates the clip."
    )

    def upscale(
        self,
        image,
        upscale_method,
        scale_by,
        frame_chunk_size,
    ):
        if len(image.shape) != 4:
            raise ValueError(
                "VELVET VICE Chunked Image Scale expects an IMAGE tensor "
                "with shape [frames, height, width, channels]."
            )

        frame_count, height, width, channels = image.shape
        target_height = scaled_dimension(height, scale_by)
        target_width = scaled_dimension(width, scale_by)

        if target_height == int(height) and target_width == int(width):
            print(
                "[VELVET VICE] CHUNKED SCALE | bypassed because the "
                "target size matches the input size"
            )
            return (image,)

        try:
            import torch
            from comfy.utils import common_upscale
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE Chunked Image Scale must run inside ComfyUI "
                "with PyTorch and comfy.utils available."
            ) from error

        method = str(upscale_method)
        if method not in UPSCALE_METHODS:
            raise ValueError(
                f"Unsupported upscale method: {method!r}"
            )

        chunk_size = max(1, int(frame_chunk_size))
        output = torch.empty(
            (
                int(frame_count),
                target_height,
                target_width,
                int(channels),
            ),
            device=image.device,
            dtype=image.dtype,
        )

        print(
            "[VELVET VICE] CHUNKED SCALE | "
            f"{int(frame_count)} frame(s), {int(width)}x{int(height)} -> "
            f"{target_width}x{target_height}, {method}, "
            f"{chunk_size} frame(s) per chunk"
        )
        log_memory_snapshot("chunked native quality pass start")

        with torch.inference_mode():
            for start, end in frame_ranges(frame_count, chunk_size):
                source = image[start:end].movedim(-1, 1)
                scaled = common_upscale(
                    source,
                    target_width,
                    target_height,
                    method,
                    "disabled",
                ).movedim(1, -1)
                output[start:end].copy_(scaled)
                del source
                del scaled

        log_memory_snapshot("chunked native quality pass complete")
        return (output,)


class VelvetViceLTXFP16ChunkedImageScaleBy(
    VelvetViceLTXChunkedImageScaleBy
):
    DESCRIPTION = (
        "Scales complete frames in small batches. Each active chunk is "
        "calculated with ComfyUI's native common_upscale routine in FP32 "
        "and written directly into one FP16 output tensor. It never "
        "spatially tiles or temporally interpolates the clip."
    )

    def upscale(
        self,
        image,
        upscale_method,
        scale_by,
        frame_chunk_size,
    ):
        if len(image.shape) != 4:
            raise ValueError(
                "VELVET VICE FP16 Chunked Image Scale expects an IMAGE "
                "tensor with shape [frames, height, width, channels]."
            )

        try:
            import torch
            from comfy.utils import common_upscale
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE FP16 Chunked Image Scale must run inside "
                "ComfyUI with PyTorch and comfy.utils available."
            ) from error

        method = str(upscale_method)
        if method not in UPSCALE_METHODS:
            raise ValueError(
                f"Unsupported upscale method: {method!r}"
            )

        frame_count, height, width, channels = image.shape
        target_height = scaled_dimension(height, scale_by)
        target_width = scaled_dimension(width, scale_by)
        chunk_size = max(1, int(frame_chunk_size))

        if (
            target_height == int(height)
            and target_width == int(width)
            and image.dtype == torch.float16
        ):
            print(
                "[VELVET VICE] FP16 CHUNKED SCALE | zero-copy bypass; "
                "target size and dtype already match"
            )
            return (image,)

        output = torch.empty(
            (
                int(frame_count),
                target_height,
                target_width,
                int(channels),
            ),
            device=image.device,
            dtype=torch.float16,
        )

        print(
            "[VELVET VICE] FP16 CHUNKED SCALE | "
            f"{int(frame_count)} frame(s), {int(width)}x{int(height)} -> "
            f"{target_width}x{target_height}, {method}, "
            f"{chunk_size} frame(s) per chunk, FP32 compute -> FP16 store"
        )
        log_memory_snapshot("FP16 native quality pass start")

        with torch.inference_mode():
            for start, end in frame_ranges(frame_count, chunk_size):
                source = (
                    image[start:end]
                    .movedim(-1, 1)
                    .to(dtype=torch.float32)
                )
                scaled = common_upscale(
                    source,
                    target_width,
                    target_height,
                    method,
                    "disabled",
                ).movedim(1, -1)
                output[start:end].copy_(scaled)
                del source
                del scaled

        log_memory_snapshot("FP16 native quality pass complete")
        return (output,)
