import { NextResponse } from "next/server";

import { normalizeCampaign, normalizeProspect } from "../../../lib/defaults";
import { generateOutreachEmail } from "../../../lib/email-template";
import { listProspects, upsertProspect } from "../../../lib/storage";

export const runtime = "nodejs";

const assertRequiredFields = (businessName: string, email: string): void => {
  if (!businessName || !email) {
    throw new Error("Business name and email are required.");
  }
};

export async function GET(): Promise<NextResponse> {
  const records = await listProspects();
  return NextResponse.json({ records });
}

export async function POST(request: Request): Promise<NextResponse> {
  try {
    const body = await request.json();
    const campaign = normalizeCampaign(body.campaign);
    const prospect = normalizeProspect(body.prospect);

    assertRequiredFields(prospect.businessName, prospect.email);

    const draft = generateOutreachEmail(campaign, prospect);
    const record = await upsertProspect({
      ...prospect,
      id: prospect.id,
      status: "draft",
      subject: draft.subject,
      preview: draft.preview,
      error: undefined,
    });

    return NextResponse.json({ record });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to save the outreach draft.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
