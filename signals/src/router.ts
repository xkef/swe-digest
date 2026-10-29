import { isDigestRun } from "./auth/github";
import { bearer, empty, fail, HttpError, Status, withCors } from "./http";
import { log } from "./log";
import { storeOf } from "./store";
import type { Reader } from "./types";

type Method = "GET" | "POST" | "PUT";

export interface Context {
  request: Request;
  env: Env;
  params: Record<string, string | undefined>;
}

export interface ReaderContext extends Context {
  reader: Reader;
}

type Handler<C extends Context = Context> = (context: C) => Promise<Response>;

interface Route {
  method: Method;
  pattern: URLPattern;
  handle: Handler;
  // Routes the site's browsers call answer with CORS headers.
  browser: boolean;
}

// The three kinds of route, by who may call them. Each wraps its handler in
// the check for that caller, so a handler never sees an unchecked request.
export function open(method: Method, pathname: string, handle: Handler): Route {
  return {
    method,
    pattern: new URLPattern({ pathname }),
    handle,
    browser: false,
  };
}

// Only the digest workflow on main, by its GitHub OIDC token.
export function run(method: Method, pathname: string, handle: Handler): Route {
  return open(method, pathname, async (context) => {
    const token = bearer(context.request);
    if (!token || !await isDigestRun(token)) {
      fail(Status.Unauthorized, "oidc_token");
    }
    return handle(context);
  });
}

// Only an enrolled browser, by its device token.
export function reader(
  method: Method,
  pathname: string,
  handle: Handler<ReaderContext>,
): Route {
  const guarded: Handler = async (context) =>
    handle({ ...context, reader: await authenticate(context) });
  return { ...open(method, pathname, guarded), browser: true };
}

export async function dispatch(
  routes: Route[],
  request: Request,
  env: Env,
): Promise<Response> {
  const url = new URL(request.url);
  const matches = routes.filter((route) => route.pattern.test(url));
  const browser = matches.some((route) => route.browser);
  const finish = browser ? withCors : (response: Response) => response;

  try {
    if (matches.length === 0) {
      return empty(Status.NotFound);
    }
    if (browser && request.method === "OPTIONS") {
      return finish(empty(Status.NoContent));
    }

    const route = matches.find((r) => r.method === request.method)
      ?? fail(Status.MethodNotAllowed);
    const params = route.pattern.exec(url)?.pathname.groups ?? {};
    return finish(await route.handle({ request, env, params }));
  } catch (error) {
    return finish(failure(error, url.pathname));
  }
}

async function authenticate({ request, env }: Context): Promise<Reader> {
  const token = bearer(request) ?? fail(Status.Unauthorized);
  return await storeOf(env).authenticate(token)
    ?? fail(Status.Unauthorized, "device_token");
}

function failure(error: unknown, path: string): Response {
  if (error instanceof HttpError) {
    if (error.reason) {
      log("rejected", { path, status: error.status, reason: error.reason });
    }
    return empty(error.status);
  }

  const message = error instanceof Error ? error.stack : String(error);
  log("error", { path, message });
  return empty(Status.ServerError);
}
