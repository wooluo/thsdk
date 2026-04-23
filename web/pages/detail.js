import { api } from "../js/api.js";
import {
    formatPrice, formatChange, formatChangePct, formatVolume, formatAmount,
    colorClass, clear
} from "../js/utils.js";

let chart = null;
let refreshTimer = null;
let currentInterval = "day";
let currentThsCode = "";

const INTERVALS = [
    { label: "分时", value: "intraday" },
    { label: "1分", value: "1m" },
    { label: "5分", value: "5m" },
    { label: "15分", value: "15m" },
    { label: "30分", value: "30m" },
    { label: "60分", value: "60m" },
    { label: "日K", value: "day" },
    { label: "周K", value: "week" },
    { label: "月K", value: "month" },
];

export function renderDetail(thsCode) {
    const app = document.getElementById("app");
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
    currentThsCode = thsCode;
    currentInterval = "day";

    app.innerHTML = `
        <div id="detail-loading" class="loading">加载中...</div>
        <div id="detail-content" style="display:none;">
            <div class="detail-header">
                <span class="name" id="d-name">--</span>
                <span class="code" id="d-code">--</span>
                <span class="price" id="d-price">--</span>
                <span class="change-info" id="d-change">--</span>
            </div>
            <div class="detail-stats" id="d-stats"></div>
            <div class="chart-section">
                <div class="chart-toolbar" id="chart-toolbar"></div>
                <div id="chart-container"></div>
            </div>
            <div class="two-col">
                <div>
                    <div class="section-title">买卖盘口</div>
                    <div class="card"><table class="depth-table" id="depth-table"></table></div>
                </div>
                <div>
                    <div class="section-title">大单资金流</div>
                    <div class="card" id="big-order-panel">加载中...</div>
                </div>
            </div>
        </div>
    `;

    buildToolbar();
    loadAll(thsCode);
    refreshTimer = setInterval(() => loadQuote(thsCode), 5000);
}

