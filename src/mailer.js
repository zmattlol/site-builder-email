const nodemailer = require("nodemailer");

function getMailConfig() {
  return {
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 587),
    secure: String(process.env.SMTP_SECURE || "false").toLowerCase() === "true",
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
    from: process.env.SMTP_FROM,
  };
}

function isMailConfigured() {
  const config = getMailConfig();

  return Boolean(
    config.host &&
    config.port &&
    config.user &&
    config.pass &&
    config.from
  );
}

function createTransport() {
  const config = getMailConfig();

  return nodemailer.createTransport({
    host: config.host,
    port: config.port,
    secure: config.secure,
    auth: {
      user: config.user,
      pass: config.pass,
    },
  });
}

async function sendOutreachEmail({ to, subject, text, html, from, replyTo }) {
  if (!isMailConfigured()) {
    throw new Error("SMTP is not configured. Add your SMTP settings to .env before sending emails.");
  }

  const transporter = createTransport();

  return transporter.sendMail({
    from: from || getMailConfig().from,
    replyTo,
    to,
    subject,
    text,
    html,
  });
}

module.exports = {
  getMailConfig,
  isMailConfigured,
  sendOutreachEmail,
};
