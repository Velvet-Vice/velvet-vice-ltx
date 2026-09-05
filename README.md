# VELVET VICE LTX 2.3 + 2.5 v1.2.8

One versioned custom-node pack shared by the separate LTX 2.3 and LTX 2.5
Velvet Vice workflows.

## Installation

Recommended: install `VELVET VICE — LTX` directly through ComfyUI Manager /
Comfy Registry (`velvet-vice-ltx`), then restart ComfyUI and hard-refresh the
browser with `Ctrl+F5`.

The canonical Manager/Registry install folder is:

`ComfyUI/custom_nodes/velvet-vice-ltx`

Use only one copy of the package in `custom_nodes`. Older manual/Civitai copies
may exist under legacy names such as:

- `ComfyUI-Velvet-Vice-LTX`
- `ComfyUI-Velvet-Vice-LTX-main`
- `velvet-vice-ltx-main`

If a legacy copy remains beside the Manager-owned `velvet-vice-ltx` folder,
ComfyUI can keep loading the Velvet Vice LTX nodes even after Manager has
uninstalled its own tracked package. This makes Manager Uninstall look broken
although the Manager-owned folder was removed correctly.

For a one-time cleanup of those old duplicate folders, close ComfyUI and run:

`_CLEAN_LEGACY_LTX_DUPLICATES.cmd`

The cleanup tool deliberately does **not** delete the canonical Manager-owned
`velvet-vice-ltx` folder. Normal installs, updates and uninstalls should be done
through ComfyUI Manager after legacy duplicates have been removed.

The complete Civitai release can still include a versioned one-click installer
as a manual/offline fallback, but that installer should also target the same
canonical folder name `velvet-vice-ltx`. Never merge an older Velvet Vice LTX
custom-node directory into a newer release.

## Versioned autonomous prompt logic

The prompt Director exposes separate `LTX 2.3` and `LTX 2.5` profiles. The 2.3
profile adds no new control text and therefore retains the previous requests
unchanged. The 2.5 profile treats the connected image as the exact first
frame, emphasizes motion and chronological action instead of re-describing the
source, keeps a continuous take, integrates caused audio, and prepares a
grounded brief for the optional Gemma enhancer. Manual prompts remain exact
passthrough text in either profile.

Starting with v1.2.5, the selector is optional at the backend boundary. ComfyUI
can omit a visible widget from the submitted API prompt in some workflow states.
When that happens, Velvet Vice resolves the profile from workflow metadata,
then from unambiguous LTX 2.5 model markers, and finally falls back to LTX 2.3.
An explicit selector value always takes precedence. This keeps existing v1.2.4
workflow files compatible without changing either prompt profile.

## VRAM cleanup after Stop/Interrupt

ComfyUI skips downstream nodes when sampling is interrupted, so a cleanup node
placed after pass 1, 2, or 3 would never run in the failure case. The pack
therefore installs an interruption-only lifecycle hook. After an interrupted
Velvet Vice prompt has unwound safely, it stops the render monitor, unloads all
tracked ComfyUI models, collects Python objects, and clears the CUDA/IPC cache.
Successful prompts and non-Velvet-Vice workflows are not changed by this hook.

## LTX 2.5 prompt enhancer

The 2.5 workflow additionally loads
`text_encoders/LTX 2.5/gemma4_e2b_it_bf16.safetensors` through ComfyUI's core
`TextGenerateLTX2Prompt` node. The image-aware enhancer runs after the existing
Velvet Vice Director and is enabled by default through a lazy switch. Disabling
the switch passes the original Director prompt through unchanged. The negative
prompt is not enhanced. Its model selector is exposed directly in the native
`VELVET VICE · CORE LOADOUT`, so future compatible enhancer models can be
selected without changing the prompt pipeline. The adjacent
`Prompt Enhancer ON / OFF` control is enabled by default and drives the lazy
switch. OFF avoids evaluating the enhancer branch and preserves the Director
prompt unchanged.

## Preserved functionality

The LTX 2.3 branch and the existing Director, Power LoRA, Player, Live Preview,
Watermark, three-pass render, postprocessing and UI behavior remain unchanged.

The `web` directory contains exactly six JavaScript files.

## Registry

- Publisher: `velvet-vice`
- Node ID: `velvet-vice-ltx`
- Version: `1.2.8`
- Display name: `VELVET VICE — LTX`
