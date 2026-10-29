import { accessEmail } from "../auth/access";
import { enrollment, site } from "../config";
import { fail, Status } from "../http";
import * as parse from "../parse";
import type { Context } from "../router";
import { storeOf } from "../store";
import type { Role } from "../types";

// Cloudflare Access guards this path. The signed-in reader gets a new device
// token and lands back on the site with it in the URL fragment.
export async function enroll({ request, env }: Context): Promise<Response> {
  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD || !env.OWNER_EMAIL) {
    fail(Status.Unavailable, "not_configured");
  }

  const email = await accessEmail(request, env)
    ?? fail(Status.Forbidden, "access_token");
  const role: Role = email === env.OWNER_EMAIL.toLowerCase()
    ? "owner"
    : "friend";
  const label = parse.deviceLabel(
    new URL(request.url).searchParams.get("device"),
  );
  const token = await storeOf(env).enroll(email, role, label);

  return new Response(null, {
    status: Status.SeeOther,
    headers: {
      Location: `${site.url}#${enrollment.fragment}=${token}`,
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
    },
  });
}
