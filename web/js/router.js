import { api } from "./api.js";
import { renderOverview } from "../pages/overview.js";
import { renderDetail } from "../pages/detail.js";
import { renderSearch } from "../pages/search.js";
import { renderSector } from "../pages/sectors.js";
import { debounce } from "./utils.js";

const app = document.getElementById("app");

const routes = [
    { pattern: /^\/$/, handler: renderOverview },
    { pattern: /^\/stock\/(.+)$/, handler: (m) => renderDetail(decodeURIComponent(m[1])) },
    { pattern: /^\/search$/, handler: renderSearch },
    { pattern: /^\/sectors$/, handler: renderSector },
];

function navigate() {
    const hash = window.location.hash.slice(1) || "/";
    for (const route of routes) {
        const match = hash.match(route.pattern);
        if (match) {
            route.handler(match);
            return;
        }
    }
    app.innerHTML = '<div class="error">页面未找到</div>';
}

window.addEventListener("hashchange", navigate);
navigate();

// Nav search
const navSearch = document.getElementById("nav-search-input");
navSearch.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && navSearch.value.trim()) {
        window.location.hash = `#/search?q=${encodeURIComponent(navSearch.value.trim())}`;
    }
});
