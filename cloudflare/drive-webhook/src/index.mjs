const REPOSITORY = "Houseoftartufo/technical-sheets";
const WORKFLOW = "sync-drive.yml";
const MAIN_REF = "main";
const CHANGE_STATES = new Set(["add", "update", "remove", "trash", "untrash", "change"]);

function equalSecret(actual, expected) {
  const left = new TextEncoder().encode(actual ?? "");
  const right = new TextEncoder().encode(expected ?? "");
  let difference = left.length ^ right.length;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    difference |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return difference === 0;
}

function response(status, body = "") {
  return new Response(body === "" ? null : body, {
    status,
    headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") return response(200, "ok");
    if (url.pathname !== "/drive") return response(404, "not found");
    if (request.method !== "POST") return response(405, "method not allowed");
    if (!env.DRIVE_WEBHOOK_TOKEN) return response(503, "webhook is not configured");
    if (!equalSecret(request.headers.get("X-Goog-Channel-Token"), env.DRIVE_WEBHOOK_TOKEN)) {
      return response(403, "forbidden");
    }

    const state = request.headers.get("X-Goog-Resource-State");
    if (state === "sync" || !CHANGE_STATES.has(state)) return response(204);
    if (!env.DISPATCHER) return response(503, "dispatch service is not configured");
    try {
      const objectId = env.DISPATCHER.idFromName("drive-change-batcher");
      const result = await env.DISPATCHER.get(objectId).fetch("https://dispatcher.internal/schedule", { method: "POST" });
      return result.ok ? response(202, "accepted") : response(503, "dispatch unavailable");
    } catch {
      return response(503, "dispatch unavailable");
    }
  },
};

export class DriveDispatchDebouncer {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    if (request.method !== "POST") return response(405, "method not allowed");
    const revision = (await this.ctx.storage.get("revision")) ?? 0;
    await this.ctx.storage.put("revision", revision + 1);
    await this.ctx.storage.setAlarm(Date.now() + 20_000);
    return response(202, "queued");
  }

  async alarm() {
    const dispatchedRevision = await this.ctx.storage.get("revision");
    const attempts = (await this.ctx.storage.get("attempts")) ?? 0;
    try {
      const fetcher = this.env.FETCH ?? fetch;
      const upstream = await fetcher(
        `https://api.github.com/repos/${REPOSITORY}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.env.GITHUB_DISPATCH_TOKEN}`,
            Accept: "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
          },
          body: JSON.stringify({ ref: MAIN_REF, inputs: { publish_to_production: "true" } }),
        },
      );
      if (!upstream.ok) throw new Error("GitHub dispatch failed");
      const latestRevision = await this.ctx.storage.get("revision");
      if (latestRevision === dispatchedRevision) {
        await this.ctx.storage.delete("revision");
        await this.ctx.storage.delete("attempts");
      } else {
        await this.ctx.storage.setAlarm(Date.now() + 20_000);
      }
    } catch {
      const nextAttempt = Math.min(attempts + 1, 8);
      await this.ctx.storage.put("attempts", nextAttempt);
      await this.ctx.storage.setAlarm(Date.now() + Math.min(60_000 * 2 ** (nextAttempt - 1), 3_600_000));
    }
  }
}
