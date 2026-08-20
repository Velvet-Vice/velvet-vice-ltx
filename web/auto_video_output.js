import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";


const OUTPUT_NODE_TYPES = new Set([
    "VelvetViceLTXAutoVideoCombineV0112",
]);

// VelvetViceOutputStudio has its own adaptive player in velvet_vice_suite.js.
// Its Python class inherits from the legacy encoder class, so ComfyUI may expose
// the inherited class name through `comfyClass`. Never install the legacy direct
// preview on this modern node or two media elements will play the same MP4.
const MODERN_OUTPUT_NODE_TYPES = new Set([
    "VelvetViceOutputStudio",
]);

const STAGE_BY_NODE_ID = new Map([
    ["4035", "AUTONOMOUS PROMPT DIRECTOR"],
    ["4036", "RELEASING OLLAMA"],
    ["4038", "SYSTEM + MEMORY CHECK"],
    ["4037", "LOADING LTX MODEL"],
    ["3678", "LTX SHOT DIRECTOR"],
    ["3577", "PRE-PROCESSING"],
    ["3676", "DASIWA 3-PASS CORE · 8 / 4 / 2"],
    ["3420", "FINISHING + WATERMARK"],
    ["4000", "NATIVE FP16 QUALITY"],
    ["4030", "OPTIONAL AREA QUALITY"],
    ["3731", "RIFE 48 FPS"],
    ["4045", "TEMPORAL ANTI-GHOST"],
    ["2196", "FINAL VIDEO ENCODE"],
    ["4039", "FINAL CLEANUP"],
]);

const liveNodes = new Set();
let listenersInstalled = false;

function isModernOutput(node) {
    return MODERN_OUTPUT_NODE_TYPES.has(String(node?.type ?? ""))
        || MODERN_OUTPUT_NODE_TYPES.has(String(node?.comfyClass ?? ""));
}

function isSupportedOutput(node) {
    if (isModernOutput(node)) return false;
    return OUTPUT_NODE_TYPES.has(String(node?.type ?? ""))
        || OUTPUT_NODE_TYPES.has(String(node?.comfyClass ?? ""));
}

function silenceMediaElement(media) {
    if (!media) return;
    try { media.pause?.(); } catch (_) {}
    try { media.muted = true; } catch (_) {}
    try { media.volume = 0; } catch (_) {}
    try { media.removeAttribute?.("src"); } catch (_) {}
    try { media.srcObject = null; } catch (_) {}
    try { media.load?.(); } catch (_) {}
}

function removeLegacyDirectPreview(node) {
    if (!node) return;

    const widget = node.velvetViceFinalVideoPreviewWidget;
    const roots = [widget?.element, widget?.inputEl].filter(Boolean);
    for (const root of roots) {
        if (root?.matches?.("video, audio")) silenceMediaElement(root);
        for (const media of root?.querySelectorAll?.("video, audio") ?? []) {
            silenceMediaElement(media);
        }
        try { root.remove?.(); } catch (_) {}
    }

    if (widget && Array.isArray(node.widgets)) {
        try { widget.onRemove?.(); } catch (_) {}
        node.widgets = node.widgets.filter((item) => item !== widget);
    }

    if (node.velvetViceFinalVideoExecutionHandlerInstalled) {
        if (Object.prototype.hasOwnProperty.call(node, "__vvLegacyOriginalOnExecuted")) {
            node.onExecuted = node.__vvLegacyOriginalOnExecuted;
        }
        delete node.__vvLegacyOriginalOnExecuted;
        delete node.velvetViceFinalVideoExecutionHandlerInstalled;
    }

    delete node.velvetViceFinalVideoPreviewWidget;
    delete node.velvetViceLoadFinalVideo;
    delete node.velvetViceUpdateRenderStatus;
    liveNodes.delete(node);
}

function eventNodeId(detail) {
    if (detail == null) return null;
    if (typeof detail === "string" || typeof detail === "number") {
        return String(detail);
    }
    return detail.node != null ? String(detail.node) : null;
}

function resolveStage(nodeId) {
    if (!nodeId) return "FINALIZING";
    if (STAGE_BY_NODE_ID.has(nodeId)) return STAGE_BY_NODE_ID.get(nodeId);
    const graphNode = app?.graph?.getNodeById?.(Number(nodeId));
    const title = graphNode?.title ?? graphNode?.type;
    return title ? String(title).toUpperCase() : `NODE ${nodeId}`;
}

