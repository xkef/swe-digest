import { reset } from "cloudflare:test";
import { afterEach, describe, expect, it } from "vitest";
import { call, deviceToken, FRIEND, OWNER, runToken } from "./helpers";

const STORY = "2026-10-30/a-story";

afterEach(async () => {
  await reset();
});

async function approvedRequest(): Promise<string> {
  const owner = await deviceToken(OWNER);
  const response = await call(owner, "POST", "/requests", {
    url: "https://example.com/post",
    note: "cover this",
  });
  return ((await response.json()) as { id: string }).id;
}

describe("GET /signals", () => {
  it("returns unused approved requests and feedback totals", async () => {
    const id = await approvedRequest();
    const owner = await deviceToken(OWNER);
    const friend = await deviceToken(FRIEND);
    await call(owner, "PUT", `/feedback/${STORY}`, {
      vote: "more",
      note: "more like this",
    });
    await call(friend, "PUT", `/feedback/${STORY}`, {
      vote: "more",
      follow: true,
    });

    const response = await call(await runToken(), "GET", "/signals?days=7");

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      requests: [{ id, url: "https://example.com/post", note: "cover this" }],
      feedback: [{
        story: STORY,
        more: 2,
        less: 0,
        knew: 0,
        follow: 1,
        notes: ["more like this"],
      }],
    });
  });

  it("leaves out pending requests", async () => {
    const friend = await deviceToken(FRIEND);
    await call(friend, "POST", "/requests", { url: "https://example.com/p" });

    const body = await (await call(await runToken(), "GET", "/signals"))
      .json() as { requests: unknown[] };

    expect(body.requests).toEqual([]);
  });

  it("admits only the digest workflow on main", async () => {
    const tokens = await Promise.all([
      runToken({ repository: "someone/swe-digest" }),
      runToken({ ref: "refs/heads/feature" }),
      runToken({
        workflow_ref:
          "xkef/swe-digest/.github/workflows/ci.yml@refs/heads/main",
      }),
      runToken({ audience: "other" }),
      deviceToken(OWNER),
    ]);

    for (const token of tokens) {
      expect((await call(token, "GET", "/signals")).status).toBe(401);
    }
  });

  it("rejects a window outside 1 to 31 days", async () => {
    const token = await runToken();

    for (const days of ["0", "32", "seven"]) {
      expect((await call(token, "GET", `/signals?days=${days}`)).status)
        .toBe(400);
    }
  });
});

describe("POST /signals/used", () => {
  it("hides a used request from later runs", async () => {
    const id = await approvedRequest();
    const token = await runToken();

    const marked = await call(token, "POST", "/signals/used", {
      requests: [id, id],
    });
    const body = await (await call(token, "GET", "/signals")).json() as {
      requests: unknown[];
    };

    expect(await marked.json()).toEqual({ marked: 1 });
    expect(body.requests).toEqual([]);
  });

  it("rejects malformed ids", async () => {
    const token = await runToken();

    for (
      const requests of [["nope"], "x", Array(101).fill(crypto.randomUUID())]
    ) {
      expect((await call(token, "POST", "/signals/used", { requests })).status)
        .toBe(400);
    }
  });
});

describe("the request list", () => {
  async function listed(token: string): Promise<string[]> {
    const requests = await (await call(token, "GET", "/requests")).json() as {
      id: string;
    }[];
    return requests.map((request) => request.id);
  }

  it("drops a request once a run covers it", async () => {
    const id = await approvedRequest();
    const owner = await deviceToken(OWNER);
    expect(await listed(owner)).toEqual([id]);

    await call(await runToken(), "POST", "/signals/used", { requests: [id] });

    expect(await listed(owner)).toEqual([]);
  });

  it("drops a rejected request for the owner and the friend", async () => {
    const friend = await deviceToken(FRIEND);
    const owner = await deviceToken(OWNER);
    const { id } = await (await call(friend, "POST", "/requests", {
      url: "https://example.com/p",
    })).json() as { id: string };
    expect(await listed(friend)).toEqual([id]);

    await call(owner, "PUT", `/requests/${id}`, { status: "rejected" });

    expect(await listed(owner)).toEqual([]);
    expect(await listed(friend)).toEqual([]);
  });
});
