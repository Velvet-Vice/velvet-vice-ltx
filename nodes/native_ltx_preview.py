from __future__ import annotations

import base64
import logging
import time
from io import BytesIO
from typing import Any


EVENT_NAME = "velvet_vice.ltx_live_preview"
WRAPPER_KEY = "velvet_vice_native_ltx_live_preview"
MIN_PLAYBACK_FPS = 24.0
MAX_BUFFERED_FRAMES = 24
LTX_TEMPORAL_COMPRESSION = 8


def _pass_number(node_id: Any) -> int | None:
    """Map the protected three sampler IDs to their visible pass number."""
    leaf = str(node_id or "").split(":")[-1]
    return {"3650": 1, "3649": 2, "3656": 3}.get(leaf)


def _latent_format_from_guider(guider):
    model_patcher = getattr(guider, "model_patcher", None)
    model = getattr(model_patcher, "model", None)
    latent_format = getattr(model, "latent_format", None)
    factors = getattr(latent_format, "latent_rgb_factors", None)
    if latent_format is None or factors is None:
        raise RuntimeError(
            "The active model does not expose ComfyUI latent RGB preview factors."
        )
    return latent_format


def _unwrap_upscale_model(latent_upscale_model):
    return getattr(latent_upscale_model, "model", latent_upscale_model)


