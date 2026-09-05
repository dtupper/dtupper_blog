"use strict";
const $ = id => document.getElementById(id);
const controls = ["page", "viewport", "mode", "scheme"];
const params = new URLSearchParams(location.search);
let revision = -1;
let sizes = {};
let panels = [];
let route = params.get("page") || "/";
for (const id of controls.slice(1)) {
    if ([...$(id).options].some(option => option.value === params.get(id))) {
        $(id).value = params.get(id);
    }
}

function saveURL() {
    const query = new URLSearchParams(controls.map(id => [id, $(id).value]));
    query.set("page", route);
    history.replaceState(null, "", "?" + query);
}

function resize() {
    const [width, height] = sizes[$("viewport").value];
    const scales = [];
    for (const {well, stage, frame} of panels) {
        const scale = Math.min(1, (well.clientWidth - 2) / width);
        scales.push(Math.round(scale * 100));
        stage.style.width = `${width * scale}px`;
        stage.style.height = `${height * scale}px`;
        frame.style.width = `${width}px`;
        frame.style.height = `${height}px`;
        frame.style.transform = `scale(${scale})`;
    }
    $("scale-note").textContent = `${width} × ${height} CSS px · canvas at ${scales[0]}%`;
}

const observer = new ResizeObserver(() => { if (panels.length) resize(); });

function render(preserveScroll = false) {
    const scroll = preserveScroll ? panels.map(panel => {
        try { return panel.frame.contentWindow.scrollY; }
        catch { return 0; }
    }) : [];
    observer.disconnect();
    panels = [];
    $("previews").replaceChildren();
    const mode = $("mode").value;
    $("scheme-control").hidden = mode === "schemes";
    $("previews").classList.toggle("single", mode === "single");
    const schemes = mode === "schemes" ? ["light", "dark"] : [$("scheme").value];
    const views = mode === "reference" ? ["reference", "current"] : ["current"];
    for (const view of views) for (const scheme of schemes) {
        const panel = document.createElement("section");
        panel.className = "panel";
        const heading = document.createElement("div");
        heading.className = "panel-heading";
        const title = document.createElement("strong");
        title.textContent = `${view === "reference" ? "Reference at startup" : "Current"} / ${scheme}`;
        const link = document.createElement("a");
        link.textContent = "Open page ↗";
        link.href = `/${view}${route}`;
        link.target = "_blank";
        link.rel = "noopener";
        link.title = "Standalone pages use your browser's color scheme and viewport";
        heading.append(title, link);
        const well = document.createElement("div");
        well.className = "well";
        const stage = document.createElement("div");
        stage.className = "stage";
        const frame = document.createElement("iframe");
        frame.title = `${title.textContent}: ${route}`;
        // Native inherited color-scheme drives prefers-color-scheme within the iframe.
        frame.style.colorScheme = scheme;
        frame.src = link.href;
        const index = panels.length;
        frame.addEventListener("load", () => {
            try {
                const path = frame.contentWindow.location.pathname;
                const next = path.replace(/^\/(current|reference)/, "");
                if (/^\/(current|reference)(\/|$)/.test(path) && next !== route) {
                    route = next || "/";
                    $("page").value = route;
                    saveURL();
                    render();
                    return;
                }
                frame.contentWindow.scrollTo(0, scroll[index] || 0);
            } catch { /* External navigation is outside the preview catalog. */ }
        });
        stage.append(frame);
        well.append(stage);
        panel.append(heading, well);
        $("previews").append(panel);
        panels.push({well, stage, frame});
        observer.observe(well);
    }
    resize();
    saveURL();
    $("description").textContent = mode === "reference"
        ? "A fixed reference beside your working changes. Restart the server to reset it."
        : "The same page, rendered by the real generator.";
}

for (const id of controls) $(id).addEventListener("change", () => {
    if (id === "page") route = $("page").value;
    render();
});

async function poll() {
    try {
        const response = await fetch("/__lab/status");
        if (!response.ok) throw new Error("Preview server unavailable");
        const data = await response.json();
        $("error").hidden = !data.error;
        $("error").textContent = data.error ? "Build failed. Showing the last successful preview.\n" + data.error : "";
        $("status").textContent = data.error ? "Build needs attention" : `● Live · build ${data.revision}`;
        if (revision !== data.revision) {
            const preserveScroll = revision !== -1;
            revision = data.revision;
            sizes = data.viewports;
            $("page").replaceChildren(...data.pages.map(page => new Option(page.label, page.path)));
            if (!data.pages.some(page => page.path === route)) route = "/";
            $("page").value = route;
            render(preserveScroll);
        }
    } catch {
        $("status").textContent = "Disconnected · restart style-lab to reconnect";
    } finally { setTimeout(poll, 1000); }
}
poll();
