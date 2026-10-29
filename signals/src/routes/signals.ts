// The routes the digest runs call with their GitHub OIDC token.
import { fail, readJson, Status } from "../http";
import * as parse from "../parse";
import type { Context } from "../router";
import { storeOf } from "../store";

export async function readSignals(
  { request, env }: Context,
): Promise<Response> {
  const days = parse.days(new URL(request.url).searchParams.get("days"))
    ?? fail(Status.BadRequest);
  return Response.json(await storeOf(env).signals(days));
}

export async function markUsed({ request, env }: Context): Promise<Response> {
  const ids = parse.requestIds(await readJson(request))
    ?? fail(Status.BadRequest);
  return Response.json({ marked: await storeOf(env).markUsed(ids) });
}
