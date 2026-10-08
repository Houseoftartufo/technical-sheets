import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"_BUILD"))
import sync_drive
from drive_sync_state import product_manifest_entry, source_fingerprint
from drive_schema import LANGS
from build_site_bundle import migrate_legacy_product_titles


def product(folder="29_TEST",title="Truffle sample"):
    localized=lambda text:{lang:f"{text} {lang}" for lang in LANGS}
    return {
      "folder":folder,"title":localized(title),
      "general":{"ean":"","typology":localized("Food product"),"shelf":localized("12 months"),"packaging":localized("Jar"),"labelling":localized("EU"),"gmo":localized("No GMO")},
      "ingredients":{"ingredients":localized("Water, truffle"),"allergens":localized("NONE")},
      "storage":{"instructions":localized("Store cool"),"method":localized("Ready to use")},
      "nutrition":{"energy":"100 kJ / 20 kcal","fat":"1 g","sat":"0 g","carb":"2 g","sugar":"1 g","protein":"1 g","salt":"0.1 g","fibre":"0 g"},
      "characteristics":{"chemical":localized("pH 5"),"micro":localized("Compliant")},
    }

class Request:
    def __init__(self,value): self.value=value
    def execute(self): return self.value
class FakeFiles:
    def __init__(self,items): self.items=items
    def list(self,q,**kwargs):
        parent=q.split("'")[1]
        name=q.split("name = '",1)[1].split("'",1)[0] if "name = '" in q else None
        return Request({"files":[x for x in self.items if parent in x.get("parents",[]) and not x.get("trashed") and (name is None or x["name"]==name)]})
class FakeDrive:
    def __init__(self,items): self.items=items
    def files(self): return FakeFiles(self.items)

class DriveSiteSyncTests(unittest.TestCase):
    def run_prepare(self,pending,active,manifest,extracted=None,extract_error=None):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(sync_drive,"list_source_items",side_effect=[pending,active]), \
             patch.object(sync_drive,"download",return_value=b"supplier"), \
             patch.object(sync_drive,"extract",side_effect=(RuntimeError(extract_error) if extract_error else None) if extract_error else None) as extractor:
            if not extract_error:
                extractor.side_effect=lambda *_: extracted or product()
            plan=sync_drive.prepare(FakeDrive([]),"intake","processed",manifest,object(),build_dir=Path(tmp)/"empty-build",run_dir=Path(tmp)/"run")
            return plan

    def test_new_supplier_sheet_is_validated_and_queued_for_same_id_move(self):
        source={"id":"new","name":"sample.pdf","mimeType":"application/pdf","md5Checksum":"one"}
        plan=self.run_prepare([source],[],{"version":2,"products":{},"legacy_folders":[]},product())
        self.assertEqual(plan["status"],"ready")
        self.assertEqual(plan["move_source_ids"],["new"])
        self.assertIn("29_TEST",plan["imported"])
        self.assertEqual(plan["next_manifest"]["products"]["new"]["folder"],"29_TEST")

    def test_replacement_of_same_active_file_regenerates_only_that_product(self):
        old={"id":"existing","name":"sample.pdf","mimeType":"application/pdf","md5Checksum":"old"}
        new={**old,"md5Checksum":"new"}
        entry=product_manifest_entry(old,"29_TEST",product()["title"])
        plan=self.run_prepare([],[new],{"version":2,"products":{"existing":entry},"legacy_folders":[]},product(title="Updated sample"))
        self.assertEqual(plan["status"],"ready")
        self.assertEqual(plan["changed_active"],[new])
        self.assertEqual(plan["imported"]["29_TEST"]["title"]["ITA"],"Updated sample ITA")
        self.assertEqual(plan["move_source_ids"],[])

    def test_removing_active_source_deactivates_only_manifest_owned_folder(self):
        source={"id":"gone","name":"old.pdf","mimeType":"application/pdf","md5Checksum":"old"}
        entry=product_manifest_entry(source,"29_TEST",product()["title"])
        plan=self.run_prepare([],[],{"version":2,"products":{"gone":entry},"legacy_folders":["01_LEGACY"]})
        self.assertEqual(plan["removed_folders"],["29_TEST"])
        self.assertEqual(plan["next_manifest"]["legacy_folders"],["01_LEGACY"])

    def test_failed_extraction_blocks_and_keeps_pending_original_unmoved(self):
        source={"id":"bad","name":"missing.pdf","mimeType":"application/pdf","md5Checksum":"x"}
        plan=self.run_prepare([source],[],{"version":2,"products":{},"legacy_folders":[]},extract_error="missing ingredients")
        self.assertEqual(plan["status"],"blocked")
        self.assertEqual(plan["move_source_ids"],[])
        self.assertEqual(plan["imported"],{})
        self.assertIn("missing ingredients",plan["errors"][0]["errors"][0])

    def test_no_change_skips_extraction_and_preserves_existing_product(self):
        source={"id":"same","name":"sample.pdf","mimeType":"application/pdf","md5Checksum":"stable"}
        entry=product_manifest_entry(source,"29_TEST",product()["title"])
        with patch.object(sync_drive,"list_source_items",side_effect=[[],[source]]), patch.object(sync_drive,"extract") as extract:
            with tempfile.TemporaryDirectory() as tmp:
                plan=sync_drive.prepare(FakeDrive([]),"intake","processed",{"version":2,"products":{"same":entry},"legacy_folders":[]},object(),build_dir=Path(tmp)/"build",run_dir=Path(tmp)/"run")
        self.assertEqual(plan["unchanged"],["same"])
        self.assertEqual(plan["imported"],{})
        self.assertEqual(plan["active_products"]["29_TEST"],product()["title"])
        extract.assert_not_called()

    def test_carpaccio_legacy_manifest_titles_are_read_from_existing_drive_html(self):
        folder="28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO"
        manifest={"version":1,"products":{"legacy-source":{"folder":folder,"name":"Carpaccio original.pdf","fingerprint":"old"}},"legacy_folders":[]}
        items=[{"id":"folder-id","name":folder,"mimeType":"application/vnd.google-apps.folder","parents":["catalog"]}]
        contents={}
        for lang in LANGS:
            file_id=f"{lang}-html"
            items.append({"id":file_id,"name":f"{folder}_{lang}.html","parents":["folder-id"]})
            contents[file_id]=f'<div class="product-title">Carpaccio {lang} &amp; oil</div>'.encode()
        drive=FakeDrive(items)
        with patch("build_site_bundle.download_drive_file",side_effect=lambda _drive,item:contents[item["id"]]):
            active=migrate_legacy_product_titles(drive,"catalog",manifest,{folder:{}})
        self.assertEqual(active[folder],{lang:f"Carpaccio {lang} & oil" for lang in LANGS})
        self.assertEqual(manifest["products"]["legacy-source"]["title"],active[folder])
        self.assertEqual(manifest["version"],2)

if __name__=="__main__": unittest.main()
