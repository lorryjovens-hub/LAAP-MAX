import { openDB, type DBSchema, type IDBPDatabase } from 'idb';

export interface CodeProjectFile {
  path: string;
  content: string;
}

export interface CodeProject {
  id: string;
  name: string;
  template: string;
  files: CodeProjectFile[];
  created_at: string;
  updated_at: string;
}

interface CodeProjectDB extends DBSchema {
  codeProjects: {
    key: string;
    value: CodeProject;
  };
}

const DB_NAME = 'laap-code-projects';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<CodeProjectDB>> | null = null;

function getDb(): Promise<IDBPDatabase<CodeProjectDB>> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('IndexedDB is only available in the browser'));
  }
  if (dbPromise) return dbPromise;
  dbPromise = openDB<CodeProjectDB>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      db.createObjectStore('codeProjects', { keyPath: 'id' });
    },
  });
  return dbPromise;
}

export async function saveCodeProject(project: CodeProject): Promise<void> {
  const db = await getDb();
  await db.put('codeProjects', project);
}

export async function loadCodeProject(id: string): Promise<CodeProject | undefined> {
  const db = await getDb();
  return db.get('codeProjects', id);
}

export async function listCodeProjects(): Promise<CodeProject[]> {
  const db = await getDb();
  return db.getAll('codeProjects');
}

export async function deleteCodeProject(id: string): Promise<void> {
  const db = await getDb();
  await db.delete('codeProjects', id);
}

export function newProjectId(): string {
  return `proj_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function projectToRecord(files: CodeProjectFile[]): Record<string, { file: { contents: string } }> {
  const record: Record<string, { file: { contents: string } }> = {};
  for (const f of files) {
    record[f.path] = { file: { contents: f.content } };
  }
  return record;
}
