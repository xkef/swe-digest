import { DurableObject } from "cloudflare:workers";
import { log } from "./log";

// Each entry moves the schema up one version. Append new entries, and never
// edit one that has shipped.
const MIGRATIONS: string[] = [];

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
