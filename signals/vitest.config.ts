import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { exportJWK, generateKeyPair } from "jose";
import { defineConfig } from "vitest/config";

// Tests run inside workerd with the bindings from wrangler.jsonc. A key pair
// made here stands in for Cloudflare Access and for GitHub's OIDC issuer: the
// Worker fetches the public half through the outbound handler below, and the
// tests sign tokens with the private half.
const TEAM_DOMAIN = "https://test.cloudflareaccess.com";
const KEY_URLS = [
  `${TEAM_DOMAIN}/cdn-cgi/access/certs`,
  "https://token.actions.githubusercontent.com/.well-known/jwks",
];

const { publicKey, privateKey } = await generateKeyPair("RS256", {
  extractable: true,
});
const publicJwk = {
  ...(await exportJWK(publicKey)),
  kid: "test",
  alg: "RS256",
};
const privateJwk = {
  ...(await exportJWK(privateKey)),
  kid: "test",
  alg: "RS256",
};

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
          ACCESS_AUD: "test-aud",
          OWNER_EMAIL: "Owner@Example.com",
          TEST_ACCESS_KEY: JSON.stringify(privateJwk),
        },
        outboundService: (request: Request) =>
          KEY_URLS.includes(request.url)
            ? Response.json({ keys: [publicJwk] })
            : new Response(null, { status: 404 }),
      },
    }),
  ],
});