function updateAll(statusText, progress = null, detailText = "") {
    for (const node of liveNodes) {
        node.velvetViceUpdateRenderStatus?.(statusText, progress, detailText);
    }
}

function installGlobalListeners() {
    if (listenersInstalled) return;
    listenersInstalled = true;

    api.addEventListener("execution_start", () => {
        updateAll("WORKFLOW STARTED", 0, "Preparing the Velvet Vice render pipeline…");
    });

    api.addEventListener("executing", ({ detail }) => {
        const nodeId = eventNodeId(detail);
        if (nodeId == null) {
            updateAll("FINALIZING", null, "Waiting for the final output…");
            return;
        }
        updateAll(resolveStage(nodeId), null, `Active node: ${nodeId}`);
    });

    api.addEventListener("progress", ({ detail }) => {
        const value = Number(detail?.value ?? 0);
        const max = Number(detail?.max ?? 0);
        const pct = max > 0 ? Math.max(0, Math.min(1, value / max)) : null;
        const nodeId = eventNodeId(detail);
        updateAll(resolveStage(nodeId), pct, max > 0 ? `${value} / ${max}` : "Working…");
    });

    api.addEventListener("execution_error", ({ detail }) => {
        updateAll("ERROR", null, detail?.exception_message ?? "The workflow stopped with an error.");
    });

    api.addEventListener("execution_interrupted", () => {
        updateAll("INTERRUPTED", null, "Execution was interrupted.");
    });

    api.addEventListener("execution_success", () => {
        updateAll("ENCODE COMPLETE", 1, "Loading the saved MP4 preview…");
    });
}

function installExecutionHandler(node) {
    if (isModernOutput(node)) {
        removeLegacyDirectPreview(node);
        return;
    }
    if (node.velvetViceFinalVideoExecutionHandlerInstalled) return;
    node.velvetViceFinalVideoExecutionHandlerInstalled = true;
    const originalExecuted = node.onExecuted;
    node.__vvLegacyOriginalOnExecuted = originalExecuted;
    node.onExecuted = function (message) {
        originalExecuted?.apply(this, arguments);
        const preview = message?.gifs?.[0];
        if (preview) {
            ensureDirectVideoPreview(this);
            this.velvetViceLoadFinalVideo?.(preview);
        }
    };
}

