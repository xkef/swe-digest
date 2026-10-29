import { ReaderAgent } from "./agent";
import { log } from "./log";

export { ReaderAgent };

const AGENT_NAME = "digest";

const NOT_FOUND = 404;
const SERVER_ERROR = 500;

export default {
  async fetch(request, env): Promise<Response> {
    const { pathname } = new URL(request.url);
    try {
      if (pathname === "/health") {
        return await health(env);
      }
      return new Response(null, { status: NOT_FOUND });
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
  const agent = env.READERS.get(env.READERS.idFromName(AGENT_NAME));
  return Response.json({ ok: true, schema: await agent.schemaVersion() });
}
