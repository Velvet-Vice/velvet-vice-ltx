import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "VelvetVice.LTX.FinalPromptSurfaceV100",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "VelvetViceLTXFinalPromptPreview") return;
        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalCreated?.apply(this, arguments);
            window.VelvetViceLTXDesign?.installCss?.();
            const shell = document.createElement("div"); shell.className = "vv-shell";
            const head = document.createElement("div"); head.className = "vv-head";
            const brand = document.createElement("div"); brand.className = "vv-brand"; brand.textContent = "VELVET VICE · FINAL PROMPT SENT TO LTXDIRECTOR";
            const badge = document.createElement("div"); badge.className = "vv-badge"; badge.textContent = "LTX INPUT";
            head.append(brand,badge); shell.appendChild(head);
            const body = document.createElement("div"); body.className = "vv-body";
            const meta = document.createElement("div"); meta.className = "vv-prompt-meta";
            const stats = document.createElement("div"); stats.className = "vv-chip"; stats.textContent = "NOT EXECUTED";
            const lock = document.createElement("div"); lock.className = "vv-chip"; lock.textContent = "EXACT DIRECTOR INPUT";
            meta.append(stats, lock);
            const text = document.createElement("textarea"); text.className = "vv-textarea"; text.readOnly = true; text.value = "Queue the workflow to generate the final prompt."; text.style.minHeight = "310px";
            const copy = document.createElement("button"); copy.className = "vv-button"; copy.textContent = "COPY FINAL PROMPT"; copy.style.marginTop = "9px";
            copy.addEventListener("click", async () => { if (text.value) await navigator.clipboard.writeText(text.value).catch(()=>{}); });
            body.append(meta,text,copy); shell.appendChild(body);
            const dom = this.addDOMWidget("vv_final_prompt_surface","VELVET VICE FINAL PROMPT",shell,{serialize:false,hideOnZoom:false});
            dom.serialize=false; dom.serializeValue=()=>undefined; dom.computeSize=(width)=>[width,480];
            this.vvPromptText=text; this.vvPromptStats=stats;
            this.setSize([Math.max(this.size?.[0] ?? 900,900), Math.max(this.size?.[1] ?? 570,570)]);
            return result;
        };
        const originalExecuted=nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted=function(message){
            originalExecuted?.apply(this,arguments);
            const prompt=message?.final_prompt?.[0]; const stats=message?.stats?.[0];
            if(typeof prompt==="string"&&this.vvPromptText)this.vvPromptText.value=prompt;
            if(typeof stats==="string"&&this.vvPromptStats)this.vvPromptStats.textContent=stats.toUpperCase();
            this.setDirtyCanvas?.(true,true);
        };
    },
});
