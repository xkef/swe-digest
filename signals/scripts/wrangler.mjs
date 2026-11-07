// Runs wrangler with the vars that differ per deployment, read from
// config.yaml at the repository root, so that wrangler.jsonc holds none.
// Workers Builds runs it through `npm run deploy`.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { parse } from "yaml";

const config = parse(
  readFileSync(new URL("../../config.yaml", import.meta.url), "utf8"),
);
const vars = {
  SITE_URL: config.site.url,
  REPOSITORY: config.repository,
  ACCESS_TEAM_DOMAIN: config.signals.access_team_domain ?? "",
  ACCESS_AUD: config.signals.access_aud ?? "",
};
const flags = Object.entries(vars).flatMap(([name, value]) => [
  "--var",
  `${name}:${value}`,
]);

const { status } = spawnSync(
  "npx",
  ["wrangler", ...process.argv.slice(2), ...flags],
  { stdio: "inherit" },
);
process.exit(status ?? 1);
