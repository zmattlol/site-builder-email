export type Tone = "warm" | "professional" | "casual";

export interface CampaignForm {
  senderName: string;
  senderBusiness: string;
  senderEmail: string;
  replyTo: string;
  offerSummary: string;
  valueProposition: string;
  benefitPoints: string;
  callToAction: string;
  portfolioUrl: string;
  calendarLink: string;
  includeOptOut: boolean;
  optOutText: string;
}

export interface ProspectForm {
  id?: string;
  businessName: string;
  contactName: string;
  email: string;
  industry: string;
  city: string;
  googleProfileUrl: string;
  currentPresence: string;
  personalization: string;
  notes: string;
  tone: Tone;
}

export interface OutreachDraft {
  subject: string;
  html: string;
  text: string;
  preview: string;
}

export interface ProspectRecord extends ProspectForm {
  status: "draft" | "sent" | "failed";
  subject: string;
  preview: string;
  createdAt: string;
  updatedAt: string;
  lastSentAt?: string;
  error?: string;
}