function buildToolbar() {
    const toolbar = document.getElementById("chart-toolbar");
    for (const iv of INTERVALS) {
        const btn = document.createElement("button");
        btn.textContent = iv.label;
        btn.dataset.value = iv.value;
        if (iv.value === currentInterval) btn.className = "active";
        btn.addEventListener("click", () => {
            toolbar.querySelectorAll("button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentInterval = iv.value;
            loadChart(currentThsCode, iv.value);
        });
        toolbar.appendChild(btn);
    }
}

async function loadAll(thsCode) {
    await Promise.all([
        loadQuote(thsCode),
        loadChart(thsCode, currentInterval),
        loadDepth(thsCode),
        loadBigOrder(thsCode),
    ]);
}

async function loadQuote(thsCode) {
    try {
        // Determine market from code prefix
        const prefix = thsCode.slice(0, 4);
        let method = api.marketCN.bind(api);
        if (["UNQQ", "UNQS"].includes(prefix)) method = api.marketUS.bind(api);
        else if (["UHKM", "UHKG"].includes(prefix)) method = api.marketHK.bind(api);
        else if (["USHI", "USZI"].includes(prefix)) method = api.marketIndex.bind(api);

        const res = await method(thsCode, "汇总");
        if (!res.success || !Array.isArray(res.data) || res.data.length === 0) {
            // fallback to 基础数据
            const res2 = await method(thsCode, "基础数据");
            if (res2.success && Array.isArray(res2.data) && res2.data.length > 0) {
                renderQuote(res2.data[0]);
            }
            return;
        }
        renderQuote(res.data[0]);
    } catch (e) { console.error("quote error", e); }
}

function renderQuote(d) {
    document.getElementById("detail-loading").style.display = "none";
    document.getElementById("detail-content").style.display = "";

    const price = Number(d["价格"] || 0);
    const change = Number(d["涨跌"] || 0);
    const changePct = Number(d["涨幅"] || 0);
    const cls = colorClass(change);

    document.getElementById("d-name").textContent = d["名称"] || "--";
    document.getElementById("d-code").textContent = d["代码"] || currentThsCode;
    const priceEl = document.getElementById("d-price");
    priceEl.textContent = formatPrice(price);
    priceEl.className = `price ${cls}`;
    document.getElementById("d-change").innerHTML =
        `<span class="${cls}">${formatChange(change)} (${formatChangePct(changePct)})</span>`;

    const stats = document.getElementById("d-stats");
    stats.innerHTML = `
        <div class="stat">开盘: <span>${formatPrice(d["开盘价"])}</span></div>
        <div class="stat">最高: <span class="up">${formatPrice(d["最高价"])}</span></div>
        <div class="stat">最低: <span class="down">${formatPrice(d["最低价"])}</span></div>
        <div class="stat">昨收: <span>${formatPrice(d["昨收价"])}</span></div>
        <div class="stat">成交量: <span>${formatVolume(d["成交量"])}</span></div>
        <div class="stat">成交额: <span>${formatAmount(d["总金额"])}</span></div>
        <div class="stat">换手率: <span>${d["换手率"] ? Number(d["换手率"]).toFixed(2) + "%" : "--"}</span></div>
    `;
}

async function loadChart(thsCode, interval) {
    const container = document.getElementById("chart-container");
    if (!container) return;

    if (interval === "intraday") {
        await loadIntradayChart(thsCode);
        return;
    }

    try {
        const res = await api.klines(thsCode, 200, interval, "");
        if (!res.success || !Array.isArray(res.data)) return;
        renderKlineChart(res.data);
    } catch (e) { console.error("kline error", e); }
}

function renderKlineChart(data) {
    const container = document.getElementById("chart-container");
    container.innerHTML = "";

    if (typeof LightweightCharts === "undefined") {
        container.innerHTML = '<div style="padding:20px;color:var(--text-secondary);">图表库加载失败</div>';
        return;
    }

    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 420,
        layout: {
            background: { type: "solid", color: "#1c2128" },
            textColor: "#8b949e",
            fontSize: 12,
        },
        grid: {
            vertLines: { color: "#262c36" },
            horzLines: { color: "#262c36" },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: "#30363d" },
        timeScale: { borderColor: "#30363d", timeVisible: true },
    });

    const candleSeries = chart.addCandlestickSeries({
        upColor: "#f85149",
        downColor: "#3fb950",
        borderUpColor: "#f85149",
        borderDownColor: "#3fb950",
        wickUpColor: "#f85149",
        wickDownColor: "#3fb950",
    });

    const rows = data.map(item => {
        const time = item["时间"];
        let ts;
        if (typeof time === "string" && time.includes("T")) {
            ts = Math.floor(new Date(time).getTime() / 1000);
        } else {
            ts = Number(time);
        }
        return {
            time: ts,
            open: Number(item["开盘价"] || 0),
            high: Number(item["最高价"] || 0),
            low: Number(item["最低价"] || 0),
            close: Number(item["价格"] || item["收盘价"] || 0),
        };
    }).sort((a, b) => a.time - b.time);

    candleSeries.setData(rows);

    // Volume
    const volumeSeries = chart.addHistogramSeries({
        color: "#30363d",
        priceFormat: { type: "volume" },
        priceScaleId: "",
    });
    chart.priceScale("").applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
    });

    const volRows = data.map(item => {
        const time = item["时间"];
        let ts;
        if (typeof time === "string" && time.includes("T")) {
            ts = Math.floor(new Date(time).getTime() / 1000);
        } else {
            ts = Number(time);
        }
        const close = Number(item["价格"] || item["收盘价"] || 0);
        const open = Number(item["开盘价"] || 0);
        return {
            time: ts,
            value: Number(item["成交量"] || 0),
            color: close >= open ? "rgba(248,81,73,0.3)" : "rgba(63,185,80,0.3)",
        };
    }).sort((a, b) => a.time - b.time);
    volumeSeries.setData(volRows);

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    });
    resizeObserver.observe(container);
}

