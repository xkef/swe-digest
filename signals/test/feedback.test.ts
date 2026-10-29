import { reset } from "cloudflare:test";
import { afterEach, describe, expect, it } from "vitest";
import { limits } from "../src/config";
import { call, deviceToken, FRIEND, OWNER } from "./helpers";

const STORY = "2026-10-30/cursor-marketplace-served-a-trojanized-extension";

afterEach(async () => {
  await reset();
});

describe("feedback", () => {
  it("saves a reader's feedback and returns it for the story's day", async () => {
    const token = await deviceToken();

    const saved = await call(token, "PUT", `/feedback/${STORY}`, {
      vote: "more",
      follow: true,
    });
    const listed = await call(token, "GET", "/feedback?day=2026-10-30");

    expect(saved.status).toBe(204);
    expect(await listed.json()).toEqual([
      { story: STORY, vote: "more", knew: false, follow: true, note: "" },
    ]);
  });

  it("shares feedback across a reader's devices but not between readers", async () => {
    const laptop = await deviceToken(FRIEND);
    const phone = await deviceToken(FRIEND);
    const owner = await deviceToken(OWNER);

    await call(laptop, "PUT", `/feedback/${STORY}`, { knew: true });

    expect(await (await call(phone, "GET", "/feedback?day=2026-10-30")).json())
      .toHaveLength(1);
    expect(await (await call(owner, "GET", "/feedback?day=2026-10-30")).json())
      .toEqual([]);
  });

  it("deletes the row when every field is cleared", async () => {
    const token = await deviceToken();
    await call(token, "PUT", `/feedback/${STORY}`, { vote: "less" });

    await call(token, "PUT", `/feedback/${STORY}`, { vote: null });

    expect(await (await call(token, "GET", "/feedback?day=2026-10-30")).json())
      .toEqual([]);
  });

  it("lets only the owner write notes", async () => {
    const friend = await deviceToken(FRIEND);
    const owner = await deviceToken(OWNER);

    expect(
      (await call(friend, "PUT", `/feedback/${STORY}`, { note: "x" })).status,
    ).toBe(403);
    expect(
      (await call(owner, "PUT", `/feedback/${STORY}`, { note: "x" })).status,
    ).toBe(204);
  });

  it("rejects malformed feedback", async () => {
    const token = await deviceToken();

    for (
      const body of [
        { vote: "up" },
        { knew: "yes" },
        { note: "x".repeat(501) },
        [],
      ]
    ) {
      expect((await call(token, "PUT", `/feedback/${STORY}`, body)).status)
        .toBe(400);
    }
    expect((await call(token, "GET", "/feedback?day=yesterday")).status).toBe(
      400,
    );
    expect((await call(token, "PUT", "/feedback/not-a-story", {})).status)
      .toBe(404);
  });

  it("accepts the longest slugs the site publishes", async () => {
    const token = await deviceToken();
    const story = `2026-10-30/${"a-".repeat(110)}b`;

    expect(
      (await call(token, "PUT", `/feedback/${story}`, { knew: true }))
        .status,
    ).toBe(204);
  });

  it("needs a device token", async () => {
    expect((await call("", "GET", "/feedback?day=2026-10-30")).status).toBe(
      401,
    );
  });
});

describe("story requests", () => {
  it("approves the owner's requests at once", async () => {
    const owner = await deviceToken(OWNER);

    const response = await call(owner, "POST", "/requests", {
      url: "https://example.com/post",
    });

    expect(response.status).toBe(201);
    expect(await response.json()).toMatchObject({ status: "approved" });
  });

  it("holds a friend's request until the owner decides", async () => {
    const friend = await deviceToken(FRIEND);
    const owner = await deviceToken(OWNER);

    const added = await (await call(friend, "POST", "/requests", {
      url: "https://example.com/post",
      note: "worth a look",
    })).json() as { id: string; status: string };
    const pending = await (await call(owner, "GET", "/requests")).json();

    expect(added.status).toBe("pending");
    expect(pending).toMatchObject([{ id: added.id, from: FRIEND }]);
    expect(
      (await call(friend, "PUT", `/requests/${added.id}`, {
        status: "approved",
      })).status,
    ).toBe(403);
    expect(
      (await call(owner, "PUT", `/requests/${added.id}`, {
        status: "approved",
      })).status,
    ).toBe(204);
    expect(
      (await call(owner, "PUT", `/requests/${added.id}`, {
        status: "rejected",
      })).status,
    ).toBe(404);
  });

  it("shows a friend only their own requests", async () => {
    const friend = await deviceToken(FRIEND);
    const other = await deviceToken("other@example.com");
    await call(other, "POST", "/requests", { url: "https://example.com/a" });

    expect(await (await call(friend, "GET", "/requests")).json()).toEqual([]);
  });

  it(`caps a friend at ${limits.pending} pending requests`, async () => {
    const friend = await deviceToken(FRIEND);
    for (let i = 0; i < limits.pending; i++) {
      await call(friend, "POST", "/requests", {
        url: `https://example.com/${i}`,
      });
    }

    const response = await call(friend, "POST", "/requests", {
      url: "https://example.com/over",
    });

    expect(response.status).toBe(429);
  });

  it("rejects a URL that is not http or https", async () => {
    const token = await deviceToken();

    for (const url of ["javascript:alert(1)", "not a url", 7]) {
      expect((await call(token, "POST", "/requests", { url })).status).toBe(
        400,
      );
    }
  });
});

describe("CORS", () => {
  it("answers every reader route with the site's origin", async () => {
    const response = await call("", "GET", "/requests");

    expect(response.status).toBe(401);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe(
      "https://xkef.github.io",
    );
  });
});
