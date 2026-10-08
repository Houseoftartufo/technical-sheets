import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"_BUILD"))
import sync_drive

class FakeFiles:
    def __init__(self): self.upload=None
    def create(self, file, purpose):
        self.upload=(file,purpose)
        return type("File",(),{"id":"uploaded-pdf"})()
    def delete(self, file_id): self.deleted=file_id
class FakeResponses:
    def create(self, **kwargs): return type("Response",(),{"output_text":"{}"})()
class FakeClient:
    def __init__(self): self.files=FakeFiles(); self.responses=FakeResponses()

class WordExtractionTests(unittest.TestCase):
    def test_docx_is_converted_to_pdf_before_openai_file_upload(self):
        client=FakeClient()
        item={"id":"word","name":"supplier.docx","mimeType":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        def convert(command, **kwargs):
            source=Path(command[-1]); (Path(command[command.index("--outdir")+1])/(source.stem+".pdf")).write_bytes(b"%PDF converted Word")
        with patch("sync_drive.subprocess.run",side_effect=convert) as run:
            result=sync_drive.extract(client,item,b"word-document-bytes")
        run.assert_called_once()
        self.assertEqual(client.files.upload[0][0],"supplier.pdf")
        self.assertEqual(client.files.upload[0][1],b"%PDF converted Word")
        self.assertEqual(result,{})
        self.assertEqual(client.files.deleted,"uploaded-pdf")

    def test_uploaded_openai_file_is_deleted_even_when_extraction_fails(self):
        client=FakeClient()
        client.responses.create=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("extraction failed"))
        item={"id":"word","name":"supplier.pdf","mimeType":"application/pdf"}
        with self.assertRaisesRegex(RuntimeError,"extraction failed"):
            sync_drive.extract(client,item,b"%PDF original")
        self.assertEqual(client.files.deleted,"uploaded-pdf")

if __name__=="__main__": unittest.main()
