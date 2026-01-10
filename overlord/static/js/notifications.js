/* notifications.js — shared toast notification system */

function showNotification(type, message) {
    const container = document.getElementById("notification-container");
    if (!container) {
        console.error("Notification container #notification-container not found");
        return;
    }

    const box = document.createElement("div");
    box.className = `notification ${type} toast-notification`;
    box.style.pointerEvents = "auto";
    box.style.minWidth = "300px";
    box.style.maxWidth = "600px";
    box.style.marginBottom = "0.5rem";
    box.style.boxShadow = "0 2px 8px rgba(0,0,0,0.2)";

    const btn = document.createElement("button");
    btn.className = "delete";
    btn.onclick = () => hideToast(box);
    box.appendChild(btn);

    const text = document.createElement("span");
    text.textContent = message;
    box.appendChild(text);

    container.appendChild(box);

    // Auto-hide after 5 seconds
    setTimeout(() => hideToast(box), 5000);
}

function hideToast(box) {
    if (!box) {
        return;
    }
    box.classList.add("toast-hide");
    box.addEventListener("animationend", () => box.remove(), { once: true });
}
