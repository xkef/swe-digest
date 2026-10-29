import { agentOf, ReaderAgent } from "./agent";
import { dispatch, open, reader, run } from "./router";
import { enroll } from "./routes/enroll";
import * as overlay from "./routes/reader";
import { markUsed, readSignals } from "./routes/signals";

export { ReaderAgent };

const routes = [
  // Answers only after a round trip to the agent, so a 200 means the Durable
  // Object started and its schema is current.
  open(
    "GET",
    "/health",
    async ({ env }) =>
      Response.json({ ok: true, schema: await agentOf(env).schemaVersion() }),
  ),
  open("GET", "/enroll", enroll),

  run("GET", "/signals", readSignals),
  run("POST", "/signals/used", markUsed),

  reader("GET", "/me", overlay.me),
  reader("GET", "/feedback", overlay.listFeedback),
  reader("PUT", "/feedback/:day/:slug", overlay.saveFeedback),
  reader("GET", "/requests", overlay.listRequests),
  reader("POST", "/requests", overlay.addRequest),
  reader("PUT", "/requests/:id", overlay.decide),
];

export default {
  fetch: (request, env) => dispatch(routes, request, env),
} satisfies ExportedHandler<Env>;
