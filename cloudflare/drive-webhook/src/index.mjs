import { DurableObject } from "cloudflare:workers";

const REPOSITORY = "Houseoftartufo/technical-sheets";
const WORKFLOW = "sync-drive.yml";
const MAIN_REF = "main";
const CHANGE_STATES = new Set(["add", "update", "remove", "trash", "untrash", "change"]);
const GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com";
const GITHUB_OIDC_JWKS_URL = `${GITHUB_OIDC_ISSUER}/.well-known/jwks`;
const GITHUB_OIDC_AUDIENCE = "https://technical-sheets.houseoftartufo.com/drive-watch";
const GITHUB_REPOSITORY_ID = "1261335289";
const GITHUB_OWNER_ID = "275527893";
const GITHUB_WORKFLOW_REF = "Houseoftartufo/technical-sheets/.github/workflows/sync-drive.yml@refs/heads/main";
const encoder = new TextEncoder();

let githubJwks;
let githubJwksExpiresAt = 0;

async function equalSecret(actual, expected) {
  if (typeof actual !== "string" || typeof expected !== "string" || expected.length === 0) return false;
  actual = actual.trim();
  expected = expected.trim();
  if (actual.length === 0 || expected.length === 0) return false;
  const actualBytes = encoder.encode(actual);
  const expectedBytes = encoder.encode(expected);
  if (actualBytes.byteLength !== expectedBytes.byteLength) {
    return !crypto.subtle.timingSafeEqual(actualBytes, actualBytes);
  }
  return crypto.subtle.timingSafeEqual(actualBytes, expectedBytes);
}

function decodeBase64Url(value) {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]+$/.test(value)) return null;
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  try {
    const binary = atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "="));
    return Uint8Array.from(binary, (character) => character.charCodeAt(0));
  } catch {
    return null;
  }
}

function decodeJsonSegment(value) {
  const bytes = decodeBase64Url(value);
  if (!bytes) return null;
  try {
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return null;
  }
}

