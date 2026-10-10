import test from "node:test";
import assert from "node:assert/strict";
import worker, { DriveDispatchDebouncer } from "../cloudflare/drive-webhook/src/index.mjs";

function notification(state = "update", token = "expected-secret") {
  return new Request("https://worker.example/drive", {
    method: "POST",
    headers: { "X-Goog-Channel-Token": token, "X-Goog-Resource-State": state },
  });
}

function fakeDispatcher(onFetch = async () => new Response("queued", { status: 202 })) {
  return { idFromName: (name) => name, get: () => ({ fetch: onFetch }) };
}

function fakeStorage() {
  const values = new Map();
  let alarmAt = null;
  return {
    values,
    get: async (key) => values.get(key),
    put: async (key, value) => values.set(key, value),
    delete: async (key) => values.delete(key),
    setAlarm: async (time) => { alarmAt = time; },
    get alarmAt() { return alarmAt; },
  };
}

test("health endpoint is public and does not disclose configuration", async () => {
  const response = await worker.fetch(new Request("https://worker.example/health"), {});
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "ok");
});

test("rejects requests without a valid channel token", async () => {
  let calls = 0;
  const response = await worker.fetch(notification("update", "wrong"), {
    DRIVE_WEBHOOK_TOKEN: "expected-secret",
    DISPATCHER: fakeDispatcher(async () => { calls += 1; return new Response(null, { status: 204 }); }),
  });
  assert.equal(response.status, 403);
  assert.equal(calls, 0);
});

test("rejects webhook requests when the worker is not configured", async () => {
  const response = await worker.fetch(notification(), {});
  assert.equal(response.status, 503);
});

test("acknowledges initial channel sync without dispatching", async () => {
  let calls = 0;
  const response = await worker.fetch(notification("sync"), {
    DRIVE_WEBHOOK_TOKEN: "expected-secret",
    DISPATCHER: fakeDispatcher(async () => { calls += 1; return new Response(null, { status: 204 }); }),
  });
  assert.equal(response.status, 204);
  assert.equal(calls, 0);
});

test("queues a recognized Drive event for a fixed main-branch workflow", async () => {
  let queuedRequest;
  const response = await worker.fetch(notification("add"), {
    DRIVE_WEBHOOK_TOKEN: "expected-secret",
    DISPATCHER: fakeDispatcher(async (request) => { queuedRequest = request; return new Response("queued", { status: 202 }); }),
  });
  assert.equal(response.status, 202);
  assert.equal(new URL(String(queuedRequest)).pathname, "/schedule");
});

test("acknowledges unknown event states without queueing", async () => {
  let calls = 0;
  const response = await worker.fetch(notification("future-state"), {
    DRIVE_WEBHOOK_TOKEN: "expected-secret",
    DISPATCHER: fakeDispatcher(async () => { calls += 1; return new Response(null, { status: 202 }); }),
  });
  assert.equal(response.status, 204);
  assert.equal(calls, 0);
});

test("debounces a burst of Drive events into one GitHub dispatch", async () => {
  const storage = fakeStorage();
  const state = { storage };
  let captured;
  const env = {
    GITHUB_DISPATCH_TOKEN: "dispatch-secret",
    FETCH: async (url, options) => {
      captured = { url: String(url), options };
      return new Response(null, { status: 204 });
    },
  };
  const debouncer = new DriveDispatchDebouncer(state, env);
  await debouncer.fetch(new Request("https://dispatcher.internal/schedule", { method: "POST" }));
  await debouncer.fetch(new Request("https://dispatcher.internal/schedule", { method: "POST" }));
  assert.equal(storage.values.get("revision"), 2);
  assert.ok(storage.alarmAt);
  await debouncer.alarm();
  assert.equal(captured.url, "https://api.github.com/repos/Houseoftartufo/technical-sheets/actions/workflows/sync-drive.yml/dispatches");
  assert.equal(captured.options.method, "POST");
  assert.equal(captured.options.headers.Authorization, "Bearer dispatch-secret");
  assert.deepEqual(JSON.parse(captured.options.body), { ref: "main", inputs: { publish_to_production: "true" } });
  assert.equal(storage.values.has("revision"), false);
});

test("retries a failed GitHub dispatch without exposing secrets", async () => {
  const storage = fakeStorage();
  const debouncer = new DriveDispatchDebouncer({ storage }, {
    GITHUB_DISPATCH_TOKEN: "dispatch-secret",
    FETCH: async () => new Response("dispatch-secret", { status: 503 }),
  });
  await debouncer.fetch(new Request("https://dispatcher.internal/schedule", { method: "POST" }));
  await debouncer.alarm();
  assert.equal(storage.values.get("attempts"), 1);
  assert.ok(storage.alarmAt > Date.now());
});