class _NativePreviewOuterWrapper:
    """Stream an aspect-safe LTX preview without changing sampler outputs.

    Each sampler callback produces the complete current temporal frame buffer.
    The browser plays that buffer at 24-60 FPS until the next sampler callback
    arrives. The already connected fast preview VAE decodes useful image detail
    at the workflow's preview resolution instead of enlarging a 16x24 latent
    projection. Any preview-side failure falls back to a safe projection or
    disables only the optional preview while sampling continues unchanged.
    """

    def __init__(
        self,
        *,
        preview_rate: float,
        jpeg_quality: int,
        max_edge: int,
        latent_upscale_model=None,
        vae=None,
    ):
        self.preview_rate = max(MIN_PLAYBACK_FPS, min(60.0, float(preview_rate)))
        self.jpeg_quality = max(85, min(95, int(jpeg_quality)))
        self.max_edge = max(512, min(1024, int(max_edge)))
        self.latent_upscale_model = latent_upscale_model
        self.vae = vae
        self._last_emit = 0.0
        self._factor_cache = {}
        self._preview_disabled = False
        self._warning_emitted = False
        self._vae_warning_emitted = False
        self._first_event_logged = False

    def _factor_tensors(self, torch, x0, latent_format):
        key = (id(latent_format), str(x0.dtype), str(x0.device))
        cached = self._factor_cache.get(key)
        if cached is not None:
            return cached

        factors = getattr(latent_format, "latent_rgb_factors", None)
        bias = getattr(latent_format, "latent_rgb_factors_bias", None)
        if factors is None:
            raise RuntimeError("No latent RGB preview factors are available.")

        # ComfyUI's current LTXAV table is the half-scale form of the factors
        # used by the former LTX 2.x preview. Doubling the linear projection
        # and applying sigmoid restores that proven preview colour response.
        factor_tensor = (
            torch.as_tensor(factors, device=x0.device, dtype=x0.dtype)
            .transpose(0, 1)
            .mul(2.0)
        )
        bias_tensor = (
            None
            if bias is None
            else torch.as_tensor(bias, device=x0.device, dtype=x0.dtype).mul(2.0)
        )
        if int(factor_tensor.shape[1]) != int(x0.shape[1]):
            raise RuntimeError(
                "Latent preview factor channels do not match the sampled latent."
            )
        self._factor_cache[key] = (factor_tensor, bias_tensor)
        return factor_tensor, bias_tensor

    @staticmethod
    def _even_frame_indices(count, device):
        import torch

        if count <= MAX_BUFFERED_FRAMES:
            return None
        return torch.linspace(
            0,
            count - 1,
            steps=MAX_BUFFERED_FRAMES,
            device=device,
        ).round().long()

    @staticmethod
    def _timeline_frame_count(x0):
        """Return the represented video-frame count without altering samples.

        LTX temporal latents encode one starting frame plus eight video frames
        for every following latent. The browser therefore must not present the
        buffered latent images themselves at 24 FPS: doing so compresses an
        eight-second clip into roughly one second.
        """
        if getattr(x0, "is_nested", False):
            x0 = x0.tensors[0]
        if getattr(x0, "ndim", 0) == 5:
            latent_frames = max(1, int(x0.shape[2]))
            return (latent_frames - 1) * LTX_TEMPORAL_COMPRESSION + 1
        if getattr(x0, "ndim", 0) == 4:
            return max(1, int(x0.shape[0]))
        return 1

    @classmethod
    def _prepare_video_frames(cls, x0, latent_format):
        if getattr(x0, "is_nested", False):
            x0 = x0.tensors[0]
        reshape = getattr(latent_format, "latent_rgb_factors_reshape", None)
        if callable(reshape):
            x0 = reshape(x0)
        if x0.ndim == 5:
            # Preserve batch-major temporal ordering: [B,C,T,H,W] -> [B*T,C,H,W].
            x0 = x0.movedim(2, 1)
            x0 = x0.reshape((-1,) + x0.shape[-3:])
        if x0.ndim != 4 or x0.shape[0] <= 0:
            return None
        indices = cls._even_frame_indices(int(x0.shape[0]), x0.device)
        if indices is not None:
            x0 = x0.index_select(0, indices)
        return x0

    @classmethod
    def _prepare_vae_samples(cls, x0):
        """Turn [B,C,T,H,W] into independent one-frame VAE samples.

        Decoding one latent frame at a time avoids the temporal expansion and
        memory cost of a full video decode while still using the preview VAE's
        learned spatial reconstruction. Frames are sampled evenly when a
        sampler buffer is longer than one second at the minimum playback rate.
        """
        import torch

        if getattr(x0, "is_nested", False):
            x0 = x0.tensors[0]
        if x0.ndim == 5:
            batch, channels, frames, height, width = x0.shape
            x0 = x0.permute(0, 2, 1, 3, 4).reshape(
                batch * frames, channels, 1, height, width
            )
        elif x0.ndim == 4:
            x0 = x0.unsqueeze(2)
        else:
            return None
        if int(x0.shape[0]) <= 0:
            return None
        indices = cls._even_frame_indices(int(x0.shape[0]), x0.device)
        if indices is not None:
            x0 = x0.index_select(0, indices)
        return x0

    @staticmethod
    def _normalize_decoded(decoded):
        """Normalize ComfyUI VAE results to [frames,height,width,channels]."""
        if isinstance(decoded, (tuple, list)):
            decoded = decoded[0]
        if decoded is None:
            return None
        if decoded.ndim == 5:
            if int(decoded.shape[-1]) in (3, 4):
                decoded = decoded.reshape((-1,) + tuple(decoded.shape[-3:]))
            elif int(decoded.shape[1]) in (3, 4):
                batch, channels, frames, height, width = decoded.shape
                decoded = decoded.permute(0, 2, 3, 4, 1).reshape(
                    batch * frames, height, width, channels
                )
        elif decoded.ndim == 4 and int(decoded.shape[1]) in (3, 4):
            decoded = decoded.movedim(1, -1)
        if decoded.ndim != 4 or int(decoded.shape[-1]) not in (3, 4):
            raise RuntimeError("The preview VAE returned an unsupported image shape.")
        return decoded[..., :3].float().clamp(0.0, 1.0)

    def _decode_with_preview_vae(self, x0):
        if self.vae is None:
            return None
        try:
            import torch

            samples = self._prepare_vae_samples(x0)
            if samples is None:
                return None
            with torch.inference_mode():
                decoded = self.vae.decode(samples)
            return self._normalize_decoded(decoded)
        except Exception as error:
            if not self._vae_warning_emitted:
                self._vae_warning_emitted = True
                logging.warning(
                    "VELVET VICE Live Preview VAE decode failed (%s); "
                    "preview continues with the safe latent projection.",
                    error,
                    exc_info=True,
                )
            return None

    def _fit_preview_edge(self, decoded):
        import torch.nn.functional as F

        height = int(decoded.shape[1])
        width = int(decoded.shape[2])
        longest = max(height, width)
        if longest == self.max_edge:
            return decoded
        scale = self.max_edge / float(max(1, longest))
        target_h = max(1, round(height * scale))
        target_w = max(1, round(width * scale))
        return F.interpolate(
            decoded.permute(0, 3, 1, 2),
            size=(target_h, target_w),
            mode="bicubic",
            align_corners=False,
            antialias=True,
        ).permute(0, 2, 3, 1).clamp(0.0, 1.0)

    def _decode_frames(self, x0, latent_format):
        import torch
        import torch.nn.functional as F

        decoded = self._decode_with_preview_vae(x0)
        if decoded is not None:
            return self._fit_preview_edge(decoded), True

        frames = self._prepare_video_frames(x0, latent_format)
        if frames is None:
            return None, False

        factors, bias = self._factor_tensors(torch, frames, latent_format)
        decoded = torch.sigmoid(
            F.linear(frames.movedim(1, -1), factors, bias=bias)
        )

        return self._fit_preview_edge(decoded), False

    def _encode_frames(self, decoded):
        import torch
        from PIL import Image

        previews = decoded.mul(255).to(device="cpu", dtype=torch.uint8)
        encoded = []
        width = 0
        height = 0
        for preview in previews:
            image = Image.fromarray(preview.numpy())
            width = int(image.width)
            height = int(image.height)
            buffer = BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=self.jpeg_quality,
                optimize=False,
            )
            encoded.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
        return encoded, width, height

    def _emit_preview(self, x0, *, latent_format, step, total_steps):
        try:
            from server import PromptServer
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE Live Preview must run inside ComfyUI."
            ) from error

        now = time.monotonic()
        is_last_step = int(step) + 1 >= int(total_steps)
        if self._last_emit and now - self._last_emit < 0.12 and not is_last_step:
            return
        self._last_emit = now

        timeline_frame_count = self._timeline_frame_count(x0)
        decoded, used_preview_vae = self._decode_frames(x0, latent_format)
        if decoded is None:
            return
        images, width, height = self._encode_frames(decoded)
        if not images:
            return
        timeline_duration_seconds = timeline_frame_count / self.preview_rate
        source_playback_fps = len(images) / max(
            timeline_duration_seconds,
            1.0 / self.preview_rate,
        )

        server = PromptServer.instance
        node_id = getattr(server, "last_node_id", None)
        payload = {
            # Keep the original single-image field for a browser tab that still
            # has the v1.1.8 frontend cached. The v1.1.10 frontend consumes the
            # complete frame buffer below.
            "image": images[0],
            "images": images,
            "mime": "image/jpeg",
            "width": width,
            "height": height,
            "frame_index": 0,
            "frame_count": len(images),
            # playback_fps stays available for cached v1.1.11 tabs. The v1.1.12
            # frontend uses source_playback_fps so the sampled images span the
            # real 24 FPS LTX video duration instead of racing through them.
            "playback_fps": self.preview_rate,
            "source_playback_fps": max(0.5, min(60.0, source_playback_fps)),
            "timeline_fps": self.preview_rate,
            "timeline_frame_count": timeline_frame_count,
            "timeline_duration_seconds": timeline_duration_seconds,
            "temporal_compression": LTX_TEMPORAL_COMPRESSION,
            "jpeg_quality": self.jpeg_quality,
            "used_preview_vae": used_preview_vae,
            # Compatibility for a browser tab that still has the v1.1.10
            # frontend cached. The learned latent upscaler is intentionally not
            # activated by v1.1.11 because the connected TAE is the decoder.
            "used_latent_upscaler": False,
            "node": str(node_id or ""),
            "pass": _pass_number(node_id),
            "step": int(step) + 1,
            "steps": int(total_steps),
            "timestamp": time.time(),
        }
        server.send_sync(
            EVENT_NAME,
            payload,
            getattr(server, "client_id", None),
        )
        if not self._first_event_logged:
            self._first_event_logged = True
            logging.info(
                "VELVET VICE Live Preview streaming %d source frame(s) at "
                "%dx%d over a %.2f second / %.0f FPS timeline.",
                len(images),
                width,
                height,
                timeline_duration_seconds,
                self.preview_rate,
            )

    def __call__(
        self,
        executor,
        noise,
        latent_image,
        sampler,
        sigmas,
        denoise_mask,
        callback,
        disable_pbar,
        seed,
        latent_shapes,
    ):
        try:
            import torch
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE Live Preview must run inside ComfyUI."
            ) from error

        guider = executor.class_obj
        try:
            latent_format = _latent_format_from_guider(guider)
        except Exception:
            logging.exception(
                "VELVET VICE Live Preview could not read the model preview "
                "format; sampling continues unchanged."
            )
            return executor(
                noise,
                latent_image,
                sampler,
                sigmas,
                denoise_mask,
                callback,
                disable_pbar,
                seed,
                latent_shapes=latent_shapes,
            )
        original_callback = callback
        self._preview_disabled = False
        self._warning_emitted = False
        self._vae_warning_emitted = False
        self._last_emit = 0.0
        self._first_event_logged = False

        keyframes = 0
        positive = getattr(guider, "conds", {}).get("positive", [])
        if positive:
            keyframe_indices = positive[0].get("keyframe_idxs")
            if keyframe_indices is not None:
                keyframes = len(torch.unique(keyframe_indices[0, 0, :, 0]))

        shape = latent_shapes[0] if len(latent_shapes) > 1 else None

        def combined_callback(step, x0, x, callback_total_steps):
            preview_latent = x0
            if preview_latent is not None and shape is not None:
                cut = 1
                for dimension in shape[1:]:
                    cut *= int(dimension)
                preview_latent = preview_latent[:, :, :cut].reshape(
                    [preview_latent.shape[0]] + list(shape)[1:]
                )
            if preview_latent is not None and keyframes > 0:
                preview_latent = preview_latent[:, :, :-keyframes]

            if preview_latent is not None and not self._preview_disabled:
                try:
                    self._emit_preview(
                        preview_latent,
                        latent_format=latent_format,
                        step=step,
                        total_steps=callback_total_steps,
                    )
                except Exception:
                    self._preview_disabled = True
                    if not self._warning_emitted:
                        self._warning_emitted = True
                        logging.exception(
                            "VELVET VICE Live Preview disabled for this render; "
                            "sampling continues unchanged."
                        )

            # Preserve ComfyUI's original callback exactly once.
            if original_callback is not None:
                original_callback(step, x0, x, callback_total_steps)

        return executor(
            noise,
            latent_image,
            sampler,
            sigmas,
            denoise_mask,
            combined_callback,
            disable_pbar,
            seed,
            latent_shapes=latent_shapes,
        )


