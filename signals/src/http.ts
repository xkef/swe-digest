import { limits, site } from "./config";

export const Status = {
  Created: 201,
  NoContent: 204,
  SeeOther: 303,
  BadRequest: 400,
  Unauthorized: 401,
  Forbidden: 403,
  NotFound: 404,
  MethodNotAllowed: 405,
  TooManyRequests: 429,
  ServerError: 500,
  Unavailable: 503,
} as const;

export type Status = (typeof Status)[keyof typeof Status];

// A handler throws this to answer with an empty status response. A reason
// marks a rejection worth a log line.
export class HttpError extends Error {
  constructor(readonly status: Status, readonly reason?: string) {
    super(reason ?? `HTTP ${status}`);
  }
}

export function fail(status: Status, reason?: string): never {
  throw new HttpError(status, reason);
}

export function empty(status: Status): Response {
  return new Response(null, { status });
}

// Returns undefined for an oversized or malformed body, which every parser
// then rejects.
export async function readJson(request: Request): Promise<unknown> {
  const text = await request.text();
  if (text.length > limits.body) {
    return undefined;
  }
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

export function bearer(request: Request): string | null {
  const [scheme, token] = request.headers.get("Authorization")?.split(" ")
    ?? [];
  return scheme === "Bearer" && token ? token : null;
}

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": site.origin,
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
  "Access-Control-Max-Age": "86400",
  Vary: "Origin",
};

export function withCors(response: Response): Response {
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(CORS_HEADERS)) {
    headers.set(name, value);
  }
  return new Response(response.body, { status: response.status, headers });
}
