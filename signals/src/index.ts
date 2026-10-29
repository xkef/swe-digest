import { accessEmail } from "./access";
import { type Reader, ReaderAgent, type Role } from "./agent";
import { log } from "./log";

export { ReaderAgent };

const AGENT_NAME = "digest";
const SITE_ORIGIN = "https://xkef.github.io";
const SITE_URL = `${SITE_ORIGIN}/swe-digest/`;
const TOKEN_FRAGMENT = "signals-token";
const MAX_LABEL = 40;

const NO_CONTENT = 204;
const SEE_OTHER = 303;
const UNAUTHORIZED = 401;
const FORBIDDEN = 403;
const NOT_FOUND = 404;
const METHOD_NOT_ALLOWED = 405;
const SERVER_ERROR = 500;
const UNAVAILABLE = 503;

export default {
  async fetch(request, env): Promise<Response> {
    const { pathname } = new URL(request.url);
    try {
      switch (pathname) {
        case "/health":
          return await health(env);
        case "/enroll":
          return await enroll(request, env);
        case "/me":
          return await me(request, env);
        default:
          return new Response(null, { status: NOT_FOUND });
      }
    } catch (error) {
      log("error", {
        path: pathname,
        message: error instanceof Error ? error.stack : String(error),
      });
      return new Response(null, { status: SERVER_ERROR });
    }
  },
} satisfies ExportedHandler<Env>;

// Answers only after a round trip to the agent, so a 200 means the Durable
// Object started and its schema is current.
async function health(env: Env): Promise<Response> {
  return Response.json({ ok: true, schema: await agent(env).schemaVersion() });
}

// Cloudflare Access guards this path. The signed-in reader gets a new device
// token and lands back on the site with it in the URL fragment, which
// browsers never send to a server.
async function enroll(request: Request, env: Env): Promise<Response> {
  if (request.method !== "GET") {
    return new Response(null, { status: METHOD_NOT_ALLOWED });
  }
  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD || !env.OWNER_EMAIL) {
    log("enroll_rejected", { reason: "not_configured" });
    return new Response("Enrollment is not configured.", {
      status: UNAVAILABLE,
    });
  }

  const email = await accessEmail(request, env);
  if (!email) {
    log("enroll_rejected", { reason: "access_token" });
    return new Response(null, { status: FORBIDDEN });
  }

  const role: Role = email === env.OWNER_EMAIL.toLowerCase()
    ? "owner"
    : "friend";
  const label = deviceLabel(new URL(request.url).searchParams.get("device"));
  const token = await agent(env).enroll(email, role, label);

  return new Response(null, {
    status: SEE_OTHER,
    headers: {
      Location: `${SITE_URL}#${TOKEN_FRAGMENT}=${token}`,
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
    },
  });
}

// Tells an enrolled browser who it is. The overlay calls it to decide what
// to show.
async function me(request: Request, env: Env): Promise<Response> {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: NO_CONTENT, headers: cors() });
  }
  if (request.method !== "GET") {
    return new Response(null, { status: METHOD_NOT_ALLOWED, headers: cors() });
  }

  const reader = await authenticate(request, env);
  if (!reader) {
    return new Response(null, { status: UNAUTHORIZED, headers: cors() });
  }
  return Response.json(
    { device: reader.device, role: reader.role },
    { headers: cors() },
  );
}

async function authenticate(
  request: Request,
  env: Env,
): Promise<Reader | null> {
  const header = request.headers.get("Authorization") ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!token) {
    return null;
  }

  const reader = await agent(env).authenticate(token);
  if (!reader) {
    log("auth_rejected", { reason: "token" });
  }
  return reader;
}

function agent(env: Env) {
  return env.READERS.get(env.READERS.idFromName(AGENT_NAME));
}

function deviceLabel(raw: string | null): string {
  const label = (raw ?? "").replace(/[^\p{L}\p{N} ._-]/gu, "").trim();
  return label.slice(0, MAX_LABEL) || "unnamed device";
}

function cors(): HeadersInit {
  return {
    "Access-Control-Allow-Origin": SITE_ORIGIN,
    "Access-Control-Allow-Headers": "Authorization",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}