async function getGithubJwks() {
  if (githubJwks && Date.now() < githubJwksExpiresAt) return githubJwks;
  const response = await fetch(GITHUB_OIDC_JWKS_URL, {
    headers: { Accept: "application/json" },
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!response.ok) throw new Error("GitHub OIDC signing keys are unavailable");
  const body = await response.json();
  if (!Array.isArray(body.keys)) throw new Error("GitHub OIDC signing keys are invalid");
  githubJwks = body.keys;
  githubJwksExpiresAt = Date.now() + 5 * 60 * 1000;
  return githubJwks;
}

async function isTrustedGithubActionsToken(token) {
  if (typeof token !== "string" || token.length > 8192) return { trusted: false, reason: "token_invalid" };
  const parts = token.split(".");
  if (parts.length !== 3) return { trusted: false, reason: "token_invalid" };
  const header = decodeJsonSegment(parts[0]);
  const claims = decodeJsonSegment(parts[1]);
  const signature = decodeBase64Url(parts[2]);
  if (!header || !claims || !signature || header.alg !== "RS256" || typeof header.kid !== "string") {
    return { trusted: false, reason: "token_invalid" };
  }

  const now = Math.floor(Date.now() / 1000);
  const audiences = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  const claimChecks = [
    [claims.iss === GITHUB_OIDC_ISSUER, "issuer_mismatch"],
    [audiences.includes(GITHUB_OIDC_AUDIENCE), "audience_mismatch"],
    [claims.repository === REPOSITORY, "repository_mismatch"],
    [String(claims.repository_id) === GITHUB_REPOSITORY_ID, "repository_id_mismatch"],
    [String(claims.repository_owner_id) === GITHUB_OWNER_ID, "repository_owner_id_mismatch"],
    [claims.ref === "refs/heads/main", "ref_mismatch"],
    [claims.workflow_ref === GITHUB_WORKFLOW_REF, "workflow_mismatch"],
    [["push", "schedule", "workflow_dispatch"].includes(claims.event_name), "event_not_allowed"],
    [Number.isInteger(claims.iat) && Number.isInteger(claims.nbf) && Number.isInteger(claims.exp), "timestamps_invalid"],
    [Number.isInteger(claims.iat) && claims.iat <= now + 30, "token_issued_in_future"],
    [Number.isInteger(claims.nbf) && claims.nbf <= now + 30, "token_not_yet_valid"],
    [Number.isInteger(claims.exp) && claims.exp > now, "token_expired"],
    [Number.isInteger(claims.exp) && Number.isInteger(claims.iat) && claims.exp > claims.iat, "token_lifetime_invalid"],
    [Number.isInteger(claims.exp) && Number.isInteger(claims.iat) && claims.exp - claims.iat <= 600, "token_lifetime_too_long"],
  ];
  const failedClaim = claimChecks.find(([passed]) => !passed);
  if (failedClaim) return { trusted: false, reason: failedClaim[1] };

  const keys = await getGithubJwks();
  let jwk = keys.find((candidate) => candidate.kid === header.kid && candidate.kty === "RSA");
  if (!jwk) {
    githubJwksExpiresAt = 0;
    jwk = (await getGithubJwks()).find((candidate) => candidate.kid === header.kid && candidate.kty === "RSA");
  }
  if (!jwk) return { trusted: false, reason: "signing_key_not_found" };

  const key = await crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const signatureValid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5",
    key,
    signature,
    encoder.encode(`${parts[0]}.${parts[1]}`),
  );
  return signatureValid
    ? { trusted: true, reason: null }
    : { trusted: false, reason: "signature_invalid" };
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
    if (url.pathname === "/dispatch-status") {
      if (request.method !== "GET") return response(405, "method not allowed");
      if (!(await equalSecret(request.headers.get("X-Goog-Channel-Token"), env.DRIVE_WEBHOOK_TOKEN))) {
        return response(403, "forbidden");
      }
      if (!env.DISPATCHER) return response(503, "dispatch service is not configured");
      const status = await env.DISPATCHER.getByName("drive-change-batcher").getDispatchStatus();
      return Response.json(status, { headers: { "Cache-Control": "no-store" } });
    }
    if (url.pathname === "/watch-state") {
      const bearerToken = request.headers.get("Authorization")?.match(/^Bearer\s+(.+)$/i)?.[1];
      let authorized;
      let rejectionReason;
      try {
        const authentication = await isTrustedGithubActionsToken(bearerToken);
        authorized = authentication.trusted;
        rejectionReason = authentication.reason;
        if (!authorized) {
          console.warn(JSON.stringify({ event: "github_oidc_rejected", reason: rejectionReason }));
        }
      } catch {
        return response(503, "GitHub authentication is temporarily unavailable");
      }
      if (!authorized) {
        return response(403, `forbidden:${rejectionReason}`);
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
      await env.DISPATCHER.getByName("drive-change-batcher").schedule(
        request.headers.get("X-Goog-Channel-ID"),
      );
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

  async schedule(channelId = null) {
    this.ctx.storage.sql.exec("UPDATE dispatch_state SET revision = revision + 1 WHERE id = 1");
    const revision = this.ctx.storage.sql.exec(
      "SELECT revision FROM dispatch_state WHERE id = 1",
    ).one().revision;
    await this.ctx.storage.put("dispatch-status", {
      channel_id: channelId,
      revision,
      status: "pending",
      http_status: null,
      updated_at: Date.now(),
    });
    await this.ctx.storage.setAlarm(Date.now() + 20_000);
  }

  async getDispatchStatus() {
    return (await this.ctx.storage.get("dispatch-status")) ?? null;
  }

  async setDispatchStatus(revision, updates) {
    const current = await this.getDispatchStatus();
    if (!current || current.revision !== revision) return;
    await this.ctx.storage.put("dispatch-status", { ...current, ...updates, updated_at: Date.now() });
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

    let failureStatus = null;
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
        failureStatus = { status: "http_error", http_status: upstream.status };
        await this.setDispatchStatus(dispatchedRevision, failureStatus);
        console.error(JSON.stringify({ event: "github_dispatch_failed", status: upstream.status, attempt: attempt + 1 }));
        throw new Error("GitHub workflow dispatch failed");
      }

      const cleared = this.ctx.storage.sql.exec(
        "UPDATE dispatch_state SET revision = 0, attempts = 0 WHERE id = 1 AND revision = ?",
        dispatchedRevision,
      ).rowsWritten;
      if (cleared === 0) {
        await this.ctx.storage.setAlarm(Date.now() + 20_000);
      } else {
        await this.setDispatchStatus(dispatchedRevision, { status: "sent", http_status: upstream.status });
      }
    } catch (error) {
      if (!failureStatus) {
        failureStatus = { status: "network_error", http_status: null };
        await this.setDispatchStatus(dispatchedRevision, failureStatus);
      }
      if (error instanceof TypeError) {
        console.error(JSON.stringify({ event: "github_dispatch_network_error", attempt: attempt + 1 }));
      }
      const nextAttempt = Math.min(attempt + 1, 8);
      this.ctx.storage.sql.exec("UPDATE dispatch_state SET attempts = ? WHERE id = 1", nextAttempt);
      await this.ctx.storage.setAlarm(Date.now() + Math.min(60_000 * 2 ** (nextAttempt - 1), 3_600_000));
    }
  }
}
