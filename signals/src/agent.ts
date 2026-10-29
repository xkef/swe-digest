import { DurableObject } from "cloudflare:workers";
import type { Feedback, RequestStatus, StoryRequest, Vote } from "./feedback";
import { log } from "./log";

type FeedbackRow = {
  story: string;
  vote: Vote | null;
  knew: number;
  follow: number;
  note: string;
};

type RequestRow = {
  id: string;
  email: string;
  url: string;
  note: string;
  status: RequestStatus;
  created_at: number;
};

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

// A friend can have this many requests waiting for the owner at once.
export const MAX_PENDING = 20;

// The owner's request list shows decided requests for this long.
const DECIDED_VISIBLE_MS = 30 * 86_400_000;
const DAY_MS = 86_400_000;

// What the digest runs read: approved requests no run has used yet, and
// every reader's feedback updated in the window, totaled per story. Only the
// owner can write notes, so every note here is the owner's.
export interface Signals {
  requests: { id: string; url: string; note: string }[];
  feedback: {
    story: string;
    more: number;
    less: number;
    knew: number;
    follow: number;
    notes: string[];
  }[];
}

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

  async feedbackFor(email: string, day: string): Promise<Feedback[]> {
    return this.sql
      .exec<FeedbackRow>(
        `SELECT story, vote, knew, follow, note FROM feedback
         WHERE email = ? AND story LIKE ? ORDER BY story`,
        email,
        `${day}/%`,
      )
      .toArray()
      .map(toFeedback);
  }

  // Feedback belongs to the reader, not the device, so a phone and a laptop
  // show the same state. Clearing every field deletes the row.
  async saveFeedback(email: string, feedback: Feedback): Promise<void> {
    const empty = feedback.vote === null && !feedback.knew
      && !feedback.follow && feedback.note === "";
    if (empty) {
      this.sql.exec(
        "DELETE FROM feedback WHERE email = ? AND story = ?",
        email,
        feedback.story,
      );
      return;
    }

    this.sql.exec(
      `INSERT INTO feedback
         (email, story, vote, knew, follow, note, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT DO UPDATE SET vote = excluded.vote, knew = excluded.knew,
         follow = excluded.follow, note = excluded.note,
         updated_at = excluded.updated_at`,
      email,
      feedback.story,
      feedback.vote,
      Number(feedback.knew),
      Number(feedback.follow),
      feedback.note,
      Date.now(),
    );
  }

  // The owner's requests count at once. A friend's wait for the owner.
  async addRequest(
    reader: Reader,
    url: string,
    note: string,
  ): Promise<StoryRequest | null> {
    const status: RequestStatus = reader.role === "owner"
      ? "approved"
      : "pending";
    if (
      status === "pending" && this.pendingCount(reader.email) >= MAX_PENDING
    ) {
      log("request_rejected", { reason: "pending_limit" });
      return null;
    }

    const now = Date.now();
    const id = crypto.randomUUID();
    this.sql.exec(
      `INSERT INTO requests (id, email, url, note, status, created_at, decided_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      id,
      reader.email,
      url,
      note,
      status,
      now,
      status === "approved" ? now : null,
    );
    log("request_added", { request: id, status });
    return { id, url, note, status, from: reader.email, createdAt: now };
  }

  // The owner sees every pending request and the last 30 days of decided
  // ones. A friend sees only their own.
  async listRequests(reader: Reader): Promise<StoryRequest[]> {
    const since = Date.now() - DECIDED_VISIBLE_MS;
    const rows = reader.role === "owner"
      ? this.sql.exec<RequestRow>(
        `SELECT * FROM requests
         WHERE status = 'pending' OR created_at >= ?
         ORDER BY created_at DESC`,
        since,
      )
      : this.sql.exec<RequestRow>(
        `SELECT * FROM requests WHERE email = ? AND created_at >= ?
         ORDER BY created_at DESC`,
        reader.email,
        since,
      );
    return rows.toArray().map(toRequest);
  }

  async decide(id: string, status: RequestStatus): Promise<boolean> {
    const changed = this.sql.exec(
      `UPDATE requests SET status = ?, decided_at = ?
       WHERE id = ? AND status = 'pending'`,
      status,
      Date.now(),
      id,
    ).rowsWritten;
    if (changed > 0) {
      log("request_decided", { request: id, status });
    }
    return changed > 0;
  }

  async signals(days: number): Promise<Signals> {
    const since = Date.now() - days * DAY_MS;
    const requests = this.sql
      .exec<{ id: string; url: string; note: string }>(
        `SELECT id, url, note FROM requests
         WHERE status = 'approved' AND used_at IS NULL ORDER BY created_at`,
      )
      .toArray();
    const totals = this.sql
      .exec<
        {
          story: string;
          more: number;
          less: number;
          knew: number;
          follow: number;
          notes: string;
        }
      >(
        `SELECT story,
           SUM(vote = 'more') AS more, SUM(vote = 'less') AS less,
           SUM(knew) AS knew, SUM(follow) AS follow,
           json_group_array(note) FILTER (WHERE note != '') AS notes
         FROM feedback WHERE updated_at >= ?
         GROUP BY story ORDER BY story`,
        since,
      )
      .toArray();

    return {
      requests,
      feedback: totals.map((row) => ({
        ...row,
        notes: JSON.parse(row.notes) as string[],
      })),
    };
  }

  // A run marks the requests it covered, so the next run does not see them.
  async markUsed(ids: string[]): Promise<number> {
    const now = Date.now();
    let marked = 0;
    for (const id of ids) {
      marked += this.sql.exec(
        `UPDATE requests SET used_at = ?
         WHERE id = ? AND status = 'approved' AND used_at IS NULL`,
        now,
        id,
      ).rowsWritten;
    }
    log("requests_used", { marked });
    return marked;
  }

  private pendingCount(email: string): number {
    return this.sql
      .exec<{ n: number }>(
        "SELECT COUNT(*) AS n FROM requests WHERE email = ? AND status = 'pending'",
        email,
      )
      .one().n;
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

function toFeedback(row: FeedbackRow): Feedback {
  return {
    story: row.story,
    vote: row.vote,
    knew: row.knew === 1,
    follow: row.follow === 1,
    note: row.note,
  };
}

function toRequest(row: RequestRow): StoryRequest {
  return {
    id: row.id,
    url: row.url,
    note: row.note,
    status: row.status,
    from: row.email,
    createdAt: row.created_at,
  };
}
