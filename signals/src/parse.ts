// Every value a client sends passes through one of these before it reaches
// the agent, so the agent only stores well-formed values. Each returns null
// for anything it rejects.
import { enrollment, limits, signals } from "./config";
import type { Feedback, RequestStatus, Vote } from "./types";

// A story is the day and slug of its page, digests/<day>/<slug>/ on the site.
// slugify() in site.py sets no length limit, and published slugs already
// reach 220 characters, so the bound only stops absurd input.
const STORY = /^\d{4}-\d{2}-\d{2}\/[a-z0-9-]{1,400}$/;
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const REQUEST_ID = /^[0-9a-f-]{36}$/;
const LABEL_JUNK = /[^\p{L}\p{N} ._-]/gu;

type Fields = Record<string, unknown>;

export function feedback(story: string, body: unknown): Feedback | null {
  if (!STORY.test(story) || !isFields(body)) {
    return null;
  }

  const { vote = null, knew = false, follow = false, note = "" } = body;
  if (
    !isVote(vote) || typeof knew !== "boolean" || typeof follow !== "boolean"
    || !isNote(note)
  ) {
    return null;
  }
  return { story, vote, knew, follow, note: note.trim() };
}

export function request(body: unknown): { url: string; note: string } | null {
  if (!isFields(body)) {
    return null;
  }

  const { url, note = "" } = body;
  if (typeof url !== "string" || url.length > limits.url || !isNote(note)) {
    return null;
  }

  const parsed = URL.parse(url);
  const web = parsed?.protocol === "https:" || parsed?.protocol === "http:";
  return parsed && web ? { url: parsed.href, note: note.trim() } : null;
}

export function decision(body: unknown): RequestStatus | null {
  const status = isFields(body) ? body.status : undefined;
  return status === "approved" || status === "rejected" ? status : null;
}

export function day(value: string | null): string | null {
  return value !== null && DAY.test(value) ? value : null;
}

export function days(value: string | null): number | null {
  const parsed = Number(value ?? signals.defaultDays);
  const valid = Number.isInteger(parsed) && parsed >= 1
    && parsed <= signals.maxDays;
  return valid ? parsed : null;
}

export function requestIds(body: unknown): string[] | null {
  const ids = isFields(body) ? body.requests : undefined;
  const valid = Array.isArray(ids) && ids.length <= signals.maxUsed
    && ids.every((id) => typeof id === "string" && REQUEST_ID.test(id));
  return valid ? ids : null;
}

// Labels are for the owner's device list, so anything odd is dropped
// instead of rejected.
export function deviceLabel(value: string | null): string {
  const label = (value ?? "").replace(LABEL_JUNK, "").trim();
  return label.slice(0, enrollment.maxLabel) || "unnamed device";
}

function isFields(value: unknown): value is Fields {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isVote(value: unknown): value is Vote | null {
  return value === null || value === "more" || value === "less";
}

function isNote(value: unknown): value is string {
  return typeof value === "string" && value.length <= limits.note;
}
