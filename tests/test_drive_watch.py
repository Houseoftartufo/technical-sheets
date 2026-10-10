import json
import unittest
import base64
from urllib.parse import parse_qs, urlsplit
from unittest.mock import Mock, call
from unittest.mock import patch

from _BUILD import ensure_drive_watch


class DriveWatchTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "webhook_url": "https://worker.example/drive",
            "webhook_token": "test-only-token",
            "source_folder_id": "intake-folder-id",
            "state": None,
            "now_ms": 1_800_000_000_000,
        }
        self.drive = Mock()
        self.github = Mock()
        files = self.drive.files.return_value
        files.get.return_value.execute.return_value = {
            "id": "intake", "driveId": "shared-drive-id", "mimeType": "application/vnd.google-apps.folder"
        }
        changes = self.drive.changes.return_value
        changes.getStartPageToken.return_value.execute.return_value = {"startPageToken": "page-123"}
        changes.watch.return_value.execute.return_value = {"resourceId": "resource-456", "expiration": str(self.config["now_ms"] + 6 * 86400_000)}

    @patch("_BUILD.ensure_drive_watch.urllib.request.urlopen")
    def test_worker_state_store_reads_and_writes_cloudflare_durable_state(self, urlopen):
        from _BUILD.ensure_drive_watch import WorkerDriveWatchState

        urlopen.return_value.__enter__.return_value.status = 200
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"id":"channel-1"}'
        store = WorkerDriveWatchState("https://worker.example/drive", "state-secret-token")
        self.assertEqual(store.get_variable(), {"id": "channel-1"})
        store.set_variable({"id": "channel-2"})
        self.assertEqual(urlopen.call_count, 2)
        get_request = urlopen.call_args_list[0].args[0]
        put_request = urlopen.call_args_list[1].args[0]
        self.assertEqual(get_request.full_url, "https://worker.example/watch-state")
        self.assertEqual(get_request.get_header("Authorization"), "Bearer state-secret-token")
        self.assertEqual(put_request.get_method(), "PUT")
        self.assertEqual(json.loads(put_request.data), {"id": "channel-2"})

    @patch.dict("os.environ", {
        "ACTIONS_ID_TOKEN_REQUEST_URL": "https://token.actions.githubusercontent.com/idtoken?api-version=2",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "runner-request-token",
    })
    @patch("_BUILD.ensure_drive_watch.urllib.request.urlopen")
    def test_requests_github_oidc_token_with_the_worker_audience(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"value":"signed-oidc-token"}'
        token = ensure_drive_watch.request_github_oidc_token()
        self.assertEqual(token, "signed-oidc-token")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer runner-request-token")
        self.assertEqual(parse_qs(urlsplit(request.full_url).query), {
            "api-version": ["2"],
            "audience": [ensure_drive_watch.GITHUB_OIDC_AUDIENCE],
        })

    @patch.dict("os.environ", {}, clear=True)
    def test_oidc_request_requires_the_actions_identity_endpoint(self):
        with self.assertRaisesRegex(RuntimeError, "id-token: write"):
            ensure_drive_watch.request_github_oidc_token()

    def test_oidc_diagnostics_include_only_non_secret_identity_claims(self):
        def segment(value):
            return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
        token = ".".join((
            segment({"alg": "RS256", "kid": "public-key-id"}),
            segment({"repository": "Houseoftartufo/technical-sheets", "actor": "private-actor", "ref": "refs/heads/main"}),
            "signature-is-never-reported",
        ))
        summary = ensure_drive_watch.oidc_claim_summary(token)
        self.assertEqual(summary["repository"], "Houseoftartufo/technical-sheets")
        self.assertEqual(summary["ref"], "refs/heads/main")
        self.assertEqual(summary["kid"], "public-key-id")
        self.assertNotIn("actor", summary)
        self.assertNotIn("signature", json.dumps(summary))

    def test_missing_webhook_configuration_skips_without_drive_calls(self):
        result = ensure_drive_watch.ensure(Mock(), {"webhook_url": "", "webhook_token": ""}, Mock())
        self.assertEqual(result["status"], "skipped")

    def test_creates_shared_drive_channel_and_saves_state(self):
        result = ensure_drive_watch.ensure(self.drive, self.config, self.github)
        self.assertEqual(result["status"], "renewed")
        args = self.drive.changes.return_value.watch.call_args
        self.assertEqual(args.kwargs["driveId"], "shared-drive-id")
        self.assertTrue(args.kwargs["supportsAllDrives"])
        self.assertTrue(args.kwargs["includeItemsFromAllDrives"])
        body = args.kwargs["body"]
        self.assertEqual(body["type"], "web_hook")
        self.assertEqual(body["address"], self.config["webhook_url"])
        self.assertEqual(body["token"], self.config["webhook_token"])
        self.github.set_variable.assert_called_once()
        saved = self.github.set_variable.call_args.args[0]
        self.assertEqual(saved["resource_id"], "resource-456")
        self.assertEqual(saved["drive_id"], "shared-drive-id")

    def test_does_not_renew_channel_with_more_than_one_day_remaining(self):
        state = {
            "id": "old", "resource_id": "old-resource", "drive_id": "shared-drive-id",
            "expiration_ms": str(self.config["now_ms"] + 2 * 86400_000),
        }
        result = ensure_drive_watch.ensure(self.drive, {**self.config, "state": state}, self.github)
        self.assertEqual(result["status"], "active")
        self.drive.changes.return_value.watch.assert_not_called()
        self.github.set_variable.assert_not_called()

    def test_replaces_channel_before_stopping_old_channel(self):
        state = {
            "id": "old", "resource_id": "old-resource", "drive_id": "shared-drive-id",
            "expiration_ms": str(self.config["now_ms"] + 1000),
        }
        events = Mock()
        self.github.set_variable.side_effect = lambda value: events.saved()
        self.drive.channels.return_value.stop.side_effect = lambda **kwargs: events.stopped()
        result = ensure_drive_watch.ensure(self.drive, {**self.config, "state": state}, self.github)
        self.assertEqual(result["status"], "renewed")
        self.assertEqual(events.mock_calls[:2], [call.saved(), call.stopped()])
        self.drive.channels.return_value.stop.assert_called_once_with(body={"id": "old", "resourceId": "old-resource"})

    def test_keeps_old_channel_when_persisting_new_state_fails(self):
        state = {
            "id": "old", "resource_id": "old-resource", "drive_id": "shared-drive-id",
            "expiration_ms": str(self.config["now_ms"] + 1000),
        }
        self.github.set_variable.side_effect = RuntimeError("GitHub API unavailable")
        with self.assertRaisesRegex(RuntimeError, "GitHub API unavailable"):
            ensure_drive_watch.ensure(self.drive, {**self.config, "state": state}, self.github)
        self.drive.channels.return_value.stop.assert_called_once()
        stopped = self.drive.channels.return_value.stop.call_args.kwargs["body"]
        self.assertNotEqual(stopped["id"], "old")


if __name__ == "__main__":
    unittest.main()
