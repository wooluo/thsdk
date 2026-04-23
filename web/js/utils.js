export function formatPrice(val) {
    if (val == null || isNaN(val)) return "--";
    return Number(val).toFixed(2);
}

export function formatChange(val) {
    if (val == null || isNaN(val)) return "--";
    return (val > 0 ? "+" : "") + Number(val).toFixed(2);
}

export function formatChangePct(val) {
    if (val == null || isNaN(val)) return "--";
    return (val > 0 ? "+" : "") + Number(val).toFixed(2) + "%";
}

export function formatVolume(vol) {
    if (vol == null || isNaN(vol)) return "--";
    if (vol >= 1e8) return (vol / 1e8).toFixed(2) + "亿";
    if (vol >= 1e4) return (vol / 1e4).toFixed(2) + "万";
    return vol.toString();
}

export function formatAmount(amt) {
    if (amt == null || isNaN(amt)) return "--";
    if (amt >= 1e8) return (amt / 1e8).toFixed(2) + "亿";
    if (amt >= 1e4) return (amt / 1e4).toFixed(2) + "万";
    return amt.toFixed(2);
}

export function colorClass(val) {
    if (val == null || isNaN(val)) return "";
    return val > 0 ? "up" : val < 0 ? "down" : "";
}

export function formatTime(timeStr) {
    if (!timeStr) return "";
    if (typeof timeStr === "string") {
        // Handle ISO datetime
        if (timeStr.includes("T")) {
            const d = new Date(timeStr);
            return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
        }
        return timeStr;
    }
    return String(timeStr);
}

export function formatDate(timeStr) {
    if (!timeStr) return "";
    if (typeof timeStr === "string" && timeStr.includes("T")) {
        const d = new Date(timeStr);
        return d.toLocaleDateString("zh-CN");
    }
    return String(timeStr);
}

export function debounce(fn, ms) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

export function el(tag, attrs = {}, children = []) {
    const elem = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === "className") elem.className = v;
        else if (k === "innerHTML") elem.innerHTML = v;
        else if (k.startsWith("on")) elem.addEventListener(k.slice(2).toLowerCase(), v);
        else elem.setAttribute(k, v);
    }
    for (const child of (Array.isArray(children) ? children : [children])) {
        if (typeof child === "string") elem.appendChild(document.createTextNode(child));
        else if (child) elem.appendChild(child);
    }
    return elem;
}

export function clear(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
}

export const INDEX_CODES = {
    "上证指数": "USHI000001",
    "深证成指": "USZI399001",
    "创业板指": "USZI399006",
    "恒生指数": "UHKMHSI",
    "纳斯达克": "UNQQIXIC",
};

export function getStockField(data, field) {
    if (!data || typeof data !== "object") return null;
    return data[field] ?? null;
}
