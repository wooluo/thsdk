import { api } from "../js/api.js";
import { debounce, el, clear } from "../js/utils.js";

export function renderSearch() {
    const app = document.getElementById("app");
    const params = new URLSearchParams(window.location.hash.split("?")[1] || "");
    const initialQuery = params.get("q") || "";

    app.innerHTML = `
        <div class="search-container">
            <input type="text" id="search-input" placeholder="输入股票名称或代码..." value="${initialQuery}" autofocus>
            <div class="search-results" id="search-results"></div>
        </div>
    `;

    const input = document.getElementById("search-input");
    const results = document.getElementById("search-results");

    const doSearch = debounce(async (q) => {
        if (!q.trim()) { results.innerHTML = ""; return; }
        results.innerHTML = '<div class="loading">搜索中...</div>';
        try {
            const res = await api.search(q.trim());
            if (!res.success) {
                results.innerHTML = `<div class="error">${res.error || "搜索失败"}</div>`;
                return;
            }
            const data = res.data;
            if (!Array.isArray(data) || data.length === 0) {
                results.innerHTML = '<div style="padding:20px;color:var(--text-secondary);text-align:center;">无结果</div>';
                return;
            }
            results.innerHTML = "";
            for (const item of data) {
                const thsCode = item["THSCODE"] || `${item["MarketStr"] || ""}${item["Code"] || ""}`;
                const name = item["Name"] || item["名称"] || "--";
                const code = item["Code"] || item["代码"] || "--";
                const market = item["MarketDisplay"] || item["MarketStr"] || "";

                const div = document.createElement("div");
                div.className = "search-item";
                div.innerHTML = `
                    <div>
                        <span class="name">${name}</span>
                        <span class="code" style="margin-left:8px;">${thsCode}</span>
                    </div>
                    <span class="code">${market}</span>
                `;
                div.addEventListener("click", () => {
                    if (thsCode) window.location.hash = `#/stock/${thsCode}`;
                });
                results.appendChild(div);
            }
        } catch (e) {
            results.innerHTML = `<div class="error">搜索出错: ${e.message}</div>`;
        }
    }, 300);

    input.addEventListener("input", (e) => doSearch(e.target.value));

    if (initialQuery) {
        doSearch(initialQuery);
    }
}
