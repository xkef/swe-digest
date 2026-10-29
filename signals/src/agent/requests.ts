import { limits } from "../config";
import { log } from "../log";
import type { Reader, RequestStatus, Signals, StoryRequest } from "../types";

type RequestRow = {
  id: string;
  email: string;
  url: string;
  note: string;
  status: RequestStatus;
  created_at: number;
};

export class RequestStore {
  readonly #sql: SqlStorage;

  constructor(sql: SqlStorage) {
    this.#sql = sql;
  }

  // The owner's requests count at once. A friend's wait for the owner.
  add(reader: Reader, url: string, note: string): StoryRequest | null {
    const status: RequestStatus = reader.role === "owner"
      ? "approved"
      : "pending";
    if (status === "pending" && this.#pending(reader.email) >= limits.pending) {
      log("request_rejected", { reason: "pending_limit" });
      return null;
    }

    const id = crypto.randomUUID();
    const now = Date.now();
    this.#sql.exec(
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

  // The owner sees every pending request and the recently decided ones. A
  // friend sees only their own.
  list(reader: Reader): StoryRequest[] {
    const since = Date.now() - limits.decidedVisible;
    const rows = reader.role === "owner"
      ? this.#sql.exec<RequestRow>(
        `SELECT * FROM requests WHERE status = 'pending' OR created_at >= ?
         ORDER BY created_at DESC`,
        since,
      )
      : this.#sql.exec<RequestRow>(
        `SELECT * FROM requests WHERE email = ? AND created_at >= ?
         ORDER BY created_at DESC`,
        reader.email,
        since,
      );
    return rows.toArray().map(({ email, created_at, ...row }) => ({
      ...row,
      from: email,
      createdAt: created_at,
    }));
  }

  decide(id: string, status: RequestStatus): boolean {
    const { rowsWritten } = this.#sql.exec(
      `UPDATE requests SET status = ?, decided_at = ?
       WHERE id = ? AND status = 'pending'`,
      status,
      Date.now(),
      id,
    );
    if (rowsWritten > 0) {
      log("request_decided", { request: id, status });
    }
    return rowsWritten > 0;
  }

  unused(): Signals["requests"] {
    return this.#sql
      .exec<Signals["requests"][number]>(
        `SELECT id, url, note FROM requests
         WHERE status = 'approved' AND used_at IS NULL ORDER BY created_at`,
      )
      .toArray();
  }

  // A run marks the requests it covered, so later runs skip them.
  markUsed(ids: string[]): number {
    const { rowsWritten } = this.#sql.exec(
      `UPDATE requests SET used_at = ?
       WHERE id IN (SELECT value FROM json_each(?))
         AND status = 'approved' AND used_at IS NULL`,
      Date.now(),
      JSON.stringify(ids),
    );
    log("requests_used", { marked: rowsWritten });
    return rowsWritten;
  }

  #pending(email: string): number {
    return this.#sql
      .exec<{ n: number }>(
        "SELECT COUNT(*) AS n FROM requests WHERE email = ? AND status = 'pending'",
        email,
      )
      .one().n;
  }
}
