const express = require("express");
const path = require("path");
const fs = require("fs/promises");
const nodemailer = require("nodemailer");
const dotenv = require("dotenv");
const { randomUUID } = require("crypto");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, "data");
const LOG_FILE = path.join(DATA_DIR, "outreach-log.json");
const TEST_MODE = process.env.TEST_MODE !== "false";

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

async function ensureDataFile() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  try {
    await fs.access(LOG_FILE);
  } catch (error) {
    await fs.writeFile(LOG_FILE, "[]", "utf8");
  }
}

async function readLog() {
  await ensureDataFile();
  const raw = await fs.readFile(LOG_FILE, "utf8");
  return JSON.parse(raw);
}

async function writeLog(entries) {
  await ensureDataFile();
  await fs.writeFile(LOG_FILE, JSON.stringify(entries, null, 2), "utf8");
}

function toTitleCase(value) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function buildEmailTemplate(payload) {
  const {
    businessName,
    contactName,
    businessType,
    location,
    offer,
    senderName,
    senderCompany,
    cta,
    businessNotes,
  } = payload;

  const normalizedBusinessType = businessType
    ? businessType.toLowerCase()
    : "local business";

  const subject = `${toTitleCase(businessName)}: quick website idea for your ${normalizedBusinessType}`;

  const introLine = contactName
    ? `Hi ${toTitleCase(contactName)},`
    : `Hi ${toTitleCase(businessName)} team,`;

  const locationSnippet = location ? ` in ${location}` : "";

  const notesLine = businessNotes
    ? `From what I saw: ${businessNotes.trim()}`
    : "";

  const body = `${introLine}

I came across ${toTitleCase(businessName)}${locationSnippet} and noticed you may not have a dedicated website yet.

I help businesses like yours with ${offer}.
${notesLine}

A clean site can quietly help with:
- capturing leads from Google/Maps visitors
- showing services, pricing, and trust signals in one place
- making it easy for customers to contact or book you

If this is something you're open to, I can send a simple one-page mockup idea tailored to your business.

${cta}

Best,
${senderName}
${senderCompany || "Website Setup Services"}`.trim();

  return { subject, body };
}

function validateInput(input, { requireRecipientEmail }) {
  const requiredFields = ["businessName", "offer", "senderName"];
  if (requireRecipientEmail) {
    requiredFields.push("businessEmail");
  }
  const missing = requiredFields.filter((field) => !input[field]);

  if (missing.length > 0) {
    return `Missing required fields: ${missing.join(", ")}`;
  }

  if (requireRecipientEmail) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(input.businessEmail)) {
      return "businessEmail is not a valid email format";
    }
  }

  return null;
}

function createTransporter() {
  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS } = process.env;
  if (!SMTP_HOST || !SMTP_PORT || !SMTP_USER || !SMTP_PASS) {
    throw new Error(
      "SMTP configuration missing. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS."
    );
  }

  return nodemailer.createTransport({
    host: SMTP_HOST,
    port: Number(SMTP_PORT),
    secure: Number(SMTP_PORT) === 465,
    auth: {
      user: SMTP_USER,
      pass: SMTP_PASS,
    },
  });
}

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, testMode: TEST_MODE });
});

app.get("/api/logs", async (_req, res) => {
  try {
    const entries = await readLog();
    res.json(entries.slice().reverse());
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post("/api/generate-email", (req, res) => {
  const input = {
    businessName: req.body.businessName?.trim(),
    contactName: req.body.contactName?.trim() || "",
    businessType: req.body.businessType?.trim() || "",
    location: req.body.location?.trim() || "",
    businessNotes: req.body.businessNotes?.trim() || "",
    offer:
      req.body.offer?.trim() ||
      "building and setting up a personalized website for your business",
    senderName: req.body.senderName?.trim(),
    senderCompany: req.body.senderCompany?.trim() || "",
    cta:
      req.body.cta?.trim() ||
      "Would you be interested in a quick chat this week?",
  };

  const error = validateInput(input, { requireRecipientEmail: false });

  if (error) {
    return res.status(400).json({ error });
  }

  const generated = buildEmailTemplate(input);
  return res.json(generated);
});

app.post("/api/send-email", async (req, res) => {
  const input = {
    businessName: req.body.businessName?.trim(),
    contactName: req.body.contactName?.trim() || "",
    businessType: req.body.businessType?.trim() || "",
    location: req.body.location?.trim() || "",
    businessEmail: req.body.businessEmail?.trim(),
    businessNotes: req.body.businessNotes?.trim() || "",
    offer:
      req.body.offer?.trim() ||
      "building and setting up a personalized website for your business",
    senderName: req.body.senderName?.trim(),
    senderCompany: req.body.senderCompany?.trim() || "",
    cta:
      req.body.cta?.trim() ||
      "Would you be interested in a quick chat this week?",
  };

  const validationError = validateInput(input, { requireRecipientEmail: true });
  if (validationError) {
    return res.status(400).json({ error: validationError });
  }

  const { subject, body } = buildEmailTemplate(input);
  const timestamp = new Date().toISOString();
  const logEntry = {
    id: randomUUID(),
    timestamp,
    to: input.businessEmail,
    businessName: input.businessName,
    subject,
    body,
    status: TEST_MODE ? "simulated" : "sent",
  };

  try {
    if (!TEST_MODE) {
      const transporter = createTransporter();
      await transporter.sendMail({
        from: `"${process.env.SMTP_FROM_NAME || input.senderName}" <${
          process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        }>`,
        to: input.businessEmail,
        subject,
        text: body,
      });
    }

    const log = await readLog();
    log.push(logEntry);
    await writeLog(log);

    return res.json({
      ok: true,
      message: TEST_MODE
        ? "Email simulation saved to log (TEST_MODE=true)."
        : "Email sent successfully.",
      preview: { subject, body },
      logEntry,
    });
  } catch (error) {
    const failedEntry = {
      ...logEntry,
      status: "failed",
      error: error.message,
    };
    const log = await readLog();
    log.push(failedEntry);
    await writeLog(log);

    return res.status(500).json({
      ok: false,
      error: error.message,
      preview: { subject, body },
    });
  }
});

app.listen(PORT, async () => {
  await ensureDataFile();
  // eslint-disable-next-line no-console
  console.log(`Dashboard running on http://localhost:${PORT}`);
  // eslint-disable-next-line no-console
  console.log(`TEST_MODE=${TEST_MODE}`);
});
