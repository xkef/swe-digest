import { createRemoteJWKSet, jwtVerify } from "jose";

// GitHub Actions mints an OIDC token for any job with `id-token: write`. Its
// claims name the repository, branch, and workflow file, so pinning all
// three admits only the digest workflow on main, never a fork or a branch.
const ISSUER = "https://token.actions.githubusercontent.com";
const KEYS = createRemoteJWKSet(new URL(`${ISSUER}/.well-known/jwks`));
const REPOSITORY = "xkef/swe-digest";
const WORKFLOW_REF =
  `${REPOSITORY}/.github/workflows/digest.yml@refs/heads/main`;
const AUDIENCE = "swe-digest-signals";
const BEARER = "Bearer ";

export async function isDigestRun(request: Request): Promise<boolean> {
  const header = request.headers.get("Authorization") ?? "";
  if (!header.startsWith(BEARER)) {
    return false;
  }

  try {
    const { payload } = await jwtVerify(header.slice(BEARER.length), KEYS, {
      issuer: ISSUER,
      audience: AUDIENCE,
      algorithms: ["RS256"],
    });
    return payload.repository === REPOSITORY
      && payload.ref === "refs/heads/main"
      && payload.workflow_ref === WORKFLOW_REF;
  } catch {
    return false;
  }
}
