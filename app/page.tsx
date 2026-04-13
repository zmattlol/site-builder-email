import OutreachDashboard from "../components/outreach-dashboard";
import { defaultCampaign, defaultProspect } from "../lib/defaults";
import { hasSmtpConfig } from "../lib/mailer";
import { listProspects } from "../lib/storage";

export default async function Home() {
  const prospects = await listProspects();

  return (
    <main className="page-shell">
      <OutreachDashboard
        initialCampaign={defaultCampaign}
        initialProspect={defaultProspect}
        initialProspects={prospects}
        emailConfigured={hasSmtpConfig()}
      />
    </main>
  );
}