async function loadIntradayChart(thsCode) {
    const container = document.getElementById("chart-container");
    container.innerHTML = "";

    try {
        const res = await api.intraday(thsCode);
        if (!res.success || !Array.isArray(res.data)) return;

        if (typeof LightweightCharts === "undefined") {
            container.innerHTML = '<div style="padding:20px;color:var(--text-secondary);">图表库加载失败</div>';
            return;
        }

        chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 420,
            layout: {
                background: { type: "solid", color: "#1c2128" },
                textColor: "#8b949e",
                fontSize: 12,
            },
            grid: {
                vertLines: { color: "#262c36" },
                horzLines: { color: "#262c36" },
            },
            rightPriceScale: { borderColor: "#30363d" },
            timeScale: { borderColor: "#30363d", timeVisible: true, secondsVisible: false },
        });

        const lineSeries = chart.addLineSeries({
            color: "#58a6ff",
            lineWidth: 2,
        });

        const rows = res.data.map(item => {
            const time = item["时间"];
            let ts;
            if (typeof time === "string" && time.includes("T")) {
                ts = Math.floor(new Date(time).getTime() / 1000);
            } else {
                ts = Number(time);
            }
            return {
                time: ts,
                value: Number(item["价格"] || 0),
            };
        }).sort((a, b) => a.time - b.time);

        lineSeries.setData(rows);
        chart.timeScale().fitContent();
    } catch (e) { console.error("intraday error", e); }
}

async function loadDepth(thsCode) {
    const table = document.getElementById("depth-table");
    if (!table) return;

    try {
        const res = await api.depth(thsCode);
        if (!res.success || !res.data) return;
        const d = Array.isArray(res.data) ? res.data[0] : res.data;
        if (!d) return;

        let html = "";
        // Ask side (sell) reversed
        for (let i = 10; i >= 1; i--) {
            const price = d[`卖${i}价`];
            const vol = d[`卖${i}量`];
            html += `<tr><td>卖${i}</td><td class="ask">${formatPrice(price)}</td><td>${formatVolume(vol)}</td></tr>`;
        }
        // Bid side (buy)
        for (let i = 1; i <= 10; i++) {
            const price = d[`买${i}价`];
            const vol = d[`买${i}量`];
            html += `<tr><td>买${i}</td><td class="bid">${formatPrice(price)}</td><td>${formatVolume(vol)}</td></tr>`;
        }
        table.innerHTML = html;
    } catch (e) { console.error("depth error", e); }
}

async function loadBigOrder(thsCode) {
    const panel = document.getElementById("big-order-panel");
    if (!panel) return;

    try {
        const res = await api.bigOrderFlow(thsCode);
        if (!res.success || !res.data) {
            panel.innerHTML = '<div style="padding:12px;color:var(--text-secondary);">暂无数据</div>';
            return;
        }
        const d = Array.isArray(res.data) ? res.data[0] : res.data;
        if (!d) {
            panel.innerHTML = '<div style="padding:12px;color:var(--text-secondary);">暂无数据</div>';
            return;
        }

        const mainIn = Number(d["大单流入"] || d["资金流入"] || 0);
        const mainOut = Number(d["大单流出"] || d["资金流出"] || 0);
        const net = mainIn - mainOut;
        const cls = colorClass(net);

        panel.innerHTML = `
            <div style="padding:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                    <div>
                        <div style="color:var(--text-secondary);font-size:12px;">主力净流入</div>
                        <div class="${cls}" style="font-size:18px;font-weight:700;">${formatAmount(net)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:var(--text-secondary);font-size:12px;">主力净量</div>
                        <div class="${cls}" style="font-size:18px;font-weight:700;">${d["主力净量"] ? Number(d["主力净量"]).toFixed(2) + "%" : "--"}</div>
                    </div>
                </div>
                <div class="flow-bar">
                    <div class="in" style="width:${mainIn / (mainIn + mainOut || 1) * 100}%"></div>
                    <div class="out" style="width:${mainOut / (mainIn + mainOut || 1) * 100}%"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-secondary);margin-top:4px;">
                    <span class="up">流入 ${formatAmount(mainIn)}</span>
                    <span class="down">流出 ${formatAmount(mainOut)}</span>
                </div>
            </div>
        `;
    } catch (e) {
        panel.innerHTML = '<div style="padding:12px;color:var(--text-secondary);">加载失败</div>';
        console.error("big order error", e);
    }
}
