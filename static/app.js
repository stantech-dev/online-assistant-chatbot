const messagesEl = document.getElementById("messages");
const chipsEl = document.getElementById("chips");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const refreshBtn = document.getElementById("refresh");

let history = [];   // the conversation so far: [{role, content}, ...]
let busy = false;   // true while waiting for an answer
let session = 0;    // changes on every reset, so old answers can be discarded

// Suggestion questions

const SUGGESTIONS = [
  "Which programmes are offered?",
  "Does Alupe have hostels?",
  "What are the fees?",
  "Where is Alupe University?",
  "How do I contact the university?",
];

// ---------- rendering ----------

// Turn special characters into harmless text BEFORE we build any HTML
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s) {
  return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

// Minimal markdown: **bold**, bullet lists, paragraphs
function renderMarkdown(text) {
  const lines = escapeHtml(text).split("\n");
  let html = "";
  let inList = false;

  for (const raw of lines) {
    const line = raw.trim();
    const bullet = line.match(/^[-•*]\s+(.*)/);

    if (bullet) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += "<li>" + inline(bullet[1]) + "</li>";
    } else {
      if (inList) { html += "</ul>"; inList = false; }
      const clean = line.replace(/^#{1,6}\s*/, "");  // drop markdown headings
      if (clean) html += "<p>" + inline(clean) + "</p>";
    }
  }
  if (inList) html += "</ul>";
  return html;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addUser(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.textContent = text;          // textContent: user text can never inject HTML
  messagesEl.appendChild(div);
  scrollToBottom();
}

function addBot(text) {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = renderMarkdown(text);   // safe: escaped first in renderMarkdown
  messagesEl.appendChild(div);
  scrollToBottom();
}

function addTyping() {
  const div = document.createElement("div");
  div.className = "msg bot typing";
  div.innerHTML = "<span></span><span></span><span></span>";
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

// ---------- talking to the backend ----------

async function send(text) {
  text = text.trim();
  if (busy || !text) return;

  const mySession = session;       // remember which chat this request belongs to
  busy = true;
  sendBtn.disabled = true;
  chipsEl.innerHTML = "";          // hide suggestions after the first message
  addUser(text);
  input.value = "";
  const typing = addTyping();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text, history: history.slice(-6) }),
    });
    if (mySession !== session) return;   // chat was reset while waiting: drop the answer

    if (res.status === 429) {
      typing.remove();
      addBot("You're sending messages too quickly. Please wait a moment and try again.");
      return;
    }
    if (!res.ok) throw new Error("Server error " + res.status);

    const data = await res.json();
    if (mySession !== session) return;
    typing.remove();
    addBot(data.answer);

    // Remember this exchange (only on success). Long answers are trimmed
    // because the server limits the size of each history message.
    history.push({ role: "user", content: text });
    history.push({ role: "assistant", content: data.answer.slice(0, 1500) });
    history = history.slice(-20);
  } catch (err) {
    console.error(err);
    if (mySession !== session) return;
    typing.remove();
    addBot("Sorry, I couldn't reach the assistant. Please try again in a moment.");
  } finally {
    if (mySession === session) {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }
}

// ---------- wiring it up ----------

function resetChat() {
  session += 1;                    // invalidates any request still in flight
  history = [];
  busy = false;
  sendBtn.disabled = false;
  messagesEl.innerHTML = "";
  chipsEl.innerHTML = "";
  input.value = "";

  addBot("Hello! I'm the AU Smart Assistant. Ask me about Alupe University, or pick a question below.");
  for (const q of SUGGESTIONS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = q;
    btn.addEventListener("click", () => send(q));
    chipsEl.appendChild(btn);
  }
  input.focus();
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  send(input.value);
});
refreshBtn.addEventListener("click", resetChat);

resetChat();   // builds the first screen