const crypto = require("node:crypto");
const path = require("node:path");
const express = require("express");
const dotenv = require("dotenv");

const { buildEmail } = require("./emailTemplate");
const { isMailConfigured, sendOutreachEmail } = require("./mailer");
const { listCampaigns, saveCampaign } = require("./storage");

dotenv.config();

const app = express();
const port = Number(process.env.PORT || 3000);

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "..", "views"));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, "..", "public")));

function defaults() {
  return {
    recipientEmail: "",
    recipientName: "",
    businessName: "",
    businessType: "",
    city: "",
    missingWebsiteContext:
      "I noticed you do not seem to have a dedicated website yet.",
    offerSummary:
      "building and setting up a personalized website for your business",
    benefit1: "learn about what you offer",
    benefit2: "see photos, reviews, and service details in one place",
    benefit3: "contact you without relying only on Google or social media",
    callToAction:
      "If that is something you would be interested in, I would be happy to send over a few ideas that fit your business.",
    customNotes: "",
    senderName: process.env.DEFAULT_SENDER_NAME || "",
    senderEmail: process.env.DEFAULT_SENDER_EMAIL || "",
    senderPhone: process.env.DEFAULT_SENDER_PHONE || "",
    senderWebsite: process.env.DEFAULT_SENDER_WEBSITE || "",
  };
}

function getFormData(source = {}) {
  return {
    ...defaults(),
    recipientEmail: String(source.recipientEmail || "").trim(),
    recipientName: String(source.recipientName || "").trim(),
    businessName: String(source.businessName || "").trim(),
    businessType: String(source.businessType || "").trim(),
    city: String(source.city || "").trim(),
    missingWebsiteContext: String(
      source.missingWebsiteContext || defaults().missingWebsiteContext
    ).trim(),
    offerSummary: String(source.offerSummary || defaults().offerSummary).trim(),
    benefit1: String(source.benefit1 || defaults().benefit1).trim(),
    benefit2: String(source.benefit2 || defaults().benefit2).trim(),
    benefit3: String(source.benefit3 || defaults().benefit3).trim(),
    callToAction: String(
      source.callToAction || defaults().callToAction
    ).trim(),
    customNotes: String(source.customNotes || "").trim(),
    senderName: String(source.senderName || defaults().senderName).trim(),
    senderEmail: String(source.senderEmail || defaults().senderEmail).trim(),
    senderPhone: String(source.senderPhone || defaults().senderPhone).trim(),
    senderWebsite: String(
      source.senderWebsite || defaults().senderWebsite
    ).trim(),
  };
}

function validateFormData(formData) {
  const missing = [];

  if (!formData.recipientEmail) {
    missing.push("recipient email");
  }

  if (!formData.businessName) {
    missing.push("business name");
  }

  if (!formData.senderName) {
    missing.push("sender name");
  }

  if (!formData.senderEmail) {
    missing.push("sender email");
  }

  return missing;
}

async function renderDashboard(res, options = {}) {
  const formData = getFormData(options.formData);
  const campaigns = await listCampaigns();

  res.render("index", {
    formData,
    preview: buildEmail(formData),
    campaigns,
    error: options.error || "",
    success: options.success || "",
    smtpReady: isMailConfigured(),
  });
}

app.get("/", async (req, res, next) => {
  try {
    await renderDashboard(res, {
      success: req.query.success ? "Outreach email sent successfully." : "",
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/preview", (req, res) => {
  const formData = getFormData(req.body);
  res.json(buildEmail(formData));
});

app.post("/campaigns", async (req, res, next) => {
  const formData = getFormData(req.body);
  const validationErrors = validateFormData(formData);

  if (validationErrors.length > 0) {
    try {
      await renderDashboard(res, {
        formData,
        error: `Please add the following before sending: ${validationErrors.join(", ")}.`,
      });
    } catch (error) {
      next(error);
    }

    return;
  }

  const preview = buildEmail(formData);

  try {
    const mailResult = await sendOutreachEmail({
      to: formData.recipientEmail,
      subject: preview.subject,
      text: preview.text,
      html: preview.html,
      replyTo: formData.senderEmail,
    });

    await saveCampaign({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      status: "sent",
      recipientEmail: formData.recipientEmail,
      recipientName: formData.recipientName,
      businessName: formData.businessName,
      businessType: formData.businessType,
      city: formData.city,
      senderName: formData.senderName,
      senderEmail: formData.senderEmail,
      subject: preview.subject,
      text: preview.text,
      messageId: mailResult.messageId,
    });

    res.redirect("/?success=1");
  } catch (error) {
    try {
      await renderDashboard(res, {
        formData,
        error: error.message,
      });
    } catch (renderError) {
      next(renderError);
    }
  }
});

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    smtpReady: isMailConfigured(),
  });
});

app.use((error, _req, res, _next) => {
  res.status(500).render("index", {
    formData: defaults(),
    preview: buildEmail(defaults()),
    campaigns: [],
    error: error.message || "Unexpected server error.",
    success: "",
    smtpReady: isMailConfigured(),
  });
});

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Dashboard running on http://localhost:${port}`);
});
