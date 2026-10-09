import sys
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
        self.assertIn("push:", self.workflow)
        self.assertIn("branches: [main]", self.workflow)
        self.assertIn('cron: "*/15 * * * *"', self.workflow)

    def test_serialized_with_read_only_repository_permissions(self):
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)

    def test_uses_vercel_secret_and_org_project_variables(self):
        for name in ("VERCEL_TOKEN", "vars.VERCEL_ORG_ID", "vars.VERCEL_PROJECT_ID", "secrets.DRIVE_SOURCE_FOLDER_ID", "secrets.DRIVE_CATALOG_FOLDER_ID"):
            self.assertIn(name, self.workflow)
        self.assertIn("VERCEL_TOKEN", self.readme)
        self.assertIn("VERCEL_ORG_ID", self.readme)
        self.assertIn("VERCEL_PROJECT_ID", self.readme)
        self.assertIn("VERCEL_ORG_ID: ${{ vars.VERCEL_ORG_ID }}", self.workflow)
        self.assertIn("VERCEL_PROJECT_ID: ${{ vars.VERCEL_PROJECT_ID }}", self.workflow)
        self.assertNotIn("vercel link", self.workflow)

    def test_preview_smoke_precedes_production_and_drive_finalization(self):
        preview = self.workflow.index("Deploy Vercel preview")
        smoke = self.workflow.index("Smoke-test preview")
        production = self.workflow.index("Deploy Vercel production")
        drive = self.workflow.index("Finalize Drive state")
        self.assertLess(preview, smoke)
        self.assertLess(smoke, production)
        self.assertLess(production, drive)
        self.assertIn("active_products", self.workflow)
        self.assertIn("steps.prepare.outputs.has_changes == 'true'", self.workflow)
        self.assertIn("Record workflow outcome", self.workflow)
        self.assertIn("workflow_status", self.workflow)

    def test_never_commits_generated_outputs_or_manifest_and_always_uploads_report(self):
        for forbidden in ("git push", "git commit", "git add _BUILD/drive_manifest.json"):
            self.assertNotIn(forbidden, self.workflow)
        self.assertIn("if: always()", self.workflow)
        self.assertIn("drive_sync_report.json", self.workflow)
        self.assertIn("preview_deployment_url", self.workflow)
        self.assertIn("production_deployment_url", self.workflow)
        self.assertIn("runner.temp", self.workflow)

    def test_readme_documents_git_deploy_prevention_and_setup(self):
        self.assertIn("Ignored Build Step", self.readme)
        self.assertIn("exit 0", self.readme)
        self.assertIn("deploy avviati dai push Git", self.readme)
        self.assertIn("Run workflow", self.readme)

if __name__ == "__main__": unittest.main()
