import { NextResponse } from "next/server";

import { normalizeCampaign, normalizeProspect } from "../../../lib/defaults";
import { generateOutreachEmail } from "../../../lib/email-template";
import { sendOutreachEmail } from "../../../lib/mailer";
import { upsertProspect } from "../../../lib/storage";
import type { CampaignForm, ProspectForm } from "../../../lib/types";

export const runtime = "nodejs";

const assertRequiredFields = (businessName: string, email: string): void => {
  if (!businessName || !email) {
    throw new Error("Business name and email are required.");
  }
};

const isClientError = (message: string): boolean =>
  message.includes("required") || message.includes("Missing SMTP");

export async function POST(request: Request): Promise<NextResponse> {
  let campaign: CampaignForm | undefined;
  let prospect: ProspectForm | undefined;

  try {
    const body = await request.json();
    campaign = normalizeCampaign(body.campaign);
    prospect = normalizeProspect(body.prospect);

    assertRequiredFields(prospect.businessName, prospect.email);

    const draft = generateOutreachEmail(campaign, prospect);
    const messageId = await sendOutreachEmail({ campaign, prospect, draft });

    const record = await upsertProspect({
      ...prospect,
      id: prospect.id,
      status: "sent",
      subject: draft.subject,
      preview: draft.preview,
      lastSentAt: new Date().toISOString(),
      error: undefined,
    });

    return NextResponse.json({ record, messageId });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to send outreach email.";

    if (campaign && prospect) {
      const draft = generateOutreachEmail(campaign, prospect);
      const record = await upsertProspect({
        ...prospect,
        id: prospect.id,
        status: "failed",
        subject: draft.subject,
        preview: draft.preview,
        error: message,
      });

      return NextResponse.json(
        { error: message, record },
        { status: isClientError(message) ? 400 : 500 },
      );
    }

    return NextResponse.json(
      { error: message },
      { status: isClientError(message) ? 400 : 500 },
    );
  }
}
