import { enrollment } from "../config";
import { log } from "../log";
import type { Reader, Role } from "../types";

type DeviceRow = {
  id: string;
  email: string;
  role: Role;
  last_seen_at: number;
};

export class Devices {
  readonly #storage: DurableObjectStorage;

  constructor(storage: DurableObjectStorage) {
    this.#storage = storage;
  }

  // Issues a device token. Only its SHA-256 hash is stored, so afterwards the
  // token exists in one place: the enrolled browser.
  async enroll(email: string, role: Role, label: string): Promise<string> {
    const token = base64url(
      crypto.getRandomValues(new Uint8Array(enrollment.tokenBytes)),
    );
    const hash = await sha256(token);
    const id = crypto.randomUUID();
    const now = Date.now();
    const { sql } = this.#storage;

    this.#storage.transactionSync(() => {
      sql.exec(
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
      sql.exec(
        `UPDATE devices SET revoked_at = ?
         WHERE id IN (
           SELECT id FROM devices WHERE email = ? AND revoked_at IS NULL
           ORDER BY last_seen_at DESC, created_at DESC, rowid DESC
           LIMIT -1 OFFSET ?
         )`,
        now,
        email,
        enrollment.maxDevices,
      );
    });

    log("device_enrolled", { device: id, role });
    return token;
  }

  async authenticate(token: string): Promise<Reader | null> {
    const { sql } = this.#storage;
    const [row] = sql
      .exec<DeviceRow>(
        `SELECT id, email, role, last_seen_at FROM devices
         WHERE token_hash = ? AND revoked_at IS NULL`,
        await sha256(token),
      )
      .toArray();
    if (!row) {
      return null;
    }

    const now = Date.now();
    if (now - row.last_seen_at >= enrollment.seenInterval) {
      sql.exec("UPDATE devices SET last_seen_at = ? WHERE id = ?", now, row.id);
    }
    return { device: row.id, email: row.email, role: row.role };
  }
}

async function sha256(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  return base64url(new Uint8Array(await crypto.subtle.digest("SHA-256", data)));
}

function base64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replace(/=+$/, "");
}
