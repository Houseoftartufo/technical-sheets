"""Finalize the Drive manifest and move intake originals after production deploy."""
import json
import os
from pathlib import Path

from publish_drive import apply, drive_client


def main():
    run_dir=Path(os.environ["DRIVE_RUN_DIR"])
    plan=json.loads((run_dir/"drive_sync_plan.json").read_text(encoding="utf-8"))
    manifest_file_id=(run_dir/"manifest_file_id.txt").read_text(encoding="utf-8").strip() or None
    result=apply(drive_client(),plan,Path(os.environ["DRIVE_GENERATED_DIR"]),
                 os.environ["DRIVE_CATALOG_FOLDER_ID"],plan["processed_folder_id"],manifest_file_id)
    report_path=run_dir/"drive_sync_report.json"
    report=json.loads(report_path.read_text(encoding="utf-8"))
    report.update(result)
    report["status"]="complete"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
