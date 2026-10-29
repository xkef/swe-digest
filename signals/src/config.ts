// Every fixed value the Worker depends on. Values that differ per deployment,
// such as the Access application, are vars in wrangler.jsonc instead.

const HOUR = 3_600_000;
export const DAY = 24 * HOUR;

export const site = {
  origin: "https://xkef.github.io",
  url: "https://xkef.github.io/swe-digest/",
} as const;

// Every request goes to this one Durable Object instance.
export const agentName = "digest";

export const enrollment = {
  // The redirect carries the token in this URL fragment, which browsers never
  // send to a server.
  fragment: "signals-token",
  tokenBytes: 32,
  // Enrolling past this many devices revokes the least recently seen one, so
  // a lost phone needs no manual cleanup.
  maxDevices: 5,
  maxLabel: 40,
  // last_seen_at is written at most this often, so reads stay reads.
  seenInterval: HOUR,
} as const;

export const limits = {
  body: 4096,
  note: 500,
  url: 2048,
  // A friend can have this many requests waiting for the owner at once.
  pending: 20,
  // The owner's request list shows decided requests for this long.
  decidedVisible: 30 * DAY,
} as const;

export const signals = {
  defaultDays: 7,
  maxDays: 31,
  maxUsed: 100,
} as const;

// Cloudflare Access signs every request it lets through and sends the token
// in this header.
export const access = {
  header: "Cf-Access-Jwt-Assertion",
} as const;

// The GitHub Actions OIDC token of the digest workflow on main. Pinning the
// repository, branch, and workflow file admits no fork, branch, or other
// workflow.
export const github = {
  issuer: "https://token.actions.githubusercontent.com",
  audience: "swe-digest-signals",
  repository: "xkef/swe-digest",
  ref: "refs/heads/main",
  workflowRef: "xkef/swe-digest/.github/workflows/digest.yml@refs/heads/main",
} as const;
