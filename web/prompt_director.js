import { app } from "../../scripts/app.js";

function ensureCss() { window.VelvetViceLTXDesign?.installCss?.(); }
function findWidget(node, name) { return node.widgets?.find((widget) => widget.name === name); }

app.registerExtension({
    name: "VelvetVice.LTX.PromptDirectorSurfaceV100",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "VelvetViceLTXPromptDirector") return;
        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalCreated?.apply(this, arguments);
            ensureCss();
            const fullAutoSettings = findWidget(this, "full_auto_settings");
            if (fullAutoSettings) fullAutoSettings.label = "EDITABLE FULL AUTO DEFAULTS";
            const endingMode = findWidget(this, "ending_mode");
            if (endingMode) endingMode.label = "ENDING MODE — HARD OVERRIDE";
            const promptProfile = findWidget(this, "ltx_prompt_profile");
            if (promptProfile) promptProfile.label = "LTX PROMPT LOGIC";

            const shell = document.createElement("div");
            shell.className = "vv-shell";
            const head = document.createElement("div");
            head.className = "vv-head";
            const brand = document.createElement("div");
            brand.className = "vv-brand";
            brand.textContent = "VELVET VICE · FINAL PROMPT OUTPUT";
            const badge = document.createElement("div");
            badge.className = "vv-badge";
            badge.textContent = "READY";
            head.append(brand, badge);
            shell.appendChild(head);
            const body = document.createElement("div");
            body.className = "vv-body";
            const chips = document.createElement("div");
            chips.className = "vv-prompt-meta";
            const modeChip = document.createElement("div"); modeChip.className = "vv-chip";
            const endingChip = document.createElement("div"); endingChip.className = "vv-chip";
            const memoryChip = document.createElement("div"); memoryChip.className = "vv-chip";
            const profileChip = document.createElement("div"); profileChip.className = "vv-chip";
            chips.append(modeChip, profileChip, endingChip, memoryChip);
            const status = document.createElement("div");
            status.className = "vv-status-detail";
            status.textContent = "Not executed yet. Manual mode never contacts Ollama.";
            const prompt = document.createElement("textarea");
            prompt.className = "vv-textarea";
            prompt.readOnly = true;
            prompt.placeholder = "The validated LTX prompt appears here after execution.";
            prompt.style.minHeight = "130px";
            const actions = document.createElement("div");
            actions.style.display = "flex"; actions.style.gap = "8px"; actions.style.marginTop = "8px";
            const copy = document.createElement("button"); copy.className = "vv-button"; copy.textContent = "COPY FINAL PROMPT";
            copy.addEventListener("click", async () => { if (prompt.value) await navigator.clipboard.writeText(prompt.value).catch(()=>{}); });
            actions.append(copy);
            body.append(chips, status, prompt, actions);
            shell.appendChild(body);

            const dom = this.addDOMWidget("vv_director_surface", "VELVET VICE DIRECTOR", shell, {serialize:false, hideOnZoom:false});
            dom.serialize = false; dom.serializeValue = () => undefined;
            dom.computeSize = (width) => [width, 278];
            this.vvDirectorPrompt = prompt; this.vvDirectorStatus = status; this.vvDirectorBadge = badge;

            const refresh = () => {
                modeChip.textContent = `MODE · ${findWidget(this,"mode")?.value ?? "MANUAL"}`;
                profileChip.textContent = `PROMPT · ${findWidget(this,"ltx_prompt_profile")?.value ?? "LTX 2.3"}`;
                endingChip.textContent = `ENDING · ${findWidget(this,"ending_mode")?.value ?? "AUTO"}`;
                memoryChip.textContent = `OLLAMA · ${findWidget(this,"ollama_context_profile")?.value ?? "DEFAULT"}`;
            };
            for (const name of ["mode","ltx_prompt_profile","ending_mode","ollama_context_profile"]) {
                const widget = findWidget(this, name); if (!widget) continue;
                const original = widget.callback;
                widget.callback = (value) => { original?.call(widget, value); refresh(); };
            }
            refresh();
            this.setSize([Math.max(this.size?.[0] ?? 800, 800), Math.max(this.size?.[1] ?? 780, 780)]);
            return result;
        };

        const originalExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalExecuted?.apply(this, arguments);
            const prompt = message?.final_prompt?.[0];
            const status = message?.status?.[0];
            if (typeof prompt === "string" && this.vvDirectorPrompt) this.vvDirectorPrompt.value = prompt;
            if (typeof status === "string" && this.vvDirectorStatus) this.vvDirectorStatus.textContent = status;
            if (this.vvDirectorBadge) this.vvDirectorBadge.textContent = "PROMPT READY";
            this.setDirtyCanvas?.(true, true);
        };
    },
});
