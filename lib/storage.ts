import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import type { ProspectRecord } from "./types";

const storagePath = path.join(process.cwd(), "data", "prospects.json");

const ensureStorage = async (): Promise<void> => {
  await mkdir(path.dirname(storagePath), { recursive: true });

  try {
    await readFile(storagePath, "utf8");
  } catch {
    await writeFile(storagePath, "[]\n", "utf8");
  }
};

const sortRecords = (records: ProspectRecord[]): ProspectRecord[] =>
  [...records].sort(
    (left, right) =>
      new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime(),
  );

export const listProspects = async (): Promise<ProspectRecord[]> => {
  await ensureStorage();

  const raw = await readFile(storagePath, "utf8");

  try {
    const parsed = JSON.parse(raw) as ProspectRecord[];
    return sortRecords(parsed);
  } catch {
    return [];
  }
};

export const upsertProspect = async (
  input: Omit<ProspectRecord, "createdAt" | "updatedAt">,
): Promise<ProspectRecord> => {
  const now = new Date().toISOString();
  const records = await listProspects();
  const existingIndex = records.findIndex(
    (record) =>
      record.id === input.id ||
      (record.email === input.email && record.businessName === input.businessName),
  );

  const nextRecord: ProspectRecord =
    existingIndex >= 0
      ? {
          ...records[existingIndex],
          ...input,
          createdAt: records[existingIndex].createdAt,
          updatedAt: now,
        }
      : {
          ...input,
          id: input.id ?? crypto.randomUUID(),
          createdAt: now,
          updatedAt: now,
        };

  const nextRecords =
    existingIndex >= 0
      ? records.map((record, index) => (index === existingIndex ? nextRecord : record))
      : [nextRecord, ...records];

  await writeFile(storagePath, `${JSON.stringify(sortRecords(nextRecords), null, 2)}\n`, "utf8");

  return nextRecord;
};
