// What a reader may send. Every body is parsed here before it reaches the
// agent, so the agent only ever stores well-formed values.

// A story is the day and slug of its page, digests/<day>/<slug>/ on the site.
// slugify() in site.py sets no length limit, and published slugs already
// reach 220 characters, so the bound only stops absurd input.
const STORY = /^\d{4}-\d{2}-\d{2}\/[a-z0-9-]{1,400}$/;
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const MAX_NOTE = 500;
const MAX_URL = 2048;

export type Vote = "more" | "less";
export type RequestStatus = "pending" | "approved" | "rejected";

export interface Feedback {
  story: string;
  vote: Vote | null;
  knew: boolean;
  follow: boolean;
  note: string;
}

export interface StoryRequest {
  id: string;
  url: string;
  note: string;
  status: RequestStatus;
  from: string;
  createdAt: number;
}

export function isStory(value: string): boolean {
  return STORY.test(value);
}

export function isDay(value: string): boolean {
  return DAY.test(value);
}

export function parseFeedback(story: string, body: unknown): Feedback | null {
  if (!isStory(story) || !isObject(body)) {
    return null;
  }

  const { vote = null, knew = false, follow = false, note = "" } = body;
  const validVote = vote === null || vote === "more" || vote === "less";
  if (
    !validVote || typeof knew !== "boolean" || typeof follow !== "boolean"
    || typeof note !== "string" || note.length > MAX_NOTE
  ) {
    return null;
  }

  return { story, vote, knew, follow, note: note.trim() };
}

export function parseRequest(
  body: unknown,
): { url: string; note: string } | null {
  if (!isObject(body)) {
    return null;
  }

  const { url, note = "" } = body;
  if (typeof url !== "string" || url.length > MAX_URL) {
    return null;
  }
  if (typeof note !== "string" || note.length > MAX_NOTE) {
    return null;
  }

  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    return null;
  }

  return { url: parsed.href, note: note.trim() };
}

export function parseDecision(body: unknown): RequestStatus | null {
  if (!isObject(body)) {
    return null;
  }
  return body.status === "approved" || body.status === "rejected"
    ? body.status
    : null;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
