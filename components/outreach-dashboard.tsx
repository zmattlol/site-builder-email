"use client";

import { useMemo, useState } from "react";

import { defaultProspect } from "../lib/defaults";
import { generateOutreachEmail } from "../lib/email-template";
import type { CampaignForm, ProspectForm, ProspectRecord } from "../lib/types";

type Notice = {
  kind: "success" | "error" | "info";
  text: string;
};

const syncRecords = (
  currentRecords: ProspectRecord[],
  nextRecord: ProspectRecord,
): ProspectRecord[] =>
  [...currentRecords.filter((record) => record.id !== nextRecord.id), nextRecord].sort(
    (left, right) =>
      new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime(),
  );

const toProspectForm = (record: ProspectRecord): ProspectForm => ({
  id: record.id,
  businessName: record.businessName,
  contactName: record.contactName,
  email: record.email,
  industry: record.industry,
  city: record.city,
  googleProfileUrl: record.googleProfileUrl,
  currentPresence: record.currentPresence,
  personalization: record.personalization,
  notes: record.notes,
  tone: record.tone,
});

const formatTimestamp = (value?: string): string =>
  value
    ? new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "Not sent yet";

export default function OutreachDashboard({
  initialCampaign,
  initialProspect,
  initialProspects,
  emailConfigured,
}: {
  initialCampaign: CampaignForm;
  initialProspect: ProspectForm;
  initialProspects: ProspectRecord[];
  emailConfigured: boolean;
}) {
  const [campaign, setCampaign] = useState<CampaignForm>(initialCampaign);
  const [prospect, setProspect] = useState<ProspectForm>(initialProspect);
  const [records, setRecords] = useState<ProspectRecord[]>(initialProspects);
  const [busyAction, setBusyAction] = useState<"save" | "send" | null>(null);
  const [notice, setNotice] = useState<Notice>({
    kind: "info",
    text: emailConfigured
      ? "SMTP is configured. You can save drafts and send live outreach."
      : "Add SMTP settings in .env.local to turn on live sending. Preview and draft saving already work.",
  });

  const draft = useMemo(
    () => generateOutreachEmail(campaign, prospect),
    [campaign, prospect],
  );
  const hasMinimumDetails =
    Boolean(prospect.businessName.trim()) && Boolean(prospect.email.trim());

  const updateCampaign = <Key extends keyof CampaignForm>(
    key: Key,
    value: CampaignForm[Key],
  ): void => {
    setCampaign((current) => ({ ...current, [key]: value }));
  };

  const updateProspect = <Key extends keyof ProspectForm>(
    key: Key,
    value: ProspectForm[Key],
  ): void => {
    setProspect((current) => ({ ...current, [key]: value }));
  };

  const handleSaveDraft = async (): Promise<void> => {
    if (!hasMinimumDetails) {
      setNotice({
        kind: "error",
        text: "Add at least the business name and email before saving a draft.",
      });
      return;
    }

    setBusyAction("save");

    try {
      const response = await fetch("/api/prospects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ campaign, prospect }),
      });
      const data = (await response.json()) as { error?: string; record?: ProspectRecord };

      if (!response.ok || !data.record) {
        throw new Error(data.error ?? "Unable to save the outreach draft.");
      }

      const savedRecord = data.record;

      setRecords((current) => syncRecords(current, savedRecord));
      setProspect((current) => ({ ...current, id: savedRecord.id }));
      setNotice({
        kind: "success",
        text: `Draft saved for ${savedRecord.businessName}.`,
      });
    } catch (error) {
      setNotice({
        kind: "error",
        text:
          error instanceof Error ? error.message : "Unable to save the outreach draft.",
      });
    } finally {
      setBusyAction(null);
    }
  };

  const handleSend = async (): Promise<void> => {
    if (!hasMinimumDetails) {
      setNotice({
        kind: "error",
        text: "Add at least the business name and email before sending.",
      });
      return;
    }

    setBusyAction("send");

    try {
      const response = await fetch("/api/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ campaign, prospect }),
      });
      const data = (await response.json()) as { error?: string; record?: ProspectRecord };

      if (!response.ok) {
        if (data.record) {
          const failedRecord = data.record;
          setRecords((current) => syncRecords(current, failedRecord));
        }

        throw new Error(data.error ?? "Unable to send the outreach email.");
      }

      if (!data.record) {
        throw new Error("Unable to send the outreach email.");
      }

      const sentRecord = data.record;

      setRecords((current) => syncRecords(current, sentRecord));
      setProspect({
        ...defaultProspect,
        tone: prospect.tone,
      });
      setNotice({
        kind: "success",
        text: `Email sent to ${sentRecord.businessName} at ${sentRecord.email}.`,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to send the outreach email.";

      setNotice({
        kind: "error",
        text: message,
      });
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div className="dashboard-shell">
      <section className="hero-card card">
        <div>
          <p className="eyebrow">Website outreach bot</p>
          <h1>Send soft-sell website outreach emails from one dashboard</h1>
          <p className="hero-copy">
            Plug in your offer, enter a business name and email, and the app builds a
            personalized message that introduces the value of a website without coming
            off too aggressive.
          </p>
        </div>
        <div className="hero-badges">
          <span className={`status-pill ${emailConfigured ? "status-sent" : "status-draft"}`}>
            {emailConfigured ? "SMTP ready" : "Preview mode"}
          </span>
          <p className="legal-note">
            Use responsibly and make sure your outreach follows the email rules in the
            regions where you operate.
          </p>
        </div>
      </section>

      <section className={`notice notice-${notice.kind}`}>{notice.text}</section>

      <div className="form-grid">
        <section className="card">
          <div className="section-heading">
            <div>
              <h2>Your offer</h2>
              <p className="section-copy">
                Reuse these details for every business you contact.
              </p>
            </div>
          </div>

          <div className="field-row">
            <label className="field">
              <span>Your name</span>
              <input
                className="input"
                value={campaign.senderName}
                onChange={(event) => updateCampaign("senderName", event.target.value)}
                placeholder="Jordan Smith"
              />
            </label>
            <label className="field">
              <span>Your business</span>
              <input
                className="input"
                value={campaign.senderBusiness}
                onChange={(event) => updateCampaign("senderBusiness", event.target.value)}
                placeholder="North Peak Web Studio"
              />
            </label>
          </div>

          <div className="field-row">
            <label className="field">
              <span>Sender email</span>
              <input
                className="input"
                value={campaign.senderEmail}
                onChange={(event) => updateCampaign("senderEmail", event.target.value)}
                placeholder="you@yourbusiness.com"
              />
            </label>
            <label className="field">
              <span>Reply-to email</span>
              <input
                className="input"
                value={campaign.replyTo}
                onChange={(event) => updateCampaign("replyTo", event.target.value)}
                placeholder="reply@yourbusiness.com"
              />
            </label>
          </div>

          <label className="field">
            <span>Main offer</span>
            <textarea
              className="textarea"
              value={campaign.offerSummary}
              onChange={(event) => updateCampaign("offerSummary", event.target.value)}
              placeholder="building and setting up personalized websites for local businesses"
              rows={3}
            />
          </label>

          <label className="field">
            <span>Why the website helps</span>
            <textarea
              className="textarea"
              value={campaign.valueProposition}
              onChange={(event) => updateCampaign("valueProposition", event.target.value)}
              rows={4}
            />
          </label>

          <label className="field">
            <span>Benefit bullets (one per line)</span>
            <textarea
              className="textarea"
              value={campaign.benefitPoints}
              onChange={(event) => updateCampaign("benefitPoints", event.target.value)}
              rows={5}
            />
          </label>

          <label className="field">
            <span>Soft call to action</span>
            <textarea
              className="textarea"
              value={campaign.callToAction}
              onChange={(event) => updateCampaign("callToAction", event.target.value)}
              rows={3}
            />
          </label>

          <div className="field-row">
            <label className="field">
              <span>Portfolio link</span>
              <input
                className="input"
                value={campaign.portfolioUrl}
                onChange={(event) => updateCampaign("portfolioUrl", event.target.value)}
                placeholder="https://yourbusiness.com"
              />
            </label>
            <label className="field">
              <span>Calendar link</span>
              <input
                className="input"
                value={campaign.calendarLink}
                onChange={(event) => updateCampaign("calendarLink", event.target.value)}
                placeholder="https://cal.com/you"
              />
            </label>
          </div>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={campaign.includeOptOut}
              onChange={(event) => updateCampaign("includeOptOut", event.target.checked)}
            />
            <span>Include a polite opt-out line</span>
          </label>

          <label className="field">
            <span>Opt-out text</span>
            <textarea
              className="textarea"
              value={campaign.optOutText}
              onChange={(event) => updateCampaign("optOutText", event.target.value)}
              rows={2}
            />
          </label>
        </section>

        <section className="card">
          <div className="section-heading">
            <div>
              <h2>Business details</h2>
              <p className="section-copy">
                Only the business name and email are required. The rest helps personalize
                the email.
              </p>
            </div>
          </div>

          <div className="field-row">
            <label className="field">
              <span>Business name *</span>
              <input
                className="input"
                value={prospect.businessName}
                onChange={(event) => updateProspect("businessName", event.target.value)}
                placeholder="Lakeside Auto Detail"
              />
            </label>
            <label className="field">
              <span>Contact name</span>
              <input
                className="input"
                value={prospect.contactName}
                onChange={(event) => updateProspect("contactName", event.target.value)}
                placeholder="Alex"
              />
            </label>
          </div>

          <div className="field-row">
            <label className="field">
              <span>Email *</span>
              <input
                className="input"
                type="email"
                value={prospect.email}
                onChange={(event) => updateProspect("email", event.target.value)}
                placeholder="owner@business.com"
              />
            </label>
            <label className="field">
              <span>City / area</span>
              <input
                className="input"
                value={prospect.city}
                onChange={(event) => updateProspect("city", event.target.value)}
                placeholder="Tampa"
              />
            </label>
          </div>

          <div className="field-row">
            <label className="field">
              <span>Industry</span>
              <input
                className="input"
                value={prospect.industry}
                onChange={(event) => updateProspect("industry", event.target.value)}
                placeholder="Auto detailing"
              />
            </label>
            <label className="field">
              <span>Current online presence</span>
              <input
                className="input"
                value={prospect.currentPresence}
                onChange={(event) => updateProspect("currentPresence", event.target.value)}
                placeholder="their Google Business Profile"
              />
            </label>
          </div>

          <label className="field">
            <span>Google profile URL</span>
            <input
              className="input"
              value={prospect.googleProfileUrl}
              onChange={(event) => updateProspect("googleProfileUrl", event.target.value)}
              placeholder="https://maps.google.com/..."
            />
          </label>

          <label className="field">
            <span>Personalization note</span>
            <textarea
              className="textarea"
              value={prospect.personalization}
              onChange={(event) => updateProspect("personalization", event.target.value)}
              placeholder="they have strong reviews but no clear service list online"
              rows={3}
            />
          </label>

          <label className="field">
            <span>Extra notes</span>
            <textarea
              className="textarea"
              value={prospect.notes}
              onChange={(event) => updateProspect("notes", event.target.value)}
              placeholder="family-owned shop focused on local repeat customers"
              rows={3}
            />
          </label>

          <label className="field">
            <span>Tone</span>
            <select
              className="input"
              value={prospect.tone}
              onChange={(event) =>
                updateProspect("tone", event.target.value as ProspectForm["tone"])
              }
            >
              <option value="warm">Warm</option>
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
            </select>
          </label>
        </section>
      </div>

      <div className="bottom-grid">
        <section className="card preview-card">
          <div className="section-heading actions-layout">
            <div>
              <h2>Email preview</h2>
              <p className="section-copy">
                This updates as you type, then the send endpoint uses the same template.
              </p>
            </div>
            <div className="button-row">
              <button
                type="button"
                className="secondary-button"
                onClick={handleSaveDraft}
                disabled={busyAction !== null || !hasMinimumDetails}
              >
                {busyAction === "save" ? "Saving..." : "Save draft"}
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={handleSend}
                disabled={busyAction !== null || !emailConfigured || !hasMinimumDetails}
              >
                {busyAction === "send" ? "Sending..." : "Send email"}
              </button>
            </div>
          </div>

          <div className="preview-meta">
            <div>
              <span className="preview-label">Subject</span>
              <div className="subject-preview">{draft.subject}</div>
            </div>
            <div className="preview-help">
              {!emailConfigured
                ? "SMTP is not configured yet, so the send button stays locked."
                : "Live sends go through your SMTP credentials from .env.local."}
            </div>
          </div>

          <div className="email-body-preview">
            <pre>{draft.text}</pre>
          </div>
        </section>

        <section className="card history-card">
          <div className="section-heading">
            <div>
              <h2>Outreach history</h2>
              <p className="section-copy">
                Drafts and sends are stored in a simple JSON file for quick reuse.
              </p>
            </div>
          </div>

          {records.length === 0 ? (
            <div className="empty-state">
              No outreach saved yet. Save a draft or send an email to create your first
              record.
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Business</th>
                    <th>Status</th>
                    <th>Last updated</th>
                    <th>Preview</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id}>
                      <td>
                        <div className="table-primary">{record.businessName}</div>
                        <div className="table-secondary">{record.email}</div>
                      </td>
                      <td>
                        <span className={`status-pill status-${record.status}`}>
                          {record.status}
                        </span>
                      </td>
                      <td>
                        <div className="table-primary">{formatTimestamp(record.updatedAt)}</div>
                        <div className="table-secondary">
                          {record.lastSentAt
                            ? `Last sent ${formatTimestamp(record.lastSentAt)}`
                            : "Not sent yet"}
                        </div>
                      </td>
                      <td>
                        <div className="table-primary">{record.subject}</div>
                        <div className="table-secondary clamp">{record.preview}</div>
                        {record.error ? (
                          <div className="error-inline">{record.error}</div>
                        ) : null}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="ghost-button"
                          onClick={() => {
                            setProspect(toProspectForm(record));
                            setNotice({
                              kind: "info",
                              text: `Loaded ${record.businessName} back into the form.`,
                            });
                          }}
                        >
                          Load
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
