/* static/js/api.js — shared REST API helper */

async function apiRequest(method, url, payload = null) {
    const options = {
        method: method,
        headers: { "Content-Type": "application/json" }
    };

    if (payload !== null) {
        options.body = JSON.stringify(payload);
    }

    let response;
    let result;

    try {
        response = await fetch(url, options);
        result = await response.json();
    } catch (e) {
        showNotification("is-danger", "Network error while contacting API");
        throw e;
    }

    if (!response.ok || !result || result.status !== "ok") {
        const msg =
            result && result.message
                ? result.message
                : "API error";
        showNotification("is-danger", msg);
        throw new Error(msg);
    }

    if (result.message) {
        showNotification("is-success", result.message);
    }

    return result.data || null;
}
