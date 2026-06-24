import { v4 as uuidv4 } from 'uuid';

export async function createPaper(payload: any) {
  // In production persist to Postgres and kick off embedding pipeline
  const id = uuidv4();
  return { id, status: 'created' };
}

export async function getPaper(id: string) {
  // Fetch from DB - stubbed
  return null;
}

export async function searchPapers(query: any) {
  // Use vector/TS search in production
  return [];
}
