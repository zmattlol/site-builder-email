const state = {
  leads: [],
  selectedLeadId: null,
};

const leadForm = document.getElementById("lead-form");
const leadList = document.getElementById("lead-list");
const leadCount = document.getElementById("lead-count");
const detailForm = document.getElementById("detail-form");
const detailEmpty = document.getElementById("detail-empty");
const detailStatus = document.getElementById("detail-status");
const generateButton = document.getElementById("generate-button");
const sendButton = document.getElementById("send-button");
const toast = document.getElementById("toast");

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.hidden = false;
  toast.style.background = isError ? "#991b1b" : "#111827";
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => {
    toast.hidden = true;
  }, 3500);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch (error) {
    payload = {};
  }

  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }

  return payload;
}

function getSelectedLead() {
  return state.leads.find((lead) => lead.id === state.selectedLeadId) || null;
}

function setSelectedLead(leadId) {
  state.selectedLeadId = leadId;
  renderLeadList();
  renderDetail();
}

function renderLeadList() {
  leadCount.textContent = `${state.leads.length} saved`;
  if (!state.leads.length) {
    leadList.className = "lead-list empty-state";
    leadList.textContent = "No leads yet. Add one to start your outreach list.";
    return;
  }

  leadList.className = "lead-list";
  leadList.innerHTML = "";

  state.leads.forEach((lead) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `lead-card${lead.id === state.selectedLeadId ? " selected" : ""}`;
    card.innerHTML = `
      <h3>${lead.business_name}</h3>
      <p>${lead.email}</p>
      <p>Status: ${lead.status}${lead.do_not_contact ? " - do not contact" : ""}</p>
    `;
    card.addEventListener("click", () => setSelectedLead(lead.id));
    leadList.appendChild(card);
  });
}

function fillForm(form, lead) {
  Array.from(form.elements).forEach((field) => {
    if (!field.name) {
      return;
    }
    if (field.type === "checkbox") {
      field.checked = Boolean(lead[field.name]);
      return;
    }
    field.value = lead[field.name] || "";
  });
}

function formToPayload(form) {
  const payload = {};
  Array.from(form.elements).forEach((field) => {
    if (!field.name) {
      return;
    }
    payload[field.name] = field.type === "checkbox" ? field.checked : field.value.trim();
  });
  return payload;
}

function renderDetail() {
  const lead = getSelectedLead();
  if (!lead) {
    detailForm.hidden = true;
    detailEmpty.hidden = false;
    detailStatus.textContent = "No lead selected";
    sendButton.disabled = true;
    generateButton.disabled = true;
    return;
  }

  detailForm.hidden = false;
  detailEmpty.hidden = true;
  detailStatus.textContent = lead.do_not_contact
    ? "Do not contact"
    : lead.status || "draft";
  fillForm(detailForm, lead);
  sendButton.disabled = lead.do_not_contact;
  generateButton.disabled = false;
}

function upsertLead(updatedLead) {
  const existingIndex = state.leads.findIndex((lead) => lead.id === updatedLead.id);
  if (existingIndex >= 0) {
    state.leads.splice(existingIndex, 1, updatedLead);
  } else {
    state.leads.unshift(updatedLead);
  }
  state.leads.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
  setSelectedLead(updatedLead.id);
}

async function loadLeads() {
  try {
    const payload = await request("/api/leads");
    state.leads = payload.leads || [];
    if (!getSelectedLead() && state.leads.length) {
      state.selectedLeadId = state.leads[0].id;
    }
    renderLeadList();
    renderDetail();
  } catch (error) {
    showToast(error.message, true);
  }
}

leadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formToPayload(leadForm);
    const response = await request("/api/leads", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    upsertLead(response.lead);
    leadForm.reset();
    showToast("Lead saved.");
  } catch (error) {
    showToast(error.message, true);
  }
});

detailForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const lead = getSelectedLead();
  if (!lead) {
    return;
  }

  try {
    const payload = formToPayload(detailForm);
    const response = await request(`/api/leads/${lead.id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    upsertLead(response.lead);
    showToast("Changes saved.");
  } catch (error) {
    showToast(error.message, true);
  }
});

generateButton.addEventListener("click", async () => {
  const lead = getSelectedLead();
  if (!lead) {
    return;
  }

  try {
    const response = await request(`/api/leads/${lead.id}/draft`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    upsertLead(response.lead);
    showToast("Draft generated.");
  } catch (error) {
    showToast(error.message, true);
  }
});

sendButton.addEventListener("click", async () => {
  const lead = getSelectedLead();
  if (!lead) {
    return;
  }

  if (!window.confirm(`Send the current draft to ${lead.email}?`)) {
    return;
  }

  try {
    const response = await request(`/api/leads/${lead.id}/send`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    upsertLead(response.lead);
    showToast("Email sent.");
  } catch (error) {
    showToast(error.message, true);
  }
});

loadLeads();

