import { reset, runInDurableObject } from "cloudflare:test";
import { env, exports } from "cloudflare:workers";
import { generateKeyPair } from "jose";
import { afterEach, describe, expect, it } from "vitest";
import type { ReaderAgent } from "../src/agent";
import { enrollment } from "../src/config";
import { call, enroll, tokenFrom } from "./helpers";

const SITE_URL = "https://xkef.github.io/swe-digest/";

afterEach(async () => {
  await reset();
});

function me(token: string): Promise<Response> {
  return call(token, "GET", "/me");
}

describe("GET /enroll", () => {
  it("redirects to the site with a token that identifies the device", async () => {
    const response = await enroll();

    expect(response.status).toBe(303);
    expect(response.headers.get("Location")).toMatch(
      new RegExp(`^${SITE_URL}#signals-token=[A-Za-z0-9_-]{43}$`),
    );
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    const reader = await me(tokenFrom(response));
    expect(reader.status).toBe(200);
    expect(await reader.json()).toMatchObject({ role: "friend" });
  });

  it("makes the owner's email, in any case, the owner", async () => {
    const response = await enroll({ email: "OWNER@example.com" });

    expect(await (await me(tokenFrom(response))).json()).toMatchObject({
      role: "owner",
    });
  });

  it("stores only a hash of the token", async () => {
    const token = tokenFrom(await enroll());

    const stored = await runInDurableObject(
      env.READERS.get(env.READERS.idFromName("digest")),
      (_: ReaderAgent, state: DurableObjectState) =>
        state.storage.sql
          .exec<{ token_hash: string }>("SELECT token_hash FROM devices")
          .one().token_hash,
    );
    expect(stored).not.toBe(token);
    expect(stored).toHaveLength(43);
  });

  it("keeps a cleaned device label", async () => {
    await enroll({}, "?device=%3Cb%3EPixel%209%3C%2Fb%3E");

    const label = await runInDurableObject(
      env.READERS.get(env.READERS.idFromName("digest")),
      (_: ReaderAgent, state: DurableObjectState) =>
        state.storage.sql
          .exec<{ label: string }>("SELECT label FROM devices")
          .one().label,
    );
    expect(label).toBe("bPixel 9b");
  });

  it("rejects requests without a valid Access token", async () => {
    const missing = await exports.default.fetch("https://signals.test/enroll");
    const other = await generateKeyPair("RS256");

    expect(missing.status).toBe(403);
    expect((await enroll({ audience: "other-app" })).status).toBe(403);
    expect((await enroll({ issuer: "https://evil.example" })).status).toBe(403);
    expect((await enroll({ expiresIn: "-1m" })).status).toBe(403);
    expect((await enroll({ key: other.privateKey })).status).toBe(403);
  });

  it("rejects other methods", async () => {
    const response = await exports.default.fetch(
      "https://signals.test/enroll",
      { method: "POST" },
    );

    expect(response.status).toBe(405);
  });

  it(`revokes the least recently used device past ${enrollment.maxDevices}`, async () => {
    const tokens: string[] = [];
    for (let i = 0; i <= enrollment.maxDevices; i++) {
      tokens.push(tokenFrom(await enroll()));
    }

    const results = await Promise.all(
      tokens.map(async (t) => (await me(t)).status),
    );
    expect(results.filter((status) => status === 200)).toHaveLength(
      enrollment.maxDevices,
    );
    expect((await me(tokens.at(-1) ?? "")).status).toBe(200);
  });
});

describe("GET /me", () => {
  it("answers 401 with CORS headers for an unknown token", async () => {
    const response = await me("not-a-token");

    expect(response.status).toBe(401);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe(
      "https://xkef.github.io",
    );
  });

  it("answers the CORS preflight", async () => {
    const response = await exports.default.fetch("https://signals.test/me", {
      method: "OPTIONS",
    });

    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Headers")).toBe(
      "Authorization, Content-Type",
    );
  });
});
