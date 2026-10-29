import { DurableObject } from "cloudflare:workers";
import { log } from "./log";

// Each entry moves the schema up one version. Append new entries, and never
// edit one that has shipped.
const MIGRATIONS: string[] = [
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
];

// Enrolling one more device than this revokes the reader's least recently
// seen device, so a lost phone does not need a manual cleanup.
export const MAX_DEVICES = 5;

// last_seen_at is written at most this often, so reads stay reads.
const SEEN_INTERVAL_MS = 3_600_000;
const TOKEN_BYTES = 32;

export type Role = "owner" | "friend";

export interface Reader {
  device: string;
  email: string;
  role: Role;
}

// The one Durable Object behind the Worker, addressed by the name "digest".
// It keeps the feedback state in its own SQLite and upgrades the schema when
// it starts.
export class ReaderAgent extends DurableObject<Env> {
  private readonly sql: SqlStorage;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    ctx.blockConcurrencyWhile(async () => this.migrate());
  }

  async schemaVersion(): Promise<number> {
    return this.version();
  }

  // Issues a device token. Only its SHA-256 hash is stored, so the token
  // exists in exactly one place afterwards: the enrolled browser.
  async enroll(email: string, role: Role, label: string): Promise<string> {
    const token = base64url(
      crypto.getRandomValues(new Uint8Array(TOKEN_BYTES)),
    );
    const hash = await sha256(token);
    const id = crypto.randomUUID();
    const now = Date.now();

    this.ctx.storage.transactionSync(() => {
      this.sql.exec(
        `INSERT INTO devices
           (id, token_hash, email, role, label, created_at, last_seen_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        id,
        hash,
        email,
        role,
        label,
        now,
        now,
      );
      this.sql.exec(
        `UPDATE devices SET revoked_at = ?
         WHERE id IN (
           SELECT id FROM devices WHERE email = ? AND revoked_at IS NULL
           ORDER BY last_seen_at DESC, created_at DESC, rowid DESC
           LIMIT -1 OFFSET ?
         )`,
        now,
        email,
        MAX_DEVICES,
      );
    });

    log("device_enrolled", { device: id, role });
    return token;
  }

  async authenticate(token: string): Promise<Reader | null> {
    const hash = await sha256(token);
    const row = this.sql
      .exec<{ id: string; email: string; role: Role; last_seen_at: number }>(
        `SELECT id, email, role, last_seen_at FROM devices
         WHERE token_hash = ? AND revoked_at IS NULL`,
        hash,
      )
      .toArray()[0];
    if (!row) {
      return null;
    }

    const now = Date.now();
    if (now - row.last_seen_at >= SEEN_INTERVAL_MS) {
      this.sql.exec(
        "UPDATE devices SET last_seen_at = ? WHERE id = ?",
        now,
        row.id,
      );
    }
    return { device: row.id, email: row.email, role: row.role };
  }

  private migrate(): void {
    this.sql.exec(
      "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)",
    );
    const from = this.version();
    if (from === MIGRATIONS.length) {
      return;
    }

    this.ctx.storage.transactionSync(() => {
      for (const statement of MIGRATIONS.slice(from)) {
        this.sql.exec(statement);
      }
      this.sql.exec("DELETE FROM schema_version");
      this.sql.exec(
        "INSERT INTO schema_version (version) VALUES (?)",
        MIGRATIONS.length,
      );
    });
    log("schema_migrated", { from, to: MIGRATIONS.length });
  }

  private version(): number {
    const row = this.sql
      .exec<{ version: number }>("SELECT version FROM schema_version")
      .toArray()[0];
    return row?.version ?? 0;
  }
}

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return base64url(new Uint8Array(digest));
}

function base64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replace(/=+$/, "");
}
