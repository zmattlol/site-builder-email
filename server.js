const path = require("path");
const express = require("express");
const nodemailer = require("nodemailer");
require("dotenv").config();

const app = express();
const port = Number.parseInt(process.env.PORT || "3000", 10);

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const DEFAULT_BENEFITS = [
  "A professional website helps new customers trust your business before they call.",
  "It gives people one clear place to view your services, hours, and contact details.",
  "A fast, mobile-friendly site can help your business show up better in local searches."
];

function toTrimmedString(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeLead(input = {}) {
  return {
    recipientEmail: toTrimmedString(input.recipientEmail),
    businessName: toTrimmedString(input.businessName),
    contactName: toTrimmedString(input.contactName),
    city: toTrimmedString(input.city),
    industry: toTrimmedString(input.industry),
    customObservation: toTrimmedString(input.customObservation),
    senderName: toTrimmedString(input.senderName),
    senderCompany: toTrimmedString(input.senderCompany),
    offerSummary: toTrimmedString(input.offerSummary),
    ctaLine: toTrimmedString(input.ctaLine),
    benefits: Array.isArray(input.benefits)
      ? input.benefits.map(toTrimmedString).filter(Boolean)
      : []
  };
}

function buildOutreachEmail(rawLead) {
  const lead = normalizeLead(rawLead);
  const {
    businessName,
    contactName,
    city,
    industry,
    customObservation,
    senderName,
    senderCompany,
    offerSummary,
    ctaLine
  } = lead;

  const benefits = (lead.benefits.length ? lead.benefits : DEFAULT_BENEFITS).slice(0, 3);

  const subjectBusinessName = businessName || "your business";
  const subject = `Quick website idea for ${subjectBusinessName}`;

  const greetingName = contactName || "there";
  const introBits = [];

  if (businessName) {
    introBits.push(`I came across ${businessName}`);
  } else {
    introBits.push("I came across your business profile");
  }

  if (city) {
    introBits.push(`in ${city}`);
  }

  if (industry) {
    introBits.push(`while looking at local ${industry} businesses`);
  }

  const introLine = `${introBits.join(" ")} and wanted to reach out with a quick idea.`;

  const observationLine = customObservation
    ? customObservation
    : "I noticed there may not be a dedicated website yet, so most people only see your profile listing.";

  const offerLine = offerSummary
    ? offerSummary
    : "I help local businesses launch personalized websites that are clean, mobile-friendly, and easy to update.";

  const cta = ctaLine
    ? ctaLine
    : "If that is something you are interested in, I can share a simple starter plan tailored to your business.";

  const signatureName = senderName || "Your Name";
  const signatureCompany = senderCompany ? `\n${senderCompany}` : "";

  const text = [
    `Hi ${greetingName},`,
    "",
    introLine,
    observationLine,
    "",
    offerLine,
    "",
    "A website can help by:",
    ...benefits.map((benefit) => `- ${benefit}`),
    "",
    cta,
    "",
    "If you would rather not receive outreach messages from me, just reply with \"No thanks\" and I will not follow up.",
    "",
    `Best,`,
    `${signatureName}${signatureCompany}`
  ].join("\n");

  return { subject, body: text };
}

function getSmtpConfig() {
  const portValue = Number.parseInt(process.env.SMTP_PORT || "587", 10);
  return {
    host: process.env.SMTP_HOST,
    port: Number.isNaN(portValue) ? 587 : portValue,
    secure: process.env.SMTP_SECURE === "true",
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
    from: process.env.SMTP_FROM
  };
}

function validateSmtpConfig(config) {
  const required = ["host", "user", "pass", "from"];
  const missing = required.filter((field) => !config[field]);
  return {
    valid: missing.length === 0,
    missing
  };
}

async function sendOutreachEmail({ recipientEmail, subject, body }) {
  const config = getSmtpConfig();
  const validation = validateSmtpConfig(config);

  if (!validation.valid) {
    throw new Error(
      `Missing SMTP configuration values: ${validation.missing.join(", ")}. Update your .env file.`
    );
  }

  const transporter = nodemailer.createTransport({
    host: config.host,
    port: config.port,
    secure: config.secure,
    auth: {
      user: config.user,
      pass: config.pass
    }
  });

  return transporter.sendMail({
    from: config.from,
    to: recipientEmail,
    subject,
    text: body
  });
}

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.get("/api/config", (_req, res) => {
  res.json({
    senderName: process.env.DEFAULT_SENDER_NAME || "",
    senderCompany: process.env.DEFAULT_SENDER_COMPANY || "",
    offerSummary: process.env.DEFAULT_OFFER_SUMMARY || "",
    ctaLine: process.env.DEFAULT_CTA_LINE || ""
  });
});

app.post("/api/generate-email", (req, res) => {
  const payload = normalizeLead(req.body);

  if (!payload.businessName && !payload.recipientEmail) {
    return res.status(400).json({
      error: "Provide at least a business name or recipient email."
    });
  }

  const draft = buildOutreachEmail(payload);
  return res.json(draft);
});

app.post("/api/send-email", async (req, res) => {
  try {
    const payload = normalizeLead(req.body);
    const recipientEmail = toTrimmedString(req.body.recipientEmail);
    const customSubject = toTrimmedString(req.body.subject);
    const customBody = toTrimmedString(req.body.body);

    if (!recipientEmail) {
      return res.status(400).json({ error: "Recipient email is required." });
    }

    const draft = buildOutreachEmail(payload);
    const finalSubject = customSubject || draft.subject;
    const finalBody = customBody || draft.body;

    const result = await sendOutreachEmail({
      recipientEmail,
      subject: finalSubject,
      body: finalBody
    });

    return res.json({
      success: true,
      messageId: result.messageId,
      accepted: result.accepted
    });
  } catch (error) {
    return res.status(500).json({
      error: error.message || "Failed to send email."
    });
  }
});

app.get(/^(?!\/api\/).*/, (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

if (require.main === module) {
  app.listen(port, () => {
    console.log(`Outreach dashboard running on http://localhost:${port}`);
  });
}

module.exports = { app, buildOutreachEmail, normalizeLead };
