import { createRemoteJWKSet, jwtVerify, type JWTVerifyGetKey } from "jose";
import { access } from "../config";

// One key set per team domain, kept for the isolate's lifetime. jose
// refetches it when a token names a key it has not seen.
const keySets = new Map<string, JWTVerifyGetKey>();

// Returns the email Access signed in, or null when Access is not configured
// or the token is missing, expired, or for another application. Access
// already blocks everyone else. Checking here as well means a misconfigured
// policy cannot let a request in.
export async function accessEmail(
  request: Request,
  env: Env,
): Promise<string | null> {
  const token = request.headers.get(access.header);
  const { ACCESS_TEAM_DOMAIN: issuer, ACCESS_AUD: audience } = env;
  if (!token || !issuer || !audience) {
    return null;
  }

  try {
    const { payload } = await jwtVerify(token, keys(issuer), {
      issuer,
      audience,
      algorithms: ["RS256"],
    });
    return typeof payload.email === "string"
      ? payload.email.toLowerCase()
      : null;
  } catch {
    return null;
  }
}

function keys(teamDomain: string): JWTVerifyGetKey {
  let set = keySets.get(teamDomain);
  if (!set) {
    set = createRemoteJWKSet(new URL("/cdn-cgi/access/certs", teamDomain));
    keySets.set(teamDomain, set);
  }
  return set;
}
