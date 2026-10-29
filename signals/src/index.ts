import { accessEmail } from "./access";
import { type Reader, ReaderAgent, type Role } from "./agent";
import { isDay, parseDecision, parseFeedback, parseRequest } from "./feedback";
import { log } from "./log";

export { ReaderAgent };

const AGENT_NAME = "digest";
const SITE_ORIGIN = "https://xkef.github.io";
const SITE_URL = `${SITE_ORIGIN}/swe-digest/`;
const TOKEN_FRAGMENT = "signals-token";
const MAX_LABEL = 40;
const MAX_BODY = 4096;
const BEARER = "Bearer ";

const CREATED = 201;
const NO_CONTENT = 204;
const SEE_OTHER = 303;
const BAD_REQUEST = 400;
const UNAUTHORIZED = 401;
const FORBIDDEN = 403;
const NOT_FOUND = 404;
const METHOD_NOT_ALLOWED = 405;
const TOO_MANY = 429;
const SERVER_ERROR = 500;
const UNAVAILABLE = 503;

export default {
  async fetch(request, env): Promise<Response> {
    const { pathname } = new URL(request.url);
    try {
      if (pathname === "/health") {
        return await health(env);
      }
      if (pathname === "/enroll") {
        return await enroll(request, env);
      }
      return withCors(await api(request, env, pathname));
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

// Every route an enrolled browser calls. Each needs a device token, and
// each answer carries CORS headers for the site.
async function api(
  request: Request,
  env: Env,
  pathname: string,
): Promise<Response> {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: NO_CONTENT });
  }

  const route = ROUTES.find((r) =>
    r.method === request.method && r.path.test(pathname)
  );
  if (!route) {
    const known = ROUTES.some((r) => r.path.test(pathname));
    return status(known ? METHOD_NOT_ALLOWED : NOT_FOUND);
  }

  const reader = await authenticate(request, env);
  if (!reader) {
    return status(UNAUTHORIZED);
  }

  const match = route.path.exec(pathname)?.slice(1) ?? [];
  return route.handle({ request, env, reader, params: match });
}

interface Call {
  request: Request;
  env: Env;
  reader: Reader;
  params: string[];
}

interface Route {
  method: string;
  path: RegExp;
  handle: (call: Call) => Promise<Response>;
}

const ROUTES: Route[] = [
  { method: "GET", path: /^\/me$/, handle: me },
  { method: "GET", path: /^\/feedback$/, handle: listFeedback },
  {
    method: "PUT",
    path: /^\/feedback\/(\d{4}-\d{2}-\d{2}\/[a-z0-9-]+)$/,
    handle: saveFeedback,
  },
  { method: "GET", path: /^\/requests$/, handle: listRequests },
  { method: "POST", path: /^\/requests$/, handle: addRequest },
  { method: "PUT", path: /^\/requests\/([0-9a-f-]{36})$/, handle: decide },
];

async function me({ reader }: Call): Promise<Response> {
  return Response.json({ device: reader.device, role: reader.role });
}

// GET /feedback?day=2026-10-30 returns the reader's feedback on that day's
// stories, so a digest page draws its controls in one request.
async function listFeedback({ request, env, reader }: Call) {
  const day = new URL(request.url).searchParams.get("day") ?? "";
  if (!isDay(day)) {
    return status(BAD_REQUEST);
  }
  return Response.json(await agent(env).feedbackFor(reader.email, day));
}

// Only the owner writes notes. A friend's feedback must leave the note empty.
async function saveFeedback({ request, env, reader, params }: Call) {
  const feedback = parseFeedback(params[0] ?? "", await jsonBody(request));
  if (!feedback) {
    return status(BAD_REQUEST);
  }
  if (feedback.note !== "" && reader.role !== "owner") {
    return status(FORBIDDEN);
  }

  await agent(env).saveFeedback(reader.email, feedback);
  return status(NO_CONTENT);
}

async function listRequests({ env, reader }: Call) {
  return Response.json(await agent(env).listRequests(reader));
}

async function addRequest({ request, env, reader }: Call) {
  const fields = parseRequest(await jsonBody(request));
  if (!fields) {
    return status(BAD_REQUEST);
  }

  const added = await agent(env).addRequest(reader, fields.url, fields.note);
  return added
    ? Response.json(added, { status: CREATED })
    : status(TOO_MANY);
}

async function decide({ request, env, reader, params }: Call) {
  if (reader.role !== "owner") {
    return status(FORBIDDEN);
  }

  const decision = parseDecision(await jsonBody(request));
  if (!decision) {
    return status(BAD_REQUEST);
  }

  const changed = await agent(env).decide(params[0] ?? "", decision);
  return status(changed ? NO_CONTENT : NOT_FOUND);
}

async function authenticate(
  request: Request,
  env: Env,
): Promise<Reader | null> {
  const header = request.headers.get("Authorization") ?? "";
  const token = header.startsWith(BEARER) ? header.slice(BEARER.length) : "";
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

// Returns null for a missing, oversized, or malformed body, which every
// parser then rejects.
async function jsonBody(request: Request): Promise<unknown> {
  const text = await request.text();
  if (text.length > MAX_BODY) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function status(code: number): Response {
  return new Response(null, { status: code });
}

function withCors(response: Response): Response {
  const headers = new Headers(response.headers);
  headers.set("Access-Control-Allow-Origin", SITE_ORIGIN);
  headers.set("Access-Control-Allow-Headers", "Authorization, Content-Type");
  headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS");
  headers.set("Access-Control-Max-Age", "86400");
  headers.set("Vary", "Origin");
  return new Response(response.body, { status: response.status, headers });
}
