document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const messagesContainer = document.getElementById("messages-container");
  const clearBtn = document.getElementById("clear-chat-btn");
  const toggleInspectorBtn = document.getElementById("toggle-inspector-btn");
  const inspectorPane = document.getElementById("inspector-pane");

  // Metrics elements
  const metricGrounding = document.getElementById("metric-grounding");
  const metricRetrieval = document.getElementById("metric-retrieval");
  const metricRisk = document.getElementById("metric-risk");
  const metricSafety = document.getElementById("metric-safety");
  const retrievedSourcesList = document.getElementById("retrieved-sources-list");

  // Auto-resize textarea
  userInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
    if (this.value.trim() === "") {
      this.style.height = "auto";
    }
  });

  // Enter to send (Shift+Enter for newline)
  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  toggleInspectorBtn.addEventListener("click", () => {
    inspectorPane.classList.toggle("collapsed");
  });

  clearBtn.addEventListener("click", () => {
    if (confirm("Clear conversation history?")) {
      messagesContainer.innerHTML = "";
      addBotWelcomeMessage();
      resetMetrics();
    }
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    userInput.value = "";
    userInput.style.height = "auto";

    // 1. Append User Message
    appendMessage("user", query);

    // 2. Append Loading Indicator
    const loaderId = appendLoadingMessage();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query })
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }

      const data = await response.json();
      removeMessage(loaderId);

      // 3. Append Bot Response
      appendBotResponse(data);

      // 4. Update Inspector Metrics
      updateInspector(data);

    } catch (err) {
      removeMessage(loaderId);
      appendMessage("bot", `⚠️ **Network/Server Error:** Failed to process query. ${err.message}`, ["ERROR"]);
    }
  });

  function appendMessage(sender, text, flags = []) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}-message`;

    const icon = sender === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    const senderName = sender === "user" ? "You" : "Gnani.ai Assistant";

    msgDiv.innerHTML = `
      <div class="message-avatar">${icon}</div>
      <div class="message-content">
        <div class="msg-header">
          <span class="sender-name">${senderName}</span>
          <span class="msg-time">${timeStr}</span>
        </div>
        <div class="msg-body">${formatMarkdown(text)}</div>
        ${renderBadges(flags)}
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
  }

  function appendBotResponse(data) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-message";

    const flags = data.guardrails?.flags || [];
    const isSafe = data.guardrails?.passed !== false;
    const groundingScore = data.hallucination_control?.grounding_score ?? 1.0;
    const confidenceLevel = data.hallucination_control?.confidence_level || "MODERATE";

    let groundingBadge = "";
    if (isSafe && !flags.includes("OFF_TOPIC")) {
      const scorePct = Math.round(groundingScore * 100);
      const badgeClass = scorePct >= 70 ? "badge-success" : (scorePct >= 45 ? "badge-warning" : "badge-danger");
      groundingBadge = `<span class="guard-badge ${badgeClass}"><i class="fa-solid fa-bullseye"></i> Grounding: ${scorePct}% (${confidenceLevel})</span>`;
    }

    msgDiv.innerHTML = `
      <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="message-content">
        <div class="msg-header">
          <span class="sender-name">Gnani.ai Assistant</span>
          <span class="msg-time">${timeStr}</span>
        </div>
        <div class="msg-body">${formatMarkdown(data.answer)}</div>
        <div class="badges-row" style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">
          ${renderBadges(flags)}
          ${groundingBadge}
        </div>
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function renderBadges(flags) {
    if (!flags || flags.length === 0) return "";
    return flags.map(flag => {
      if (flag === "PROMPT_INJECTION") {
        return `<span class="guard-badge badge-danger"><i class="fa-solid fa-shield-virus"></i> Prompt Injection Shield Blocked</span>`;
      } else if (flag === "PII_REDACTED") {
        return `<span class="guard-badge badge-warning"><i class="fa-solid fa-user-lock"></i> Sensitive PII Masked</span>`;
      } else if (flag === "OFF_TOPIC") {
        return `<span class="guard-badge badge-warning"><i class="fa-solid fa-compass"></i> Domain Boundary Filter</span>`;
      } else if (flag === "MALICIOUS_TOPIC") {
        return `<span class="guard-badge badge-danger"><i class="fa-solid fa-ban"></i> Policy Violation</span>`;
      }
      return `<span class="guard-badge badge-warning">${flag}</span>`;
    }).join(" ");
  }

  function appendLoadingMessage() {
    const id = "loader-" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.id = id;
    msgDiv.className = "message bot-message";
    msgDiv.innerHTML = `
      <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="message-content">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <span style="font-size:0.75rem; color:var(--text-muted); margin-left:6px;">Retrieving from gnani.ai & verifying grounding...</span>
        </div>
      </div>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const elem = document.getElementById(id);
    if (elem) elem.remove();
  }

  function updateInspector(data) {
    const hCtrl = data.hallucination_control || {};
    const gScore = hCtrl.grounding_score !== undefined ? `${Math.round(hCtrl.grounding_score * 100)}%` : "--";
    const cScore = hCtrl.confidence_score !== undefined ? `${Math.round(hCtrl.confidence_score * 100)}%` : "--";
    const risk = hCtrl.hallucination_risk || (data.guardrails?.passed === false ? "BLOCKED" : "LOW");
    const safety = data.guardrails?.passed !== false ? "PROTECTED" : "BLOCKED";

    metricGrounding.innerText = gScore;
    metricGrounding.style.color = (hCtrl.grounding_score >= 0.7) ? "var(--accent-green)" : "var(--accent-amber)";

    metricRetrieval.innerText = cScore;
    metricRetrieval.style.color = (hCtrl.confidence_score >= 0.5) ? "var(--accent-cyan)" : "var(--accent-rose)";

    metricRisk.innerText = risk;
    metricRisk.style.color = (risk === "LOW" || risk === "NONE" || risk === "PREVENTED") ? "var(--accent-green)" : "var(--accent-rose)";

    metricSafety.innerText = safety;
    metricSafety.style.color = (safety === "PROTECTED") ? "var(--accent-green)" : "var(--accent-rose)";

    // Update retrieved chunks list
    const sources = data.retrieved_sources || [];
    if (sources.length === 0) {
      retrievedSourcesList.innerHTML = `<p class="empty-state">No source chunks retrieved for this prompt.</p>`;
    } else {
      retrievedSourcesList.innerHTML = sources.map(s => `
        <div class="source-item">
          <div class="source-item-header">
            <span class="source-item-title">${escapeHtml(s.title)}</span>
            <span class="source-item-score">${Math.round(s.similarity * 100)}% match</span>
          </div>
          <a href="${s.url}" target="_blank" class="source-item-url" rel="noopener">${escapeHtml(s.url)}</a>
        </div>
      `).join("");
    }
  }

  function resetMetrics() {
    metricGrounding.innerText = "--";
    metricRetrieval.innerText = "--";
    metricRisk.innerText = "--";
    metricSafety.innerText = "--";
    retrievedSourcesList.innerHTML = `<p class="empty-state">No query evaluated yet.</p>`;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Markdown Headers ###
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');

    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Links [title](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Unordered lists - item
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Convert newlines to paragraphs
    html = html.split('\n\n').map(p => {
      if (p.startsWith('<h3>') || p.startsWith('<ul>') || p.startsWith('<li>')) return p;
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    return html;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, function(m) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      }[m];
    });
  }

  function addBotWelcomeMessage() {
    appendMessage("bot", `Welcome! I am the **Gnani.ai Enterprise Assistant**. You can ask about our Voice AI agents, Armour365 voice biometrics, Inya Assist, or speech recognition engines.`);
  }

  // Global helper functions
  window.askQuestion = (text) => {
    userInput.value = text;
    chatForm.dispatchEvent(new Event("submit"));
  };

  window.testAdversarial = (text) => {
    userInput.value = text;
    chatForm.dispatchEvent(new Event("submit"));
  };
});

