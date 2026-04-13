const form = document.getElementById("lead-form");
const generateBtn = document.getElementById("generate-btn");
const sendBtn = document.getElementById("send-btn");
const statusEl = document.getElementById("status");
const subjectInput = document.getElementById("email-subject");
const bodyInput = document.getElementById("email-body");

function showStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.classList.remove("success", "error");
  if (type) {
    statusEl.classList.add(type);
  }
}

function fieldValue(name) {
  const field = form.elements.namedItem(name);
  return field ? field.value.trim() : "";
}

function readBenefits() {
  return [fieldValue("benefit1"), fieldValue("benefit2"), fieldValue("benefit3")].filter(Boolean);
}

function buildPayload() {
  return {
    recipientEmail: fieldValue("recipientEmail"),
    businessName: fieldValue("businessName"),
    contactName: fieldValue("contactName"),
    city: fieldValue("city"),
    industry: fieldValue("industry"),
    customObservation: fieldValue("customObservation"),
    senderName: fieldValue("senderName"),
    senderCompany: fieldValue("senderCompany"),
    offerSummary: fieldValue("offerSummary"),
    ctaLine: fieldValue("ctaLine"),
    benefits: readBenefits()
  };
}

async function loadDefaults() {
  try {
    const response = await fetch("/api/config");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load default values.");
    }

    if (data.senderName) form.elements.namedItem("senderName").value = data.senderName;
    if (data.senderCompany) form.elements.namedItem("senderCompany").value = data.senderCompany;
    if (data.offerSummary) form.elements.namedItem("offerSummary").value = data.offerSummary;
    if (data.ctaLine) form.elements.namedItem("ctaLine").value = data.ctaLine;
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function generateDraft() {
  const payload = buildPayload();

  try {
    generateBtn.disabled = true;
    showStatus("Generating personalized draft...");

    const response = await fetch("/api/generate-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to generate draft.");
    }

    subjectInput.value = data.subject;
    bodyInput.value = data.body;
    showStatus("Draft generated. Review it and send when ready.", "success");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    generateBtn.disabled = false;
  }
}

async function sendEmail() {
  const payload = buildPayload();
  const subject = subjectInput.value.trim();
  const body = bodyInput.value.trim();

  if (!payload.recipientEmail) {
    showStatus("Recipient email is required.", "error");
    return;
  }

  if (!subject || !body) {
    showStatus("Generate a draft (or type a subject/body) before sending.", "error");
    return;
  }

  try {
    sendBtn.disabled = true;
    showStatus("Sending email...");

    const response = await fetch("/api/send-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...payload,
        subject,
        body
      })
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to send email.");
    }

    showStatus(`Email sent. Message ID: ${data.messageId}`, "success");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    sendBtn.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  generateDraft();
});

generateBtn.addEventListener("click", generateDraft);
sendBtn.addEventListener("click", sendEmail);

loadDefaults();
