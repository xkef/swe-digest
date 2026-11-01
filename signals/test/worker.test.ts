import { reset } from "cloudflare:test";
import { env, exports } from "cloudflare:workers";
import { afterEach, describe, expect, it, vi } from "vitest";
import { call } from "./helpers";

// The `simple.limit` of the LIMITER binding in wrangler.jsonc.
const LIMIT = 60;

// The plugin keeps Durable Object storage between tests, so each test
// deletes it afterwards.
afterEach(async () => {
  vi.restoreAllMocks();
  await reset();
});

function fromAddress(address: string, path = "/health"): Promise<Response> {
  return exports.default.fetch(`https://signals.test${path}`, {
    headers: { "CF-Connecting-IP": address },
  });
}

describe("requests that cannot authenticate", () => {
  it("never reach the store with a bearer no enrollment issues", async () => {
    const store = vi.spyOn(env.SIGNALS, "getByName");

    for (const token of ["", "x", "a".repeat(42), "a".repeat(44), `${"a".repeat(42)}+`]) {
      expect((await call(token, "GET", "/me")).status).toBe(401);
    }
    expect(store).not.toHaveBeenCalled();
  });
});

describe("rate limit", () => {
  // The local limiter keeps its counts between runs, so each run starts from
  // fresh addresses.
  it("answers 429 once an address exceeds the limit", async () => {
    const [busy, other] = [crypto.randomUUID(), crypto.randomUUID()];
    for (let i = 0; i < LIMIT; i++) {
      expect((await fromAddress(busy)).status).toBe(200);
    }

    expect((await fromAddress(busy)).status).toBe(429);
    expect((await fromAddress(busy, "/me")).status).toBe(429);
    expect((await fromAddress(other)).status).toBe(200);
  });
});

describe("GET /health", () => {
  it("reports the schema version after reaching the store", async () => {
    const response = await exports.default.fetch("https://signals.test/health");

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, schema: 3 });
  });
});

describe("unknown paths", () => {
  it("return 404", async () => {
    const response = await exports.default.fetch("https://signals.test/nope");

    expect(response.status).toBe(404);
  });
});
