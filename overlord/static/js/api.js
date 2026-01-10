// static/js/api.js

async function apiRequest(method, url, data = null) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (data !== null) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const json = await response.json().catch(() => ({}));

        if (!response.ok || json.status === "error") {
            const msg = json.message || `Request failed (${response.status})`;
            if (typeof showNotification === "function") {
                showNotification("is-danger", msg);
            }
            throw new Error(msg);
        }

        if (typeof showNotification === "function" && json.message) {
            showNotification("is-success", json.message);
        }

        return json.data || {};
    } catch (err) {
        if (typeof showNotification === "function") {
            showNotification("is-danger", err.message);
        }
        throw err;
    }
}
