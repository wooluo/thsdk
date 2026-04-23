import { api } from "../js/api.js";
import {
    formatPrice, formatChangePct, colorClass, formatVolume
} from "../js/utils.js";

let currentTab = "industry";
let currentSectorCode = null;

export function renderSector() {
    const app = document.getElementById("app");

    app.innerHTML = `
        <div class="tabs" id="sector-tabs">
            <button class="active" data-tab="industry">行业板块</button>
            <button data-tab="concept">概念板块</button>
        </div>
        <div class="sector-layout">
            <div class="card sector-list" id="sector-list">
                <div class="loading">加载中...</div>
            </div>
            <div>
                <div class="section-title" id="sector-title">选择板块查看成分股</div>
                <div class="card"><div class="table-wrap">
                    <table id="constituents-table">
                        <thead><tr><th>名称</th><th>代码</th><th>价格</th><th>涨幅</th><th>成交量</th></tr></thead>
                        <tbody id="constituents-body"></tbody>
                    </table>
                </div></div>
            </div>
        </div>
    `;

    // Tab switching
    const tabs = document.getElementById("sector-tabs");
    tabs.addEventListener("click", (e) => {
        if (e.target.tagName !== "BUTTON") return;
        tabs.querySelectorAll("button").forEach(b => b.classList.remove("active"));
        e.target.classList.add("active");
        currentTab = e.target.dataset.tab;
        currentSectorCode = null;
        loadSectors();
    });

    loadSectors();
}

async function loadSectors() {
    const list = document.getElementById("sector-list");
    list.innerHTML = '<div class="loading">加载中...</div>';

    try {
        const res = currentTab === "industry" ? await api.industry() : await api.concept();
        if (!res.success || !Array.isArray(res.data)) {
            list.innerHTML = `<div class="error">加载失败: ${res.error || "未知错误"}</div>`;
            return;
        }

        list.innerHTML = "";
        // Sort by change pct if available
        const items = res.data.sort((a, b) => {
            const pctA = Number(a["涨幅"] || 0);
            const pctB = Number(b["涨幅"] || 0);
            return pctB - pctA;
        });

        for (const item of items) {
            const div = document.createElement("div");
            div.className = "sector-item";
            const pct = Number(item["涨幅"] || 0);
            const cls = colorClass(pct);
            const linkCode = item["link_code"] || item["THSCODE"] || item["代码"] || "";
            div.innerHTML = `
                <span>${item["名称"] || "--"}</span>
                <span class="${cls}">${formatChangePct(pct)}</span>
            `;
            div.addEventListener("click", () => {
                list.querySelectorAll(".sector-item").forEach(s => s.classList.remove("active"));
                div.classList.add("active");
                loadConstituents(linkCode, item["名称"]);
            });
            list.appendChild(div);
        }
    } catch (e) {
        list.innerHTML = `<div class="error">加载出错: ${e.message}</div>`;
    }
}

async function loadConstituents(linkCode, name) {
    currentSectorCode = linkCode;
    const title = document.getElementById("sector-title");
    const tbody = document.getElementById("constituents-body");
    title.textContent = name || linkCode;
    tbody.innerHTML = '<tr><td colspan="5" class="loading">加载中...</td></tr>';

    try {
        const res = await api.blockConstituents(linkCode);
        if (!res.success || !Array.isArray(res.data)) {
            tbody.innerHTML = `<tr><td colspan="5" class="error">加载失败</td></tr>`;
            return;
        }

        // Get codes for price data
        const codes = res.data.map(item => {
            if (typeof item === "string") return item;
            return item["THSCODE"] || item["代码"] || item["code"] || "";
        }).filter(Boolean);

        if (codes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary);">无成分股</td></tr>';
            return;
        }

        // Fetch prices in batches of 50
        const allPriceData = [];
        for (let i = 0; i < codes.length; i += 50) {
            const batch = codes.slice(i, i + 50);
            try {
                const priceRes = await api.marketCN(batch.join(","), "扩展2");
                if (priceRes.success && Array.isArray(priceRes.data)) {
                    allPriceData.push(...priceRes.data);
                }
            } catch (e) { /* skip batch */ }
        }

        // Build name map from constituents
        const nameMap = {};
        for (const item of res.data) {
            if (typeof item === "object") {
                const code = item["THSCODE"] || item["代码"] || "";
                nameMap[code] = item["名称"] || item["Name"] || "";
            }
        }

        // Sort by change pct
        allPriceData.sort((a, b) => {
            const pctA = Number(a["涨幅"] || 0);
            const pctB = Number(b["涨幅"] || 0);
            return pctB - pctA;
        });

        tbody.innerHTML = "";
        for (const item of allPriceData) {
            const pct = Number(item["涨幅"] || 0);
            const cls = colorClass(pct);
            const code = item["代码"] || item["THSCODE"] || "";
            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";
            tr.addEventListener("click", () => {
                if (code) window.location.hash = `#/stock/${code}`;
            });
            tr.innerHTML = `
                <td>${item["名称"] || nameMap[code] || "--"}</td>
                <td>${code}</td>
                <td class="${cls}">${formatPrice(item["价格"])}</td>
                <td class="${cls}">${formatChangePct(pct)}</td>
                <td>${formatVolume(item["成交量"])}</td>
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="error">加载出错: ${e.message}</td></tr>`;
    }
}
