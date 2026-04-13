const fs = require("node:fs/promises");
const path = require("node:path");

const DATA_FILE = path.join(__dirname, "..", "data", "leads.json");

async function ensureStore() {
  try {
    await fs.access(DATA_FILE);
  } catch {
    await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify({ campaigns: [] }, null, 2));
  }
}

async function readStore() {
  await ensureStore();

  const raw = await fs.readFile(DATA_FILE, "utf8");
  const parsed = JSON.parse(raw);

  if (!Array.isArray(parsed.campaigns)) {
    return { campaigns: [] };
  }

  return parsed;
}

async function saveCampaign(campaign) {
  const store = await readStore();
  store.campaigns.unshift(campaign);
  await fs.writeFile(DATA_FILE, JSON.stringify(store, null, 2));
  return campaign;
}

async function listCampaigns() {
  const store = await readStore();
  return store.campaigns;
}

module.exports = {
  listCampaigns,
  saveCampaign,
};
