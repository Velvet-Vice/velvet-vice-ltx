import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const DISPLAY_TYPE = "VelvetViceLTXLivePreviewDisplay";
const EVENT_NAME = "velvet_vice.ltx_live_preview";
const STYLE_ID = "vv-native-ltx-live-preview-v1115";
const VERSION = "1.1.15";
const MIN_TIMELINE_FPS = 24;
const MIN_SOURCE_PLAYBACK_FPS = 0.5;
const PREVIEW_FPS_OPTIONS = ["AUTO", "10", "15", "20", "24", "30"];
const PREVIEW_FPS_PROPERTY = "vv_preview_fps";
const displays = new Set();
let listenersInstalled = false;

function installStyle() {
    const existing = document.getElementById(STYLE_ID);
    if (existing) {
        if (document.head.lastElementChild !== existing) document.head.appendChild(existing);
        return;
    }
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .vv-native-preview-shell,.vv-native-preview-shell *{box-sizing:border-box}
      .vv-native-preview-shell{width:100%;min-width:0;padding:12px 14px 13px;pointer-events:none;contain:layout paint;font-family:Inter,"Segoe UI",Arial,sans-serif;color:#e9e5ee;background:linear-gradient(145deg,#151d25,#202b35);border:1px solid rgba(195,180,212,.22);border-radius:12px;overflow:hidden;box-shadow:0 10px 28px rgba(0,0,0,.27);-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
      .vv-native-preview-meta{display:grid;grid-template-columns:auto auto;grid-template-areas:"title title" "badge controls";align-items:center;justify-content:center;gap:5px 10px;min-height:47px;margin:0 0 10px;padding:0 20px;text-align:center;pointer-events:auto;cursor:grab;touch-action:none;user-select:none}
      .vv-native-preview-meta.vv-dragging{cursor:grabbing}
      .vv-native-preview-meta strong{grid-area:title;display:block;width:100%;min-width:0;color:#eee9f2;font-size:11px;line-height:1.25;font-weight:850;letter-spacing:.095em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .vv-native-preview-meta>span{grid-area:badge;display:block;max-width:170px;min-width:0;padding:4px 8px;border-radius:999px;background:#111820;border:1px solid rgba(196,181,214,.17);font-size:8px;line-height:1.15;font-weight:850;letter-spacing:.08em;color:#cbbdd8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .vv-native-preview-controls{grid-area:controls;display:flex;align-items:center;justify-content:center;gap:6px;min-height:22px;margin:0;pointer-events:auto}
      .vv-native-preview-controls label{color:#9da8b3;font-size:7.5px;line-height:1;font-weight:850;letter-spacing:.08em;white-space:nowrap;user-select:none}
      .vv-native-preview-fps{width:88px;height:22px;padding:0 23px 0 8px;border:1px solid rgba(196,181,214,.22);border-radius:7px;outline:none;background:#111820;color:#e8e2ed;font:800 8.5px/1 Inter,"Segoe UI",Arial,sans-serif;letter-spacing:.03em;cursor:pointer}
      .vv-native-preview-fps:hover{border-color:rgba(199,181,216,.42)}
      .vv-native-preview-fps:focus{border-color:rgba(202,180,223,.68);box-shadow:0 0 0 2px rgba(164,132,190,.14)}
      .vv-native-preview-stage{display:flex;align-items:center;justify-content:center;max-width:100%;min-width:0;height:320px;margin:0 auto;background:#070b0f;border:1px solid rgba(196,181,214,.15);border-radius:10px;overflow:hidden;box-shadow:inset 0 0 32px rgba(0,0,0,.38)}
      .vv-native-preview-stage img{display:none;width:100%;height:100%;max-width:100%;max-height:100%;object-fit:contain;image-rendering:auto;background:#070b0f;pointer-events:none;user-select:none}
      .vv-native-preview-empty{padding:42px 18px;text-align:center;color:#b5c0ca;font-size:10px;line-height:1.45;letter-spacing:.025em}
      .vv-native-preview-foot{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:6px 12px;margin-top:9px;color:#8995a1;font-size:8.5px;line-height:1.3}
      .vv-native-preview-foot span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    `;
    document.head.appendChild(style);
}

function nodeType(node) {
    return String(node?.comfyClass ?? node?.type ?? "");
}

function makePreviewDraggable(node, handle) {
    if (!node || !handle || handle.__vvDragBoundV1115) return;
    handle.__vvDragBoundV1115 = true;
    handle.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        const drag = {
            clientX: event.clientX,
            clientY: event.clientY,
            nodeX: Number(node.pos?.[0] ?? 0),
            nodeY: Number(node.pos?.[1] ?? 0),
            scale: Math.max(0.05, Number(app.canvas?.ds?.scale ?? 1) || 1),
        };
        handle.classList.add("vv-dragging");

        const move = (moveEvent) => {
            if (moveEvent.pointerId !== event.pointerId) return;
            const nextX = drag.nodeX + (moveEvent.clientX - drag.clientX) / drag.scale;
            const nextY = drag.nodeY + (moveEvent.clientY - drag.clientY) / drag.scale;
            try { node.pos = [nextX, nextY]; } catch (_) {
                if (node.pos) {
                    node.pos[0] = nextX;
                    node.pos[1] = nextY;
                }
            }
            app.canvas?.setDirty?.(true, true);
            node.graph?.setDirtyCanvas?.(true, true);
            node.setDirtyCanvas?.(true, true);
            moveEvent.preventDefault();
            moveEvent.stopPropagation();
        };
        const finish = (upEvent) => {
            window.removeEventListener("pointermove", move, true);
            window.removeEventListener("pointerup", finish, true);
            window.removeEventListener("pointercancel", finish, true);
            window.removeEventListener("blur", finish, true);
            handle.classList.remove("vv-dragging");
            upEvent?.preventDefault?.();
            upEvent?.stopPropagation?.();
        };
        window.addEventListener("pointermove", move, true);
        window.addEventListener("pointerup", finish, true);
        window.addEventListener("pointercancel", finish, true);
        window.addEventListener("blur", finish, true);
        event.preventDefault();
        event.stopPropagation();
    });
}

function previewGeometry(width, height) {
    const ratio = Math.max(0.25, Math.min(4, Number(width) / Math.max(1, Number(height))));
    let stageWidth;
    let stageHeight;
    if (ratio < 1) {
        stageHeight = 640;
        stageWidth = Math.round(stageHeight * ratio);
    } else {
        stageWidth = 640;
        stageHeight = Math.round(stageWidth / ratio);
    }
    stageWidth = Math.max(340, Math.min(640, stageWidth));
    stageHeight = Math.max(260, Math.min(640, stageHeight));
    return {
        stageWidth,
        stageHeight,
        nodeWidth: Math.max(400, Math.min(680, stageWidth + 32)),
    };
}

function setNodeSize(display, geometry) {
    const safeStageWidth = Math.max(340, Math.min(640, Math.round(geometry.stageWidth)));
    const safeStageHeight = Math.max(260, Math.min(640, Math.round(geometry.stageHeight)));
    const safeNodeWidth = Math.max(400, Math.min(680, Math.round(geometry.nodeWidth)));
    const widgetHeight = safeStageHeight + 108;
    const nodeHeight = widgetHeight + 68;
    display.layout.height = widgetHeight;
    display.shell.style.height = `${widgetHeight}px`;
    display.shell.style.minHeight = `${widgetHeight}px`;
    display.stage.style.width = `${safeStageWidth}px`;
    display.stage.style.height = `${safeStageHeight}px`;

    display.widget.computeSize = () => [safeNodeWidth, widgetHeight];
    display.widget.computeLayoutSize = () => ({
        minHeight: display.layout.height,
        maxHeight: display.layout.height,
    });
    display.widget.options ??= {};
    display.widget.options.getMinHeight = () => display.layout.height;
    display.widget.options.getMaxHeight = () => display.layout.height;
    display.widget.options.getHeight = () => display.layout.height;

    const currentWidth = Number(display.node.size?.[0] ?? 0);
    const currentHeight = Number(display.node.size?.[1] ?? 0);
    if (Math.abs(currentWidth - safeNodeWidth) > 2 || Math.abs(currentHeight - nodeHeight) > 2) {
        display.node.setSize?.([safeNodeWidth, nodeHeight]);
        if (display.node.size) {
            display.node.size[0] = safeNodeWidth;
            display.node.size[1] = nodeHeight;
        }
    }
    display.node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
}

function normalizePreviewFpsMode(value) {
    const mode = String(value ?? "AUTO").toUpperCase();
    return PREVIEW_FPS_OPTIONS.includes(mode) ? mode : "AUTO";
}

function effectivePreviewFps(display) {
    const selected = normalizePreviewFpsMode(display.previewFpsMode);
    if (selected === "AUTO") {
        return Math.max(MIN_SOURCE_PLAYBACK_FPS, Math.min(60, Number(display.sourcePlaybackFps) || MIN_SOURCE_PLAYBACK_FPS));
    }
    return Number(selected);
}

function restartAnimator(display) {
    stopAnimator(display);
    if (display.frameUrls.length > 1) startAnimator(display);
}

function stopAnimator(display) {
    if (display.animationId != null) cancelAnimationFrame(display.animationId);
    display.animationId = null;
    display.lastTick = 0;
}

function stopWatchdog(display) {
    if (display.watchdogId != null) clearTimeout(display.watchdogId);
    display.watchdogId = null;
}

function showFrame(display, index) {
    if (!display.frameUrls.length) return;
    const safeIndex = ((index % display.frameUrls.length) + display.frameUrls.length) % display.frameUrls.length;
    display.frameIndex = safeIndex;
    display.image.src = display.frameUrls[safeIndex];
    display.image.style.display = "block";
    display.empty.style.display = "none";
    const previewLabel = display.previewFpsMode === "AUTO"
        ? `AUTO (${Math.round(effectivePreviewFps(display))})`
        : display.previewFpsMode;
    display.counter.textContent = `Frame ${safeIndex + 1} / ${display.frameUrls.length} - PREVIEW ${previewLabel} FPS - ${Math.round(display.timelineFps)} FPS TIMELINE`;
}

function startAnimator(display) {
    if (display.animationId != null || display.frameUrls.length <= 1) return;
    const tick = (timestamp) => {
        const interval = 1000 / effectivePreviewFps(display);
        if (!display.lastTick) display.lastTick = timestamp;
        const elapsed = timestamp - display.lastTick;
        if (elapsed >= interval && display.frameUrls.length) {
            const advance = Math.max(1, Math.floor(elapsed / interval));
            display.lastTick += advance * interval;
            showFrame(display, display.frameIndex + advance);
        }
        display.animationId = requestAnimationFrame(tick);
    };
    display.animationId = requestAnimationFrame(tick);
}

function clearDisplay(display, message = "Waiting for the first LTX sampler frame...") {
    stopAnimator(display);
    stopWatchdog(display);
    display.frameUrls = [];
    display.preloadedFrames = [];
    display.frameIndex = 0;
    display.sourcePlaybackFps = MIN_SOURCE_PLAYBACK_FPS;
    display.timelineFps = MIN_TIMELINE_FPS;
    display.image.removeAttribute("src");
    display.image.style.display = "none";
    display.empty.style.display = "block";
    display.empty.textContent = message;
    display.title.textContent = "VELVET VICE - REAL-TIME HIGH-RES LIVE PREVIEW";
    display.title.title = display.title.textContent;
    display.badge.textContent = "READY";
    display.details.textContent = "TAE-decoded preview - real LTX video duration";
    display.counter.textContent = `v${VERSION}`;
    if (display.fpsSelect) display.fpsSelect.value = normalizePreviewFpsMode(display.previewFpsMode);
    setNodeSize(display, previewGeometry(16, 9));
}

function updateDisplay(display, detail) {
    const width = Number(detail?.width ?? 0);
    const height = Number(detail?.height ?? 0);
    const encodedFrames = Array.isArray(detail?.images)
        ? detail.images.filter((item) => typeof item === "string" && item.length)
        : typeof detail?.image === "string" && detail.image.length ? [detail.image] : [];
    if (!encodedFrames.length || width <= 0 || height <= 0) return;

    // Latest-frame-wins: a newly received preview buffer replaces the current
    // one immediately. Nothing is queued between sampler callbacks.
    stopAnimator(display);
    stopWatchdog(display);
    const mime = detail?.mime || "image/jpeg";
    display.frameUrls = encodedFrames.map((encoded) => `data:${mime};base64,${encoded}`);
    display.preloadedFrames = display.frameUrls.map((src) => {
        const preload = new Image();
        preload.decoding = "async";
        preload.src = src;
        return preload;
    });
    display.frameIndex = 0;
    display.timelineFps = Math.max(
        MIN_TIMELINE_FPS,
        Math.min(60, Number(detail?.timeline_fps ?? detail?.playback_fps ?? MIN_TIMELINE_FPS)),
    );
    display.sourcePlaybackFps = Math.max(
        MIN_SOURCE_PLAYBACK_FPS,
        Math.min(60, Number(detail?.source_playback_fps ?? detail?.playback_fps ?? MIN_TIMELINE_FPS)),
    );

    const ratio = width / height;
    const orientation = Math.abs(ratio - 1) < 0.015
        ? "SQUARE"
        : ratio > 1 ? "LANDSCAPE" : "PORTRAIT";
    const pass = Number(detail?.pass ?? 0);
    const step = Number(detail?.step ?? 0);
    const steps = Math.max(1, Number(detail?.steps ?? 1));
    const quality = detail?.used_preview_vae ? "TAE HIGH RES" : "SAFE FALLBACK";

    display.title.textContent = `${width} x ${height} - ${orientation}`;
    display.title.title = display.title.textContent;
    display.badge.textContent = pass ? `PASS ${pass} - LIVE` : "LIVE";
    display.details.textContent = `Sampler step ${step} / ${steps} - ${quality} - REAL TIME`;
    setNodeSize(display, previewGeometry(width, height));
    showFrame(display, 0);
    startAnimator(display);
}

function installListeners() {
    if (listenersInstalled) return;
    listenersInstalled = true;
    api.addEventListener(EVENT_NAME, ({ detail }) => {
        for (const display of displays) updateDisplay(display, detail);
    });
    api.addEventListener("execution_start", () => {
        for (const display of displays) {
            clearDisplay(display, "Render started. Waiting for the first preview buffer...");
            display.badge.textContent = "STARTING";
            display.watchdogId = setTimeout(() => {
                if (display.frameUrls.length) return;
                display.badge.textContent = "WAITING";
                display.empty.textContent = "Sampler is running, but no preview buffer has arrived yet.";
            }, 20000);
        }
    });
    api.addEventListener("execution_error", () => {
        for (const display of displays) {
            stopWatchdog(display);
            display.badge.textContent = "ERROR";
            display.details.textContent = "The render stopped before completion.";
        }
    });
    api.addEventListener("execution_interrupted", () => {
        for (const display of displays) {
            stopWatchdog(display);
            display.badge.textContent = "STOPPED";
        }
    });
    api.addEventListener("execution_success", () => {
        for (const display of displays) {
            stopWatchdog(display);
            display.badge.textContent = "COMPLETE";
        }
    });
}

function removeStaleDisplay(node) {
    const active = node.__vvNativePreviewDisplay;
    if (active) {
        stopAnimator(active);
        stopWatchdog(active);
        displays.delete(active);
    }
    try { node.__vvNativePreviewDisplay?.shell?.closest?.(".dom-widget")?.remove?.(); } catch (_) {}
    for (const item of [...(node.widgets ?? [])]) {
        if (!String(item?.name ?? "").startsWith("vv_native_ltx_live_preview")) continue;
        try { item.onRemove?.(); } catch (_) {}
        try { item.element?.closest?.(".dom-widget")?.remove?.(); } catch (_) {}
        try { item.inputEl?.closest?.(".dom-widget")?.remove?.(); } catch (_) {}
        try { item.element?.remove?.(); } catch (_) {}
        try { item.inputEl?.remove?.(); } catch (_) {}
    }
    if (Array.isArray(node.widgets)) {
        node.widgets = node.widgets.filter(
            (item) => !String(item?.name ?? "").startsWith("vv_native_ltx_live_preview"),
        );
    }
    node.__vvNativePreviewDisplay = null;
}

function installDisplay(node) {
    const currentSurfaces = (node.widgets ?? []).filter((item) =>
        String(item?.name ?? "").startsWith("vv_native_ltx_live_preview")
    );
    if (
        node.__vvNativePreviewDisplayVersion === VERSION &&
        currentSurfaces.length === 1 &&
        Boolean(node.__vvNativePreviewDisplay)
    ) return;
    removeStaleDisplay(node);
    node.__vvNativePreviewDisplayVersion = VERSION;
    installStyle();
    installListeners();

    const shell = document.createElement("div");
    shell.className = "vv-native-preview-shell";
    shell.dataset.vvSurface = "native-ltx-live-preview-v1115";

    const meta = document.createElement("div");
    meta.className = "vv-native-preview-meta";
    const title = document.createElement("strong");
    const badge = document.createElement("span");
    meta.append(title, badge);
    makePreviewDraggable(node, meta);
    shell.appendChild(meta);

    const controls = document.createElement("div");
    controls.className = "vv-native-preview-controls";
    const fpsLabel = document.createElement("label");
    fpsLabel.textContent = "PREVIEW FPS";
    const fpsSelect = document.createElement("select");
    fpsSelect.className = "vv-native-preview-fps";
    fpsSelect.setAttribute("aria-label", "Preview FPS");
    for (const value of PREVIEW_FPS_OPTIONS) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value === "AUTO" ? "AUTO" : `${value} FPS`;
        fpsSelect.appendChild(option);
    }
    node.properties ??= {};
    const initialPreviewFps = normalizePreviewFpsMode(node.properties[PREVIEW_FPS_PROPERTY]);
    node.properties[PREVIEW_FPS_PROPERTY] = initialPreviewFps;
    fpsSelect.value = initialPreviewFps;
    fpsSelect.addEventListener("pointerdown", (event) => event.stopPropagation());
    controls.addEventListener("pointerdown", (event) => event.stopPropagation());
    controls.append(fpsLabel, fpsSelect);
    meta.appendChild(controls);

    const stage = document.createElement("div");
    stage.className = "vv-native-preview-stage";
    const image = document.createElement("img");
    image.alt = "VELVET VICE LTX buffered live sampler preview";
    image.draggable = false;
    const empty = document.createElement("div");
    empty.className = "vv-native-preview-empty";
    stage.append(image, empty);
    shell.appendChild(stage);

    const foot = document.createElement("div");
    foot.className = "vv-native-preview-foot";
    const details = document.createElement("span");
    const counter = document.createElement("span");
    foot.append(details, counter);
    shell.appendChild(foot);

    const layout = { height: 413 };
    const widget = node.addDOMWidget(
        "vv_native_ltx_live_preview_v1115",
        "VELVET VICE NATIVE LTX LIVE PREVIEW",
        shell,
        {
            serialize: false,
            hideOnZoom: false,
            margin: 0,
            getMinHeight: () => layout.height,
            getMaxHeight: () => layout.height,
            getHeight: () => layout.height,
        },
    );
    widget.serialize = false;
    widget.serializeValue = () => undefined;

    const display = {
        node,
        widget,
        layout,
        shell,
        stage,
        image,
        empty,
        title,
        badge,
        details,
        counter,
        fpsSelect,
        previewFpsMode: initialPreviewFps,
        frameUrls: [],
        preloadedFrames: [],
        frameIndex: 0,
        sourcePlaybackFps: MIN_SOURCE_PLAYBACK_FPS,
        timelineFps: MIN_TIMELINE_FPS,
        animationId: null,
        lastTick: 0,
        watchdogId: null,
    };
    fpsSelect.addEventListener("change", () => {
        const mode = normalizePreviewFpsMode(fpsSelect.value);
        display.previewFpsMode = mode;
        node.properties ??= {};
        node.properties[PREVIEW_FPS_PROPERTY] = mode;
        restartAnimator(display);
        if (display.frameUrls.length) showFrame(display, display.frameIndex);
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    });

    displays.add(display);
    node.__vvNativePreviewDisplay = display;
    const previousRemoved = node.onRemoved;
    node.onRemoved = function () {
        stopAnimator(display);
        stopWatchdog(display);
        displays.delete(display);
        previousRemoved?.apply(this, arguments);
    };
    clearDisplay(display);
}

function reassertSinglePreviewSurface() {
    installStyle();
    for (const node of app.graph?._nodes ?? []) {
        if (nodeType(node) === DISPLAY_TYPE) installDisplay(node);
    }
}

app.registerExtension({
    name: "VelvetVice.LTX.NativeLivePreviewV1115DraggableSingleHeader",
    setup() {
        installStyle();
        installListeners();
    },
    nodeCreated(node) {
        if (nodeType(node) === DISPLAY_TYPE) installDisplay(node);
    },
    loadedGraphNode(node) {
        if (nodeType(node) === DISPLAY_TYPE) installDisplay(node);
    },
    afterConfigureGraph() {
        reassertSinglePreviewSurface();
        requestAnimationFrame(() => requestAnimationFrame(reassertSinglePreviewSurface));
        setTimeout(reassertSinglePreviewSurface, 250);
        setTimeout(reassertSinglePreviewSurface, 1000);
        setTimeout(reassertSinglePreviewSurface, 2750);
        setTimeout(reassertSinglePreviewSurface, 4000);
        setTimeout(reassertSinglePreviewSurface, 6000);
        // Run after the last delayed replacement used by merged v1.1.12 and
        // older frontend files. This only reconciles the visible DOM surface.
        setTimeout(reassertSinglePreviewSurface, 6500);
        setTimeout(reassertSinglePreviewSurface, 8000);
        setTimeout(reassertSinglePreviewSurface, 10000);
        setTimeout(reassertSinglePreviewSurface, 12500);
    },
});
