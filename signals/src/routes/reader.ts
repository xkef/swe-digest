// The routes an enrolled browser calls through the overlay.
import { agentOf } from "../agent";
import { empty, fail, readJson, Status } from "../http";
import * as parse from "../parse";
import type { ReaderContext } from "../router";

export async function me({ reader }: ReaderContext): Promise<Response> {
  return Response.json({ device: reader.device, role: reader.role });
}

// GET /feedback?day=2026-10-30 returns the reader's feedback on that day's
// stories, so a page draws its controls in one request.
export async function listFeedback(
  { request, env, reader }: ReaderContext,
): Promise<Response> {
  const day = parse.day(new URL(request.url).searchParams.get("day"))
    ?? fail(Status.BadRequest);
  return Response.json(await agentOf(env).feedbackFor(reader.email, day));
}

// Only the owner writes notes. A friend's feedback must leave the note empty.
export async function saveFeedback(
  { request, env, reader, params }: ReaderContext,
): Promise<Response> {
  const story = `${params.day}/${params.slug}`;
  const feedback = parse.feedback(story, await readJson(request))
    ?? fail(Status.BadRequest);
  if (feedback.note && reader.role !== "owner") {
    fail(Status.Forbidden, "friend_note");
  }

  await agentOf(env).saveFeedback(reader.email, feedback);
  return empty(Status.NoContent);
}

export async function listRequests(
  { env, reader }: ReaderContext,
): Promise<Response> {
  return Response.json(await agentOf(env).listRequests(reader));
}

export async function addRequest(
  { request, env, reader }: ReaderContext,
): Promise<Response> {
  const { url, note } = parse.request(await readJson(request))
    ?? fail(Status.BadRequest);
  const added = await agentOf(env).addRequest(reader, url, note)
    ?? fail(Status.TooManyRequests);
  return Response.json(added, { status: Status.Created });
}

export async function decide(
  { request, env, reader, params }: ReaderContext,
): Promise<Response> {
  if (reader.role !== "owner") {
    fail(Status.Forbidden, "friend_decision");
  }

  const status = parse.decision(await readJson(request))
    ?? fail(Status.BadRequest);
  const changed = await agentOf(env).decide(params.id ?? "", status);
  return empty(changed ? Status.NoContent : Status.NotFound);
}
