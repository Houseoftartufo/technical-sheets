import json
import unittest
from unittest.mock import Mock, call

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
