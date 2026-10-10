import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { setupNetwork } from "@msw/cloudflare";
import { env } from "cloudflare:workers";
import { runDurableObjectAlarm, runInDurableObject } from "cloudflare:test";
import worker from "../src/index.mjs";

const network = setupNetwork();
const OIDC_ISSUER = "https://token.actions.githubusercontent.com";
const OIDC_AUDIENCE = "https://technical-sheets.houseoftartufo.com/drive-watch";
const OIDC_JWKS_URL = `${OIDC_ISSUER}/.well-known/jwks`;
const encoder = new TextEncoder();
let oidcKeyPair;
let oidcPublicJwk;

function base64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function signedOidcToken(claims = {}) {
  const now = Math.floor(Date.now() / 1000);
  const header = base64Url(encoder.encode(JSON.stringify({ alg: "RS256", kid: "github-test-key", typ: "JWT" })));
  const payload = base64Url(encoder.encode(JSON.stringify({
    iss: OIDC_ISSUER,
    aud: OIDC_AUDIENCE,
    sub: "repo:Houseoftartufo/technical-sheets:ref:refs/heads/main",
    repository: "Houseoftartufo/technical-sheets",
    repository_id: "1261335289",
    repository_owner_id: "275527893",
    ref: "refs/heads/main",
    workflow_ref: "Houseoftartufo/technical-sheets/.github/workflows/sync-drive.yml@refs/heads/main",
    event_name: "schedule",
    iat: now,
    nbf: now - 1,
    exp: now + 300,
    ...claims,
  })));
  const signingInput = `${header}.${payload}`;
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", oidcKeyPair.privateKey, encoder.encode(signingInput));
  return `${signingInput}.${base64Url(new Uint8Array(signature))}`;
}

function mockGithubOidcKeys() {
  network.use(http.get(OIDC_JWKS_URL, () => HttpResponse.json({ keys: [oidcPublicJwk] })));
}

function notification(state = "update", token = "fixture-drive-token") {
  return new Request("https://worker.example/drive", {
    method: "POST",
    headers: { "X-Goog-Channel-Token": token, "X-Goog-Resource-State": state },
  });
}

async function invoke(request) {
  return worker.fetch(request, env, { waitUntil() {} });
}

