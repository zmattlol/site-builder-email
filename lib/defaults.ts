import type { CampaignForm, ProspectForm } from "./types";

export const defaultCampaign: CampaignForm = {
  senderName: "",
  senderBusiness: "",
  senderEmail: "",
  replyTo: "",
  offerSummary:
    "building and setting up a personalized website for local businesses that do not have one yet",
  valueProposition:
    "A simple website can make a business look more established, give customers one clear place to learn about services, and turn profile views into calls or quote requests.",
  benefitPoints:
    "Show services, hours, and contact details in one place\nLook more established when people search the business name\nGive customers an easy way to call, message, or request a quote",
  callToAction:
    "If this is something you'd be interested in, I can put together a simple idea for your business and handle the setup from start to finish.",
  portfolioUrl: "",
  calendarLink: "",
  includeOptOut: true,
  optOutText: "If now is not the right time, just reply and I will not follow up.",
};

export const defaultProspect: ProspectForm = {
  businessName: "",
  contactName: "",
  email: "",
  industry: "",
  city: "",
  googleProfileUrl: "",
  currentPresence: "their Google Business Profile",
  personalization: "",
  notes: "",
  tone: "warm",
};

const cleanString = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

export const normalizeCampaign = (input: unknown): CampaignForm => {
  const data = typeof input === "object" && input !== null ? input : {};
  const source = data as Partial<CampaignForm>;

  return {
    senderName: cleanString(source.senderName),
    senderBusiness: cleanString(source.senderBusiness),
    senderEmail: cleanString(source.senderEmail),
    replyTo: cleanString(source.replyTo),
    offerSummary: cleanString(source.offerSummary) || defaultCampaign.offerSummary,
    valueProposition:
      cleanString(source.valueProposition) || defaultCampaign.valueProposition,
    benefitPoints: cleanString(source.benefitPoints) || defaultCampaign.benefitPoints,
    callToAction: cleanString(source.callToAction) || defaultCampaign.callToAction,
    portfolioUrl: cleanString(source.portfolioUrl),
    calendarLink: cleanString(source.calendarLink),
    includeOptOut:
      typeof source.includeOptOut === "boolean"
        ? source.includeOptOut
        : defaultCampaign.includeOptOut,
    optOutText: cleanString(source.optOutText) || defaultCampaign.optOutText,
  };
};

export const normalizeProspect = (input: unknown): ProspectForm => {
  const data = typeof input === "object" && input !== null ? input : {};
  const source = data as Partial<ProspectForm>;
  const tone = cleanString(source.tone);

  return {
    id: cleanString(source.id) || undefined,
    businessName: cleanString(source.businessName),
    contactName: cleanString(source.contactName),
    email: cleanString(source.email),
    industry: cleanString(source.industry),
    city: cleanString(source.city),
    googleProfileUrl: cleanString(source.googleProfileUrl),
    currentPresence: cleanString(source.currentPresence) || defaultProspect.currentPresence,
    personalization: cleanString(source.personalization),
    notes: cleanString(source.notes),
    tone:
      tone === "professional" || tone === "casual" || tone === "warm"
        ? tone
        : defaultProspect.tone,
  };
};
