import { createRemoteJWKSet, jwtVerify, type JWTVerifyGetKey } from "jose";

// Cloudflare Access signs a JWT for every request it lets through and sends
// it in this header. Access already blocks everyone else, and checking the
// token here as well means a misconfigured policy cannot let a request in.
const ASSERTION_HEADER = "Cf-Access-Jwt-Assertion";

const keySets = new Map<string, JWTVerifyGetKey>();

// Returns the signed-in email, or null when Access is not configured or the
// token is missing, expired, or not for this application.
export async function accessEmail(
  request: Request,
  env: Env,
): Promise<string | null> {
  const token = request.headers.get(ASSERTION_HEADER);
  if (!token || !env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
    return null;
  }

  try {
    const { payload } = await jwtVerify(token, keys(env.ACCESS_TEAM_DOMAIN), {
      issuer: env.ACCESS_TEAM_DOMAIN,
      audience: env.ACCESS_AUD,
      algorithms: ["RS256"],
    });
    return typeof payload.email === "string"
      ? payload.email.toLowerCase()
      : null;
  } catch {
    return null;
  }
}

// One key set per team domain, kept for the isolate's lifetime. jose
// refetches it when a token names a key it has not seen.
function keys(teamDomain: string): JWTVerifyGetKey {
  let set = keySets.get(teamDomain);
  if (!set) {
    set = createRemoteJWKSet(new URL("/cdn-cgi/access/certs", teamDomain));
    keySets.set(teamDomain, set);
  }
  return set;
}
