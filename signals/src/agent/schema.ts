import { log } from "../log";

// Each entry moves the schema up one version. Append new entries, and never
// edit one that has shipped.
const MIGRATIONS = [
  `CREATE TABLE devices (
     id TEXT PRIMARY KEY,
     token_hash TEXT NOT NULL UNIQUE,
     email TEXT NOT NULL,
     role TEXT NOT NULL CHECK (role IN ('owner', 'friend')),
     label TEXT NOT NULL,
     created_at INTEGER NOT NULL,
     last_seen_at INTEGER NOT NULL,
     revoked_at INTEGER
   );
   CREATE INDEX devices_by_email ON devices (email, revoked_at);`,
  `CREATE TABLE feedback (
     email TEXT NOT NULL,
     story TEXT NOT NULL,
     vote TEXT CHECK (vote IN ('more', 'less')),
     knew INTEGER NOT NULL,
     follow INTEGER NOT NULL,
     note TEXT NOT NULL,
     updated_at INTEGER NOT NULL,
     PRIMARY KEY (email, story)
   );
   CREATE TABLE requests (
     id TEXT PRIMARY KEY,
     email TEXT NOT NULL,
     url TEXT NOT NULL,
     note TEXT NOT NULL,
     status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
     created_at INTEGER NOT NULL,
     decided_at INTEGER
   );
   CREATE INDEX requests_by_status ON requests (status, created_at);`,
  `ALTER TABLE requests ADD COLUMN used_at INTEGER;`,
];

// Applies pending migrations in one transaction, so a failed one leaves the
// previous schema intact.
export function migrate(storage: DurableObjectStorage): void {
  const { sql } = storage;
  sql.exec(
    "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)",
  );
  const from = schemaVersion(sql);
  if (from === MIGRATIONS.length) {
    return;
  }

  storage.transactionSync(() => {
    for (const statement of MIGRATIONS.slice(from)) {
      sql.exec(statement);
    }
    sql.exec("DELETE FROM schema_version");
    sql.exec(
      "INSERT INTO schema_version (version) VALUES (?)",
      MIGRATIONS.length,
    );
  });
  log("schema_migrated", { from, to: MIGRATIONS.length });
}

export function schemaVersion(sql: SqlStorage): number {
  const [row] = sql
    .exec<{ version: number }>("SELECT version FROM schema_version")
    .toArray();
  return row?.version ?? 0;
}
