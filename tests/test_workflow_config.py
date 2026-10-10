import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-drive.yml"
README = ROOT / "README.md"


class WorkflowConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")

    def test_runs_on_schedule_manual_and_main_push(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("publish_to_production:", self.workflow)
        self.assertIn("default: false", self.workflow)
        self.assertIn("push:", self.workflow)
        self.assertIn("branches: [main]", self.workflow)
        self.assertIn('cron: "*/15 * * * *"', self.workflow)

    def test_has_only_scoped_permissions_needed_for_preview_and_catalog_push(self):
        self.assertIn("contents: write", self.workflow)
        self.assertIn("deployments: read", self.workflow)
        self.assertIn("statuses: read", self.workflow)
        self.assertNotIn("pull-requests:", self.workflow)
        self.assertNotIn("contents: read\n", self.workflow)

    def test_does_not_depend_on_vercel_cli_or_vercel_secrets(self):
        for token in ("VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID", "vercel deploy", "vercel link"):
            self.assertNotIn(token, self.workflow)
            self.assertNotIn(token, self.readme)
        self.assertIn("collegata a Vercel tramite GitHub", self.readme)

    def test_uses_official_generator_then_applies_only_validated_catalog_paths(self):
        self.assertIn("_BUILD/engine.py", self.workflow)
        self.assertIn("_BUILD/build_site_bundle.py", self.workflow)
        self.assertIn("_BUILD/apply_site_bundle.py", self.workflow)
        self.assertIn("DRIVE_GENERATED_DIR: /tmp/technical-sheets-generated", self.workflow)
        self.assertNotIn("${{ runner.temp }}/technical-sheets-generated", self.workflow)
        self.assertIn('subprocess.run(["git","add","-A","--",*sorted(paths)]', self.workflow)
        self.assertNotIn("git add .", self.workflow)
        self.assertIn('paths.update(plan["active_products"])', self.workflow)
        self.assertIn('paths.update(plan["removed_folders"])', self.workflow)
        self.assertIn('git rebase "origin/$BRANCH"', self.workflow)
        self.assertNotIn("--force", self.workflow)

    def test_preview_and_production_checks_precede_drive_finalization(self):
        preview = self.workflow.index("Wait for Vercel Git preview deployment")
        smoke = self.workflow.index("Validate catalog bundle for the ready Vercel preview")
        production = self.workflow.index("Promote validated catalog commit to main")
        verify = self.workflow.index("Verify official production catalog")
        finalize = self.workflow.index("Finalize Drive state")
        self.assertLess(preview, smoke)
        self.assertLess(smoke, production)
        self.assertLess(production, verify)
        self.assertLess(verify, finalize)
        self.assertIn("technical.houseoftartufo.com", self.workflow)

    def test_never_stages_unrelated_work_and_always_uploads_report(self):
        self.assertNotIn("git add .", self.workflow)
        self.assertIn("if: always()", self.workflow)
        self.assertIn("drive_sync_report.json", self.workflow)
        self.assertIn("preview_branch_url", self.workflow)
        self.assertIn("preview_deployment_url", self.workflow)
        self.assertIn("production_deployment_url", self.workflow)

    def test_manual_dispatch_defaults_to_preview_and_only_main_can_publish(self):
        production = self.workflow.split("- name: Promote validated catalog commit to main", 1)[1].split("- name: Verify official production catalog", 1)[0]
        self.assertIn("github.ref == 'refs/heads/main'", production)
        self.assertIn("github.event_name != 'workflow_dispatch'", production)
        self.assertIn("github.event.inputs.publish_to_production == 'true'", production)
        finalize = self.workflow.split("- name: Finalize Drive state", 1)[1].split("- name: Record workflow outcome", 1)[0]
        self.assertIn("steps.production.outcome == 'success'", finalize)

    def test_readme_documents_git_preview_setup_without_a_vercel_token(self):
        self.assertIn("collegata a Vercel tramite GitHub", self.readme)
        self.assertIn("preview", self.readme.lower())
        self.assertIn("Ignored Build Step", self.readme)


if __name__ == "__main__":
    unittest.main()
