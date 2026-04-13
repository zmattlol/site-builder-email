import nodemailer from "nodemailer";

import type { CampaignForm, OutreachDraft, ProspectForm } from "./types";

const formatMailbox = (name: string, email: string): string =>
  email.includes("<") ? email : name ? `"${name.replaceAll('"', '\\"')}" <${email}>` : email;

const getPort = (): number => {
  const value = Number(process.env.SMTP_PORT ?? "587");
  return Number.isFinite(value) && value > 0 ? value : 587;
};

export const hasSmtpConfig = (): boolean =>
  Boolean(process.env.SMTP_HOST && (process.env.SMTP_FROM || process.env.SMTP_USER));

export const sendOutreachEmail = async ({
  campaign,
  prospect,
  draft,
}: {
  campaign: CampaignForm;
  prospect: ProspectForm;
  draft: OutreachDraft;
}): Promise<string> => {
  const host = process.env.SMTP_HOST;
  const port = getPort();
  const secure = process.env.SMTP_SECURE === "true" || port === 465;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;
  const fallbackFrom = campaign.senderEmail || user;
  const fromAddress = process.env.SMTP_FROM || fallbackFrom;

  if (!host || !fromAddress) {
    throw new Error(
      "Missing SMTP configuration. Add SMTP_HOST and either SMTP_FROM or SMTP_USER in .env.local.",
    );
  }

  const transporter = nodemailer.createTransport({
    host,
    port,
    secure,
    auth: user && pass ? { user, pass } : undefined,
  });

  const info = await transporter.sendMail({
    from: formatMailbox(campaign.senderName, fromAddress),
    to: prospect.email,
    replyTo: campaign.replyTo || campaign.senderEmail || process.env.SMTP_REPLY_TO || undefined,
    subject: draft.subject,
    html: draft.html,
    text: draft.text,
  });

  return info.messageId;
};
