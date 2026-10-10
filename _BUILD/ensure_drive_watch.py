"""Create or renew a Google Drive changes.watch channel for the catalog drive."""
import json
import os
import sys
import time
import uuid
import base64
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from pathlib import Path

RENEW_BEFORE_MS = 24 * 60 * 60 * 1000
REQUESTED_LIFETIME_MS = 6 * 24 * 60 * 60 * 1000
GITHUB_OIDC_AUDIENCE = "https://technical-sheets.houseoftartufo.com/drive-watch"
OIDC_DIAGNOSTIC_CLAIMS = (
    "iss", "aud", "repository", "repository_id", "repository_owner_id",
    "ref", "workflow_ref", "event_name", "iat", "nbf", "exp",
)


def oidc_claim_summary(token):
    """Return only public workflow claims for diagnosing a rejected OIDC token."""
    try:
        header_segment, payload_segment, _ = token.split(".")
        decode = lambda segment: json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        header = decode(header_segment)
        claims = decode(payload_segment)
        return {
            "alg": header.get("alg"),
            "kid": header.get("kid"),
            **{name: claims.get(name) for name in OIDC_DIAGNOSTIC_CLAIMS},
        }
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"jwt_format": "invalid"}


def request_github_oidc_token():
    """Request a short-lived identity token for the GitHub Actions watch job."""
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not request_url or not request_token:
        raise RuntimeError("GitHub Actions OIDC is unavailable; grant id-token: write to the watch job")

    parsed = urlsplit(request_url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if key != "audience"]
    query.append(("audience", GITHUB_OIDC_AUDIENCE))
    token_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
    request = urllib.request.Request(
        token_url,
        headers={"Authorization": f"Bearer {request_token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("GitHub Actions could not issue the Drive watch identity token") from None
    token = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("GitHub Actions returned an invalid Drive watch identity token")
    return token


class WorkerDriveWatchState:
    def __init__(self, worker_url, token):
        self.url = worker_url.rstrip("/").removesuffix("/drive") + "/watch-state"
        self.token = token

    def _request(self, method, value=None):
        data = json.dumps(value, separators=(",", ":")).encode("utf-8") if value is not None else None
        request = urllib.request.Request(
            self.url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-store",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            diagnostic = ""
            if exc.code == 403:
                response_body = exc.read(256).decode("utf-8", errors="replace").strip()
                match = re.fullmatch(r"forbidden:([a-z_]+)", response_body)
                if match:
                    diagnostic = f" ({match.group(1)})"
                print("Rejected GitHub OIDC claims (token omitted): " +
                      json.dumps(oidc_claim_summary(self.token), sort_keys=True))
            raise RuntimeError(f"Cloudflare watch state API returned HTTP {exc.code}{diagnostic}") from None
        if method == "GET":
            try:
                state = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise RuntimeError("Cloudflare returned invalid Drive watch state") from None
            if state is not None and not isinstance(state, dict):
                raise RuntimeError("Cloudflare returned invalid Drive watch state")
            return state
        return None

    def get_variable(self):
        return self._request("GET")

    def set_variable(self, value):
        self._request("PUT", value)


def _stop_channel(drive, channel_id, resource_id):
    if not channel_id or not resource_id:
        return
    drive.channels().stop(body={"id": channel_id, "resourceId": resource_id}).execute()


def ensure(drive, config, github):
    """Ensure a live notification channel; return a non-sensitive status dict."""
    webhook_url = config.get("webhook_url")
    webhook_token = config.get("webhook_token")
    if not webhook_url and not webhook_token:
        return {"status": "skipped", "reason": "webhook_not_configured"}
    if not webhook_url or not webhook_token:
        raise RuntimeError("Both DRIVE_WEBHOOK_URL and DRIVE_WEBHOOK_TOKEN are required")

    now_ms = int(config.get("now_ms", time.time() * 1000))
    old = config.get("state") or {}
    try:
        old_expiration = int(old.get("expiration_ms", 0))
    except (TypeError, ValueError):
        old_expiration = 0
    if old.get("id") and old.get("resource_id") and old_expiration > now_ms + RENEW_BEFORE_MS:
        return {"status": "active", "expiration_ms": old_expiration}

    source_folder_id = config.get("source_folder_id")
    if not source_folder_id:
        raise RuntimeError("DRIVE_SOURCE_FOLDER_ID is required to register the Drive change channel")
    source = drive.files().get(
        fileId=source_folder_id,
        fields="id,driveId,mimeType",
        supportsAllDrives=True,
    ).execute()
    drive_id = source.get("driveId")
    if not drive_id:
        raise RuntimeError("DRIVE_SOURCE_FOLDER_ID must be inside a shared drive with a driveId")

    page_token = drive.changes().getStartPageToken(
        driveId=drive_id,
        supportsAllDrives=True,
    ).execute().get("startPageToken")
    if not page_token:
        raise RuntimeError("Google Drive did not return a shared-drive change page token")

    channel_id = str(uuid.uuid4())
    new_channel = drive.changes().watch(
        pageToken=page_token,
        driveId=drive_id,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        body={
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
            "token": webhook_token,
            "expiration": str(now_ms + REQUESTED_LIFETIME_MS),
        },
    ).execute()
    resource_id = new_channel.get("resourceId")
    if not resource_id:
        raise RuntimeError("Google Drive created a channel without a resource ID")

    state = {
        "id": channel_id,
        "resource_id": resource_id,
        "drive_id": drive_id,
        "expiration_ms": str(new_channel.get("expiration", now_ms + REQUESTED_LIFETIME_MS)),
    }
    try:
        github.set_variable(state)
    except Exception:
        try:
            _stop_channel(drive, channel_id, resource_id)
        except Exception:
            pass
        raise

    if old.get("id") and old.get("resource_id"):
        try:
            _stop_channel(drive, old["id"], old["resource_id"])
        except Exception:
            # The old channel expires on its own; new channel state is already durable.
            pass
    return {"status": "renewed", "expiration_ms": int(state["expiration_ms"]), "drive_id": drive_id}


def _write_status(result):
    run_dir = os.environ.get("DRIVE_RUN_DIR")
    if run_dir:
        path = Path(run_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "drive_watch_status.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(f"### Drive push channel: {result.get('status', 'error')}\n\n")
            if result.get("reason"):
                stream.write(f"{result['reason']}\n\n")
            if result.get("expiration_ms"):
                stream.write(f"Scadenza: {result['expiration_ms']}\n\n")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        status = result.get("status", "error")
        if status not in {"active", "renewed", "skipped", "error"}:
            status = "error"
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"status={status}\n")


def main():
    raw_credentials = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if not raw_credentials:
        _write_status({"status": "skipped", "reason": "google_credentials_not_configured"})
        return 0
    try:
        from sync_drive import FOLDER_ID, drive_client
        state_store = WorkerDriveWatchState(
            os.environ["DRIVE_WEBHOOK_URL"], request_github_oidc_token()
        )
        state = state_store.get_variable()
        result = ensure(
            drive_client(),
            {
                "webhook_url": os.environ.get("DRIVE_WEBHOOK_URL", ""),
                "webhook_token": os.environ.get("DRIVE_WEBHOOK_TOKEN", ""),
                "source_folder_id": os.environ.get("DRIVE_SOURCE_FOLDER_ID") or FOLDER_ID,
                "state": state,
            },
            state_store,
        )
        _write_status(result)
        print(f"Drive push channel: {result['status']}")
        return 0
    except Exception as exc:
        result = {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}
        _write_status(result)
        print(f"Drive push channel setup failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
