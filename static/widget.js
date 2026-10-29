(function () {
  if (window.__chatWidgetLoaded) return;
  window.__chatWidgetLoaded = true;

  var script = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var origin = new URL(script.src).origin;   // where the bot is hosted
  var BRAND = "#14532d";                     // bubble colour

  var ICON_CHAT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>';
  var ICON_CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

  var CSS = [
    ".ka-launcher{position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;border:none;padding:0;background:" + BRAND + ";color:#fff;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);z-index:2147483000;display:flex;align-items:center;justify-content:center}",
    ".ka-launcher:hover{filter:brightness(1.15)}",
    ".ka-launcher svg{width:26px;height:26px}",
    ".ka-panel{position:fixed;right:20px;bottom:88px;width:380px;height:560px;max-width:calc(100vw - 24px);max-height:calc(100vh - 110px);border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 8px 30px rgba(0,0,0,.3);z-index:2147483000;display:none}",
    ".ka-panel.ka-open{display:block}",
    ".ka-panel iframe{width:100%;height:100%;border:0}",
    "@media (max-width:480px){.ka-panel{left:8px;right:8px;width:auto;max-width:none;bottom:84px;height:calc(100vh - 100px);height:calc(100dvh - 100px);max-height:none}}"
  ].join("");

  function init() {
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    var panel = document.createElement("div");
    panel.className = "ka-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Chat assistant");

    var launcher = document.createElement("button");
    launcher.className = "ka-launcher";
    launcher.type = "button";
    launcher.innerHTML = ICON_CHAT;
    launcher.setAttribute("aria-label", "Open chat assistant");
    launcher.setAttribute("aria-expanded", "false");

    var frame = null;

    function setOpen(open) {
      panel.classList.toggle("ka-open", open);
      launcher.innerHTML = open ? ICON_CLOSE : ICON_CHAT;
      launcher.setAttribute("aria-expanded", String(open));
      launcher.setAttribute("aria-label", open ? "Close chat assistant" : "Open chat assistant");
      if (open && !frame) {              // load the chat page only on first open
        frame = document.createElement("iframe");
        frame.src = origin + "/";
        frame.title = "Chat assistant";
        panel.appendChild(frame);
      }
    }

    launcher.addEventListener("click", function () {
      setOpen(!panel.classList.contains("ka-open"));
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel.classList.contains("ka-open")) setOpen(false);
    });

    document.body.appendChild(panel);
    document.body.appendChild(launcher);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();