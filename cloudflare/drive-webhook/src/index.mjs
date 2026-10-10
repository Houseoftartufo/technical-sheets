import { DurableObject } from "cloudflare:workers";

const REPOSITORY = "Houseoftartufo/technical-sheets";
const WORKFLOW = "sync-drive.yml";
const MAIN_REF = "main";
const CHANGE_STATES = new Set(["add", "update", "remove", "trash", "untrash", "change"]);

async function equalSecret(actual, expected) {
  if (typeof actual !== "string" || typeof expected !== "string" || expected.length === 0) return false;
  actual = actual.trim();
  expected = expected.trim();
  if (actual.length === 0 || expected.length === 0) return false;
  const encoder = new TextEncoder();
  const [actualHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(actual)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  return crypto.subtle.timingSafeEqual(actualHash, expectedHash);
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
    if (url.pathname === "/watch-state") {
      if (!env.GITHUB_DISPATCH_TOKEN) return response(503, "watch state is not configured");
      if (!(await equalSecret(request.headers.get("X-Drive-Watch-Secret"), env.GITHUB_DISPATCH_TOKEN))) {
        return response(403, "forbidden");
      }
      if (!env.DISPATCHER) return response(503, "state storage is not configured");
      const stateStore = env.DISPATCHER.getByName("drive-change-batcher");
      if (request.method === "GET") {
        return Response.json(await stateStore.getWatchState(), {
          headers: { "Cache-Control": "no-store" },
        });
      }
      if (request.method !== "PUT") return response(405, "method not allowed");
      const body = await request.text();
      if (body.length > 2048) return response(413, "state too large");
      let state;
      try {
        state = JSON.parse(body);
      } catch {
        return response(400, "invalid state");
      }
      if (!state || typeof state !== "object" || Array.isArray(state) ||
          !["id", "resource_id", "drive_id", "expiration_ms"].every((key) => typeof state[key] === "string")) {
        return response(400, "invalid state");
      }
      await stateStore.setWatchState(state);
      return response(200, "saved");
    }
    if (url.pathname !== "/drive") return response(404, "not found");
    if (request.method !== "POST") return response(405, "method not allowed");
    if (!env.DRIVE_WEBHOOK_TOKEN) return response(503, "webhook is not configured");
    if (!(await equalSecret(request.headers.get("X-Goog-Channel-Token"), env.DRIVE_WEBHOOK_TOKEN))) {
      return response(403, "forbidden");
    }

    const state = request.headers.get("X-Goog-Resource-State");
    if (state === "sync" || !CHANGE_STATES.has(state)) return response(204);
    if (!env.DISPATCHER) return response(503, "dispatch service is not configured");
    try {
      await env.DISPATCHER.getByName("drive-change-batcher").schedule();
      return response(202, "accepted");
    } catch {
      return response(503, "dispatch unavailable");
    }
  },
};

export class DriveDispatchDebouncer extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.ctx.storage.sql.exec(`
      CREATE TABLE IF NOT EXISTS dispatch_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        revision INTEGER NOT NULL DEFAULT 0,
        attempts INTEGER NOT NULL DEFAULT 0
      )
    `);
    this.ctx.storage.sql.exec("INSERT OR IGNORE INTO dispatch_state (id) VALUES (1)");
  }

  async schedule() {
    this.ctx.storage.sql.exec("UPDATE dispatch_state SET revision = revision + 1 WHERE id = 1");
    await this.ctx.storage.setAlarm(Date.now() + 20_000);
  }

  async getWatchState() {
    return (await this.ctx.storage.get("drive-watch-state")) ?? null;
  }

  async setWatchState(state) {
    await this.ctx.storage.put("drive-watch-state", state);
  }

  async alarm() {
    const dispatchedRevision = this.ctx.storage.sql.exec(
      "SELECT revision FROM dispatch_state WHERE id = 1",
    ).one().revision;
    const attempt = this.ctx.storage.sql.exec(
      "SELECT attempts FROM dispatch_state WHERE id = 1",
    ).one().attempts;

    try {
      const upstream = await fetch(
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
      if (!upstream.ok) {
        console.error(JSON.stringify({ event: "github_dispatch_failed", status: upstream.status, attempt: attempt + 1 }));
        throw new Error("GitHub workflow dispatch failed");
      }

      const cleared = this.ctx.storage.sql.exec(
        "UPDATE dispatch_state SET revision = 0, attempts = 0 WHERE id = 1 AND revision = ?",
        dispatchedRevision,
      ).rowsWritten;
      if (cleared === 0) await this.ctx.storage.setAlarm(Date.now() + 20_000);
    } catch (error) {
      if (error instanceof TypeError) {
        console.error(JSON.stringify({ event: "github_dispatch_network_error", attempt: attempt + 1 }));
      }
      const nextAttempt = Math.min(attempt + 1, 8);
      this.ctx.storage.sql.exec("UPDATE dispatch_state SET attempts = ? WHERE id = 1", nextAttempt);
      await this.ctx.storage.setAlarm(Date.now() + Math.min(60_000 * 2 ** (nextAttempt - 1), 3_600_000));
    }
  }
}
