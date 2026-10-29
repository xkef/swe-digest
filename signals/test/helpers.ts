import { env, exports } from "cloudflare:workers";
import { importJWK, type JWK, SignJWT } from "jose";

const TEAM_DOMAIN = "https://test.cloudflareaccess.com";
const testEnv = env as Env & { TEST_ACCESS_KEY: string };

export const OWNER = "owner@example.com";
export const FRIEND = "friend@example.com";

export interface TokenOptions {
  email?: string;
  audience?: string;
  issuer?: string;
  expiresIn?: string;
  key?: CryptoKey;
}

// Signs an Access token with the key pair from vitest.config.ts.
export async function accessToken(options: TokenOptions = {}): Promise<string> {
  const key = options.key
    ?? await importJWK(JSON.parse(testEnv.TEST_ACCESS_KEY) as JWK, "RS256");
  return new SignJWT({ email: options.email ?? FRIEND })
    .setProtectedHeader({ alg: "RS256", kid: "test" })
    .setIssuer(options.issuer ?? TEAM_DOMAIN)
    .setAudience(options.audience ?? "test-aud")
    .setIssuedAt()
    .setExpirationTime(options.expiresIn ?? "5m")
    .sign(key);
}

export async function enroll(
  options: TokenOptions = {},
  query = "",
): Promise<Response> {
  return exports.default.fetch(`https://signals.test/enroll${query}`, {
    headers: { "Cf-Access-Jwt-Assertion": await accessToken(options) },
    redirect: "manual",
  });
}

export function tokenFrom(response: Response): string {
  const location = response.headers.get("Location") ?? "";
  return new URL(location).hash.replace("#signals-token=", "");
}

export async function deviceToken(email = FRIEND): Promise<string> {
  return tokenFrom(await enroll({ email }));
}

export function call(
  token: string,
  method: string,
  path: string,
  body?: unknown,
): Promise<Response> {
  return exports.default.fetch(`https://signals.test${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export interface RunClaims {
  repository?: string;
  ref?: string;
  workflow_ref?: string;
  audience?: string;
}

// Signs a GitHub Actions OIDC token for the digest workflow on main, unless
// a claim is overridden.
export async function runToken(claims: RunClaims = {}): Promise<string> {
  const key = await importJWK(
    JSON.parse(testEnv.TEST_ACCESS_KEY) as JWK,
    "RS256",
  );
  const repository = claims.repository ?? "xkef/swe-digest";
  return new SignJWT({
    repository,
    ref: claims.ref ?? "refs/heads/main",
    workflow_ref: claims.workflow_ref
      ?? `${repository}/.github/workflows/digest.yml@refs/heads/main`,
  })
    .setProtectedHeader({ alg: "RS256", kid: "test" })
    .setIssuer("https://token.actions.githubusercontent.com")
    .setAudience(claims.audience ?? "swe-digest-signals")
    .setIssuedAt()
    .setExpirationTime("5m")
    .sign(key);
}