class VelvetViceLTXNativePreviewBridge:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "preview_rate": (
                    "FLOAT",
                    {"default": 24.0, "min": 24.0, "max": 60.0, "step": 1.0},
                ),
                "jpeg_quality": (
                    "INT",
                    {"default": 95, "min": 85, "max": 95, "step": 1},
                ),
                "max_preview_edge": (
                    "INT",
                    {"default": 768, "min": 512, "max": 1024, "step": 32},
                ),
            },
            "optional": {
                "latent_upscale_model": ("LATENT_UPSCALE_MODEL",),
                "vae": ("VAE",),
            },
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "apply_preview_bridge"
    CATEGORY = "VELVET VICE/LTX/Preview"
    DESCRIPTION = (
        "Adds an isolated, VAE-decoded LTX live preview with a 24-60 FPS "
        "frame buffer. The sampling model is cloned and preview failures "
        "cannot stop a render."
    )

    def apply_preview_bridge(
        self,
        model,
        preview_rate,
        jpeg_quality,
        max_preview_edge,
        latent_upscale_model=None,
        vae=None,
    ):
        try:
            import comfy.patcher_extension
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE Live Preview must run inside ComfyUI."
            ) from error

        cloned = model.clone()
        wrapper = _NativePreviewOuterWrapper(
            preview_rate=preview_rate,
            jpeg_quality=jpeg_quality,
            max_edge=max_preview_edge,
            latent_upscale_model=latent_upscale_model,
            vae=vae,
        )
        cloned.add_wrapper_with_key(
            comfy.patcher_extension.WrappersMP.OUTER_SAMPLE,
            WRAPPER_KEY,
            wrapper,
        )
        return (cloned,)


class VelvetViceLTXLivePreviewDisplay:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "display"
    OUTPUT_NODE = True
    CATEGORY = "VELVET VICE/LTX/Preview"
    DESCRIPTION = (
        "Displays the dedicated Velvet Vice LTX live-preview frame buffer "
        "without participating in the render path."
    )

    def display(self):
        return {"ui": {"status": ["VELVET VICE LIVE PREVIEW READY"]}, "result": ()}
