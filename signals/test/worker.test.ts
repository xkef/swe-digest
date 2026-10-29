import { reset } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { afterEach, describe, expect, it } from "vitest";

// The plugin keeps Durable Object storage between tests, so each test
// deletes it afterwards.
afterEach(async () => {
  await reset();
});

describe("GET /health", () => {
  it("reports the schema version after reaching the agent", async () => {
    const response = await exports.default.fetch("https://signals.test/health");

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true, schema: 1 });
  });
});

describe("unknown paths", () => {
  it("return 404", async () => {
    const response = await exports.default.fetch("https://signals.test/nope");

    expect(response.status).toBe(404);
  });
});
