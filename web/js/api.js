const API_BASE = window.__THS_API_BASE__ || "";

async function request(path, params = {}) {
    const url = new URL(API_BASE + path, window.location.origin);
    for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") {
            url.searchParams.set(k, v);
        }
    }
    const resp = await fetch(url.toString());
    return resp.json();
}

export const api = {
    // Market
    marketCN(codes, queryKey = "基础数据") { return request("/api/market/cn", { codes, query_key: queryKey }); },
    marketUS(codes, queryKey = "基础数据") { return request("/api/market/us", { codes, query_key: queryKey }); },
    marketHK(codes, queryKey = "基础数据") { return request("/api/market/hk", { codes, query_key: queryKey }); },
    marketIndex(codes, queryKey = "基础数据") { return request("/api/market/index", { codes, query_key: queryKey }); },
    marketBlock(codes, queryKey = "基础数据") { return request("/api/market/block", { codes, query_key: queryKey }); },

    // Stock
    klines(thsCode, count = 100, interval = "day", adjust = "") {
        return request("/api/stock/klines", { ths_code: thsCode, count, interval, adjust });
    },
    intraday(thsCode) { return request("/api/stock/intraday", { ths_code: thsCode }); },
    depth(thsCode) { return request("/api/stock/depth", { ths_code: thsCode }); },
    bigOrderFlow(thsCode) { return request("/api/stock/big-order-flow", { ths_code: thsCode }); },
    callAuction(thsCode) { return request("/api/stock/call-auction", { ths_code: thsCode }); },

    // Catalog
    industry() { return request("/api/catalog/industry"); },
    concept() { return request("/api/catalog/concept"); },
    stockCN() { return request("/api/catalog/stock-cn"); },
    stockUS() { return request("/api/catalog/stock-us"); },
    stockHK() { return request("/api/catalog/stock-hk"); },
    indexList() { return request("/api/catalog/index-list"); },
    blockConstituents(linkCode) { return request("/api/catalog/block-constituents", { link_code: linkCode }); },

    // Misc
    search(pattern) { return request("/api/search", { pattern }); },
    completeCode(thsCode) { return request("/api/complete-code", { ths_code: thsCode }); },
    news(code = "1A0001", market = "USHI") { return request("/api/news", { code, market }); },
    ipoToday() { return request("/api/ipo/today"); },

    // Health
    health() { return request("/api/health"); },
};
