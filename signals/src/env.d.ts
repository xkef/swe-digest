// The vars scripts/wrangler.mjs passes from config.yaml. wrangler types
// cannot see them, because wrangler.jsonc holds none. Handlers take the global
// Env, and `env` from cloudflare:workers is a Cloudflare.Env, so both get them.
interface DeploymentVars {
  SITE_URL: string;
  REPOSITORY: string;
  ACCESS_TEAM_DOMAIN: string;
  ACCESS_AUD: string;
}

interface Env extends DeploymentVars {}

declare namespace Cloudflare {
  interface Env extends DeploymentVars {}
}