describe("Drive webhook on the Cloudflare Workers runtime", () => {
  beforeAll(async () => {
    network.enable();
    oidcKeyPair = await crypto.subtle.generateKey(
      { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
      true,
      ["sign", "verify"],
    );
    oidcPublicJwk = await crypto.subtle.exportKey("jwk", oidcKeyPair.publicKey);
    oidcPublicJwk.kid = "github-test-key";
    oidcPublicJwk.alg = "RS256";
    oidcPublicJwk.use = "sig";
  });
  afterEach(() => network.resetHandlers());
  afterAll(() => network.disable());

  it("serves a public health check without revealing configured values", async () => {
    const result = await invoke(new Request("https://worker.example/health"));
    expect(result.status).toBe(200);
    expect(await result.text()).toBe("ok");
  });

  it("protects persistent Drive watch state with a signed token from the expected GitHub workflow", async () => {
    const denied = await invoke(new Request("https://worker.example/watch-state"));
    expect(denied.status).toBe(403);

    mockGithubOidcKeys();
    const token = await signedOidcToken();
    const headers = { Authorization: `Bearer ${token}` };
    const saved = { id: "channel-1", resource_id: "resource-1", drive_id: "drive-1", expiration_ms: "1900000000000" };
    const put = await invoke(new Request("https://worker.example/watch-state", {
      method: "PUT", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(saved),
    }));
    expect(put.status).toBe(200);

    const get = await invoke(new Request("https://worker.example/watch-state", { headers }));
    expect(get.status).toBe(200);
    expect(await get.json()).toEqual(saved);
  });

  it("rejects a correctly signed GitHub token from another repository", async () => {
    mockGithubOidcKeys();
    const token = await signedOidcToken({ repository: "someone-else/technical-sheets" });
    const result = await invoke(new Request("https://worker.example/watch-state", {
      headers: { Authorization: `Bearer ${token}` },
    }));
    expect(result.status).toBe(403);
  });

  it("rejects tokens with the wrong audience or an invalid signature", async () => {
    mockGithubOidcKeys();
    const wrongAudience = await signedOidcToken({ aud: "https://example.invalid" });
    const wrongAudienceResponse = await invoke(new Request("https://worker.example/watch-state", {
      headers: { Authorization: `Bearer ${wrongAudience}` },
    }));
    expect(wrongAudienceResponse.status).toBe(403);

    const valid = await signedOidcToken();
    const [header, payload, signature] = valid.split(".");
    const corruptedSignature = `${signature[0] === "A" ? "B" : "A"}${signature.slice(1)}`;
    const invalidSignatureResponse = await invoke(new Request("https://worker.example/watch-state", {
      headers: { Authorization: `Bearer ${header}.${payload}.${corruptedSignature}` },
    }));
    expect(invalidSignatureResponse.status).toBe(403);
  });

  it("logs only a safe rejection category for an invalid OIDC signature", async () => {
    mockGithubOidcKeys();
    const token = await signedOidcToken();
    const [header, payload, signature] = token.split(".");
    const corruptedSignature = `${signature[0] === "A" ? "B" : "A"}${signature.slice(1)}`;
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    const result = await invoke(new Request("https://worker.example/watch-state", {
      headers: { Authorization: `Bearer ${header}.${payload}.${corruptedSignature}` },
    }));

    expect(result.status).toBe(403);
    expect(warn).toHaveBeenCalledWith(JSON.stringify({
      event: "github_oidc_rejected",
      reason: "signature_invalid",
    }));
    expect(JSON.stringify(warn.mock.calls)).not.toContain(token);
    warn.mockRestore();
  });

  it("rejects an invalid Google channel token and does not queue work", async () => {
    const result = await invoke(notification("update", "wrong-token"));
    expect(result.status).toBe(403);
  });

  it("ignores surrounding whitespace accidentally included in a configured token", async () => {
    const result = await worker.fetch(notification("sync"), {
      ...env,
      DRIVE_WEBHOOK_TOKEN: " fixture-drive-token\r\n",
    }, { waitUntil() {} });
    expect(result.status).toBe(204);
  });

  it("ignores Drive's initial sync and unknown notification states", async () => {
    expect((await invoke(notification("sync"))).status).toBe(204);
    expect((await invoke(notification("future-state"))).status).toBe(204);
  });

  it("queues recognized changes in the Durable Object", async () => {
    const stub = env.DISPATCHER.getByName("drive-change-batcher");
    const result = await invoke(notification("add"));
    expect(result.status).toBe(202);
    const revision = await runInDurableObject(stub, (instance) =>
      instance.ctx.storage.sql.exec("SELECT revision FROM dispatch_state WHERE id = 1").one().revision,
    );
    expect(revision).toBe(1);
  });

  it("coalesces a burst and dispatches only the fixed main workflow", async () => {
    const stub = env.DISPATCHER.getByName("drive-change-batcher");
    let dispatches = 0;
    network.use(
      http.post("https://api.github.com/repos/Houseoftartufo/technical-sheets/actions/workflows/sync-drive.yml/dispatches", async ({ request }) => {
        dispatches += 1;
        expect(request.headers.get("Authorization")).toBe("Bearer fixture-github-token");
        expect(await request.json()).toEqual({ ref: "main", inputs: { publish_to_production: "true" } });
        return new HttpResponse(null, { status: 204 });
      }),
    );

    expect((await invoke(notification("add"))).status).toBe(202);
    expect((await invoke(notification("update"))).status).toBe(202);
    expect((await invoke(notification("remove"))).status).toBe(202);
    await runDurableObjectAlarm(stub);
    expect(dispatches).toBe(1);
    const state = await runInDurableObject(stub, (instance) =>
      instance.ctx.storage.sql.exec("SELECT revision, attempts FROM dispatch_state WHERE id = 1").one(),
    );
    expect(state.revision).toBe(0);
    expect(state.attempts).toBe(0);
  });

  it("retries a failed GitHub dispatch and succeeds on the following alarm", async () => {
    const stub = env.DISPATCHER.getByName("drive-change-batcher");
    let dispatches = 0;
    network.use(
      http.post("https://api.github.com/repos/Houseoftartufo/technical-sheets/actions/workflows/sync-drive.yml/dispatches", () => {
        dispatches += 1;
        return dispatches === 1
          ? new HttpResponse("failure body is never logged", { status: 503 })
          : new HttpResponse(null, { status: 204 });
      }),
    );

    expect((await invoke(notification("update"))).status).toBe(202);
    await runDurableObjectAlarm(stub);
    const attempts = await runInDurableObject(stub, (instance) =>
      instance.ctx.storage.sql.exec("SELECT attempts FROM dispatch_state WHERE id = 1").one().attempts,
    );
    expect(attempts).toBe(1);
    await runDurableObjectAlarm(stub);
    expect(dispatches).toBe(2);
    const finalState = await runInDurableObject(stub, (instance) =>
      instance.ctx.storage.sql.exec("SELECT revision, attempts FROM dispatch_state WHERE id = 1").one(),
    );
    expect(finalState.revision).toBe(0);
    expect(finalState.attempts).toBe(0);
  });
});
