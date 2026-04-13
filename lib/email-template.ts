import type { CampaignForm, OutreachDraft, ProspectForm, Tone } from "./types";

const escapeHtml = (value: string): string =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const toBulletPoints = (value: string): string[] =>
  value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5);

const toneOpening: Record<Tone, string> = {
  warm: "I hope you're doing well.",
  professional: "I wanted to reach out with a quick idea.",
  casual: "Quick idea I thought might be useful.",
};

const toneCloser: Record<Tone, string> = {
  warm: "Happy to send over a simple concept if helpful.",
  professional: "I would be glad to share a simple concept if it would be useful.",
  casual: "Happy to sketch out a quick idea if you want.",
};

const formatGreeting = (prospect: ProspectForm): string =>
  prospect.contactName
    ? `Hi ${prospect.contactName},`
    : `Hi ${prospect.businessName || "there"},`;

const buildIntroduction = (prospect: ProspectForm): string => {
  const businessName = prospect.businessName || "your business";
  const presence = prospect.currentPresence || "your online presence";
  const location = prospect.city ? ` in ${prospect.city}` : "";

  return `I came across ${businessName}${location} through ${presence} and noticed you do not seem to have a dedicated website yet.`;
};

const buildPersonalization = (prospect: ProspectForm): string | null => {
  if (prospect.personalization) {
    return `From what I saw, ${prospect.personalization}.`;
  }

  if (prospect.notes) {
    return prospect.notes.endsWith(".") ? prospect.notes : `${prospect.notes}.`;
  }

  return null;
};

const buildSignature = (campaign: CampaignForm): string[] => {
  const lines = [campaign.senderName, campaign.senderBusiness, campaign.senderEmail].filter(Boolean);

  if (campaign.portfolioUrl) {
    lines.push(campaign.portfolioUrl);
  }

  if (campaign.calendarLink) {
    lines.push(campaign.calendarLink);
  }

  return lines;
};

export const generateOutreachEmail = (
  campaign: CampaignForm,
  prospect: ProspectForm,
): OutreachDraft => {
  const benefits = toBulletPoints(campaign.benefitPoints);
  const greeting = formatGreeting(prospect);
  const intro = buildIntroduction(prospect);
  const personalization = buildPersonalization(prospect);
  const signature = buildSignature(campaign);
  const businessName = prospect.businessName || "your business";
  const subject = prospect.city
    ? `Quick website idea for ${businessName} in ${prospect.city}`
    : `Quick website idea for ${businessName}`;

  const textLines = [
    greeting,
    "",
    toneOpening[prospect.tone],
    intro,
    campaign.valueProposition,
    "",
    `I help businesses with ${campaign.offerSummary}.`,
    "",
    `For ${businessName}, a simple personalized site could help:`,
    ...benefits.map((benefit) => `- ${benefit}`),
    "",
    personalization,
    toneCloser[prospect.tone],
    campaign.callToAction,
    "",
    ...(campaign.includeOptOut ? [campaign.optOutText, ""] : []),
    ...signature,
  ].filter(Boolean);

  const htmlBenefits = benefits
    .map((benefit) => `<li>${escapeHtml(benefit)}</li>`)
    .join("");

  const htmlParagraphs = [
    `<p>${escapeHtml(greeting)}</p>`,
    `<p>${escapeHtml(toneOpening[prospect.tone])} ${escapeHtml(intro)} ${escapeHtml(
      campaign.valueProposition,
    )}</p>`,
    `<p>I help businesses with ${escapeHtml(campaign.offerSummary)}.</p>`,
    `<p>For ${escapeHtml(businessName)}, a simple personalized site could help:</p>`,
    `<ul>${htmlBenefits}</ul>`,
    personalization ? `<p>${escapeHtml(personalization)}</p>` : "",
    `<p>${escapeHtml(toneCloser[prospect.tone])} ${escapeHtml(campaign.callToAction)}</p>`,
    campaign.includeOptOut ? `<p>${escapeHtml(campaign.optOutText)}</p>` : "",
    `<p>${signature.map(escapeHtml).join("<br />")}</p>`,
  ].filter(Boolean);

  const text = textLines.join("\n");

  return {
    subject,
    html: htmlParagraphs.join(""),
    text,
    preview: text.slice(0, 180),
  };
};