function ensureDirectVideoPreview(node) {
    if (isModernOutput(node)) {
        removeLegacyDirectPreview(node);
        return null;
    }
    if (node.velvetViceFinalVideoPreviewWidget) {
        return node.velvetViceFinalVideoPreviewWidget;
    }

    installGlobalListeners();
    liveNodes.add(node);

    const container = document.createElement("div");
    container.style.width = "100%";
    container.style.boxSizing = "border-box";
    container.style.padding = "4px 6px 8px";

    const statusCard = document.createElement("div");
    statusCard.style.padding = "9px 10px";
    statusCard.style.marginBottom = "8px";
    statusCard.style.borderRadius = "7px";
    statusCard.style.background = "linear-gradient(135deg, rgba(145,58,100,.34), rgba(45,107,97,.20))";
    statusCard.style.border = "1px solid rgba(240,160,197,.28)";

    const stage = document.createElement("div");
    stage.textContent = "READY";
    stage.style.fontWeight = "700";
    stage.style.letterSpacing = ".04em";
    stage.style.color = "#f0a0c5";
    statusCard.appendChild(stage);

    const detail = document.createElement("div");
    detail.textContent = "Queue the workflow. The final MP4 will appear below after one encode.";
    detail.style.marginTop = "4px";
    detail.style.opacity = ".78";
    detail.style.fontSize = "12px";
    statusCard.appendChild(detail);

    const barTrack = document.createElement("div");
    barTrack.style.height = "6px";
    barTrack.style.marginTop = "8px";
    barTrack.style.borderRadius = "999px";
    barTrack.style.overflow = "hidden";
    barTrack.style.background = "rgba(255,255,255,.10)";
    const bar = document.createElement("div");
    bar.style.width = "0%";
    bar.style.height = "100%";
    bar.style.transition = "width .12s linear";
    bar.style.background = "linear-gradient(90deg, #913a64, #f0a0c5)";
    barTrack.appendChild(bar);
    statusCard.appendChild(barTrack);
    container.appendChild(statusCard);

    const video = document.createElement("video");
    video.controls = true;
    video.loop = true;
    video.muted = true;
    video.autoplay = true;
    video.playsInline = true;
    video.preload = "metadata";
    video.style.width = "100%";
    video.style.display = "none";
    video.style.borderRadius = "7px";
    video.style.background = "#08070a";
    container.appendChild(video);

    const empty = document.createElement("div");
    empty.textContent = "Final video preview appears here after encoding.";
    empty.style.padding = "8px";
    empty.style.opacity = "0.65";
    container.appendChild(empty);

    const previewWidget = node.addDOMWidget(
        "velvet_vice_final_video_preview",
        "LIVE STATUS + FINAL VIDEO PREVIEW",
        container,
        { serialize: false, hideOnZoom: false },
    );
    previewWidget.serialize = false;
    previewWidget.options = { ...(previewWidget.options ?? {}), serialize: false };
    previewWidget.serializeValue = () => undefined;
    previewWidget.aspectRatio = null;
    previewWidget.computeSize = (width) => {
        if (!previewWidget.aspectRatio) return [width, 142];
        return [width, Math.max(260, (width - 20) / previewWidget.aspectRatio + 122)];
    };

    node.velvetViceUpdateRenderStatus = (text, progress, details) => {
        stage.textContent = text || "WORKING";
        detail.textContent = details || "Working…";
        if (progress == null) {
            bar.style.width = "16%";
            bar.style.opacity = ".45";
        } else {
            bar.style.opacity = "1";
            bar.style.width = `${Math.round(progress * 100)}%`;
        }
        node.setDirtyCanvas(true, true);
    };

    video.addEventListener("loadedmetadata", () => {
        previewWidget.aspectRatio = video.videoWidth > 0 && video.videoHeight > 0
            ? video.videoWidth / video.videoHeight
            : 16 / 9;
        video.style.display = "block";
        empty.style.display = "none";
        stage.textContent = "FINAL VIDEO READY";
        detail.textContent = "Saved MP4 loaded. Preview playback starts automatically.";
        bar.style.width = "100%";
        bar.style.opacity = "1";
        video.play().catch(() => {});
        node.setSize(node.computeSize());
        node.setDirtyCanvas(true, true);
    });

    video.addEventListener("error", () => {
        video.style.display = "none";
        empty.style.display = "block";
        empty.textContent = "The video was saved, but the browser could not load the preview.";
        stage.textContent = "PREVIEW LOAD ERROR";
        node.setDirtyCanvas(true, true);
    });

    node.velvetViceLoadFinalVideo = (preview) => {
        if (!preview?.filename) return;
        const params = {
            filename: preview.filename,
            subfolder: preview.subfolder ?? "",
            type: preview.type ?? "output",
            t: Date.now(),
        };
        stage.textContent = "LOADING FINAL VIDEO";
        detail.textContent = preview.filename;
        video.style.display = "none";
        empty.style.display = "block";
        empty.textContent = "Loading saved final video…";
        video.src = api.apiURL("/view?" + new URLSearchParams(params));
        video.load();
    };

    node.velvetViceFinalVideoPreviewWidget = previewWidget;
    return previewWidget;
}

function addPreviewAfterCurrentConfiguration(node) {
    const schedule = globalThis.requestAnimationFrame ?? ((callback) => globalThis.setTimeout(callback, 0));
    schedule(() => {
        if (isModernOutput(node)) {
            removeLegacyDirectPreview(node);
            return;
        }
        if (node.graph && !node.velvetViceFinalVideoPreviewWidget) {
            ensureDirectVideoPreview(node);
        }
    });
}

app.registerExtension({
    name: "VelvetVice.LTXLiveStatusAndFinalPreviewV05",

    async nodeCreated(node) {
        if (isModernOutput(node)) {
            removeLegacyDirectPreview(node);
            return;
        }
        if (!isSupportedOutput(node)) return;
        installExecutionHandler(node);
        addPreviewAfterCurrentConfiguration(node);
    },

    loadedGraphNode(node) {
        if (isModernOutput(node)) {
            removeLegacyDirectPreview(node);
            return;
        }
        if (!isSupportedOutput(node)) return;
        installExecutionHandler(node);
        ensureDirectVideoPreview(node);
    },

    nodeRemoved(node) {
        removeLegacyDirectPreview(node);
        liveNodes.delete(node);
    },
});
