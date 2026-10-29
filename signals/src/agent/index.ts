import { DurableObject } from "cloudflare:workers";
import { agentName, DAY } from "../config";
import type {
  Feedback,
  Reader,
  RequestStatus,
  Role,
  Signals,
  StoryRequest,
} from "../types";
import { Devices } from "./devices";
import { FeedbackStore } from "./feedback";
import { RequestStore } from "./requests";
import { migrate, schemaVersion } from "./schema";

// The one Durable Object behind the Worker. It keeps every reader's state in
// its own SQLite and upgrades the schema before it serves a call. Its methods
// are the RPC surface the routes call.
export class ReaderAgent extends DurableObject<Env> {
  readonly #devices: Devices;
  readonly #feedback: FeedbackStore;
  readonly #requests: RequestStore;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => migrate(ctx.storage));
    this.#devices = new Devices(ctx.storage);
    this.#feedback = new FeedbackStore(ctx.storage.sql);
    this.#requests = new RequestStore(ctx.storage.sql);
  }

  schemaVersion(): number {
    return schemaVersion(this.ctx.storage.sql);
  }

  enroll(email: string, role: Role, label: string): Promise<string> {
    return this.#devices.enroll(email, role, label);
  }

  authenticate(token: string): Promise<Reader | null> {
    return this.#devices.authenticate(token);
  }

  feedbackFor(email: string, day: string): Feedback[] {
    return this.#feedback.forDay(email, day);
  }

  saveFeedback(email: string, feedback: Feedback): void {
    this.#feedback.save(email, feedback);
  }

  addRequest(reader: Reader, url: string, note: string): StoryRequest | null {
    return this.#requests.add(reader, url, note);
  }

  listRequests(reader: Reader): StoryRequest[] {
    return this.#requests.list(reader);
  }

  decide(id: string, status: RequestStatus): boolean {
    return this.#requests.decide(id, status);
  }

  signals(days: number): Signals {
    return {
      requests: this.#requests.unused(),
      feedback: this.#feedback.tally(Date.now() - days * DAY),
    };
  }

  markUsed(ids: string[]): number {
    return this.#requests.markUsed(ids);
  }
}

export function agentOf(env: Env): DurableObjectStub<ReaderAgent> {
  return env.READERS.getByName(agentName);
}
