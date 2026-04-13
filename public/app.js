const form = document.getElementById("outreach-form");
const previewSubjectEl = document.getElementById("preview-subject");
const previewRecipientEl = document.getElementById("preview-recipient");
const previewStatusEl = document.getElementById("preview-status");
const previewBodyEl = document.getElementById("preview-body");
const historyEl = document.getElementById("history");
const refreshBtn = document.getElementById("refresh-log");

function getPayload() {
  const data = new FormData(form);
  const raw = Object.fromEntries(data.entries());
  return {
    businessName: raw.businessName || "",
    contactName: raw.contactName || "",
    businessType: raw.businessType || "",
    location: raw.location || "",
    businessEmail: raw.contactEmail || "",
    offer: raw.offerDetails || "",
    senderName: raw.yourName || "",
    senderCompany: "Website Setup Services",
    cta:
      "If this is something you're interested in, I can share a quick outline and next steps.",
    businessNotes: raw.businessNotes || "",
  };
}

function setPreview({ subject, body, to, status }) {
  previewSubjectEl.textContent = subject || "-";
  previewBodyEl.textContent = body || "Fill out the form to generate an outreach email.";
  previewRecipientEl.textContent = to || "-";
  previewStatusEl.textContent = status || "Waiting for input";
}

function renderHistory(logs) {
  if (!Array.isArray(logs) || logs.length === 0) {
    historyEl.innerHTML = `<p>No activity yet.</p>`;
    return;
  }

  historyEl.innerHTML = logs
    .map((entry) => {
      return `
        <article class="history-item">
          <p><strong>${entry.businessName}</strong> (${entry.to})</p>
          <p>${entry.subject}</p>
          <p><small>${new Date(entry.timestamp).toLocaleString()} - ${entry.status}</small></p>
          ${entry.error ? `<p class="error-text">Error: ${entry.error}</p>` : ""}
        </article>
      `;
    })
    .join("");
}

async function refreshLogs() {
  try {
    const response = await fetch("/api/logs");
    const data = await response.json();
    renderHistory(data);
  } catch (error) {
    historyEl.innerHTML = `<p class="error-text">Failed to load history.</p>`;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const sendEmail = form.elements.sendEmail.checked;
  const payload = getPayload();
  const endpoint = sendEmail ? "/api/send-email" : "/api/generate-email";
  const button = form.querySelector("button[type='submit']");

  button.disabled = true;
  button.textContent = sendEmail ? "Sending..." : "Generating...";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      setPreview({
        subject: data.preview?.subject || "-",
        body: data.preview?.body || data.error || "Failed request.",
        to: payload.businessEmail,
        status: `Error: ${data.error || "Request failed"}`,
      });
      return;
    }

    const subject = data.subject || data.preview?.subject;
    const body = data.body || data.preview?.body;
    setPreview({
      subject,
      body,
      to: payload.businessEmail,
      status: sendEmail ? data.message || "Sent." : "Preview generated (not sent).",
    });

    if (sendEmail) {
      await refreshLogs();
    }
  } catch (error) {
    setPreview({
      subject: "-",
      body: "Request failed. Check server and try again.",
      to: payload.businessEmail,
      status: `Error: ${error.message}`,
    });
  } finally {
    button.disabled = false;
    button.textContent = "Generate Outreach Email";
  }
});

refreshBtn.addEventListener("click", refreshLogs);
refreshLogs();
