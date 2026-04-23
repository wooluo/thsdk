import { api } from "../js/api.js";
import {
    formatPrice, formatChange, formatChangePct, formatVolume, formatAmount,
    colorClass, el, clear, INDEX_CODES
} from "../js/utils.js";

let refreshTimer = null;

export function renderOverview() {
    const app = document.getElementById("app");
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }

    app.innerHTML = `
        <div class="section-title">主要指数</div>
        <div class="index-grid" id="index-grid"></div>
        <div class="two-col">
            <div>
                <div class="section-title">A股涨幅榜 Top 20</div>
                <div class="card"><div class="table-wrap"><table id="gainers-table">
                    <thead><tr><th>名称</th><th>代码</th><th>价格</th><th>涨幅</th><th>成交额</th></tr></thead>
                    <tbody></tbody>
                </table></div></div>
            </div>
            <div>
                <div class="section-title">A股跌幅榜 Top 20</div>
                <div class="card"><div class="table-wrap"><table id="losers-table">
                    <thead><tr><th>名称</th><th>代码</th><th>价格</th><th>涨幅</th><th>成交额</th></tr></thead>
                    <tbody></tbody>
                </table></div></div>
            </div>
        </div>
    `;
    loadIndexData();
    loadTopStocks();
    refreshTimer = setInterval(() => { loadIndexData(); loadTopStocks(); }, 5000);
}

async function loadIndexData() {
    const codes = Object.values(INDEX_CODES).join(",");
    try {
        const res = await api.marketIndex(codes);
        if (!res.success || !Array.isArray(res.data)) return;
        renderIndexCards(res.data);
    } catch (e) { console.error("index error", e); }
}

function renderIndexCards(data) {
    const grid = document.getElementById("index-grid");
    if (!grid) return;

    const names = Object.keys(INDEX_CODES);
    grid.innerHTML = "";
    for (let i = 0; i < names.length; i++) {
        const name = names[i];
        const item = data[i] || {};
        const price = Number(item["价格"] || 0);
        const change = Number(item["涨跌"] || 0);
        const changePct = Number(item["涨幅"] || 0);
        const vol = Number(item["总金额"] || 0);
        const cls = colorClass(change);

        const card = document.createElement("div");
        card.className = `card index-card`;
        card.innerHTML = `
            <div class="name">${name}</div>
            <div class="price ${cls}">${formatPrice(price)}</div>
            <div class="change ${cls}">${formatChange(change)} ${formatChangePct(changePct)}</div>
            <div class="volume">成交额 ${formatAmount(vol)}</div>
        `;
        grid.appendChild(card);
    }
}

async function loadTopStocks() {
    try {
        // Load A-share list and then get prices
        const listRes = await api.stockCN();
        if (!listRes.success || !Array.isArray(listRes.data) || listRes.data.length === 0) return;

        const codes = listRes.data.slice(0, 100).map(item => {
            if (typeof item === "string") return item;
            return item["THSCODE"] || item["代码"] || "";
        }).filter(Boolean);

        if (codes.length === 0) return;

        const res = await api.marketCN(codes.slice(0, 50).join(","), "扩展2");
        if (!res.success || !Array.isArray(res.data)) return;

        const sorted = [...res.data].sort((a, b) => {
            const pctA = Number(a["涨幅"] || 0);
            const pctB = Number(b["涨幅"] || 0);
            return pctB - pctA;
        });

        const gainers = sorted.slice(0, 20);
        const losers = sorted.slice(-20).reverse();

        fillTable("gainers-table", gainers);
        fillTable("losers-table", losers);
    } catch (e) { console.error("stocks error", e); }
}

function fillTable(tableId, rows) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;
    tbody.innerHTML = "";
    for (const row of rows) {
        const pct = Number(row["涨幅"] || 0);
        const cls = colorClass(pct);
        const tr = document.createElement("tr");
        tr.style.cursor = "pointer";
        tr.addEventListener("click", () => {
            const code = row["代码"] || row["THSCODE"] || "";
            if (code) window.location.hash = `#/stock/${code}`;
        });
        tr.innerHTML = `
            <td>${row["名称"] || "--"}</td>
            <td>${row["代码"] || "--"}</td>
            <td class="${cls}">${formatPrice(row["价格"])}</td>
            <td class="${cls}">${formatChangePct(pct)}</td>
            <td>${formatAmount(row["总金额"])}</td>
        `;
        tbody.appendChild(tr);
    }
}
