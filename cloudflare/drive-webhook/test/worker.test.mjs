import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupNetwork } from "@msw/cloudflare";
import { env } from "cloudflare:workers";
import { runDurableObjectAlarm, runInDurableObject } from "cloudflare:test";
import worker from "../src/index.mjs";

const network = setupNetwork();

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
  beforeAll(() => network.enable());
  afterEach(() => network.resetHandlers());
  afterAll(() => network.disable());

  it("serves a public health check without revealing configured values", async () => {
    const result = await invoke(new Request("https://worker.example/health"));
    expect(result.status).toBe(200);
    expect(await result.text()).toBe("ok");
  });

  it("protects persistent Drive watch state with the webhook secret", async () => {
    const denied = await invoke(new Request("https://worker.example/watch-state"));
    expect(denied.status).toBe(403);

    const headers = { "X-Drive-Watch-Secret": "fixture-github-token" };
    const saved = { id: "channel-1", resource_id: "resource-1", drive_id: "drive-1", expiration_ms: "1900000000000" };
    const put = await invoke(new Request("https://worker.example/watch-state", {
      method: "PUT", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(saved),
    }));
    expect(put.status).toBe(200);

    const get = await invoke(new Request("https://worker.example/watch-state", { headers }));
    expect(get.status).toBe(200);
    expect(await get.json()).toEqual(saved);
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
