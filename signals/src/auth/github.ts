import { createRemoteJWKSet, jwtVerify } from "jose";
import { github } from "../config";

const keys = createRemoteJWKSet(new URL("/.well-known/jwks", github.issuer));

// GitHub Actions mints this token for a job with `id-token: write`. Its
// claims name the repository, branch, and workflow file.
export async function isDigestRun(token: string): Promise<boolean> {
  try {
    const { payload } = await jwtVerify(token, keys, {
      issuer: github.issuer,
      audience: github.audience,
      algorithms: ["RS256"],
    });
    return payload.repository === github.repository
      && payload.ref === github.ref
      && payload.workflow_ref === github.workflowRef;
  } catch {
    return false;
  }
}
