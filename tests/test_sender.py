#!/usr/bin/env python3
"""Recette hors reseau du lecteur de campagnes Split Eval."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "server" / "split_eval_sender.py"
spec = importlib.util.spec_from_file_location("split_eval_sender", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "campagne.zip"
        self.manifest = {
            "schema": 1, "messages": [{
                "statut": "PREPARE_NON_ENVOYE", "to": ["test@example.org"],
                "subject": "Evaluation", "body": "Bonjour",
                "attachments": ["pieces_jointes/6G1_TEST_Eleve_FR.pdf"]
            }]
        }

    def archive(self, pdf=b"%PDF-1.4\n%%EOF", manifest=None):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("campagne.json", json.dumps(manifest or self.manifest))
            z.writestr("pieces_jointes/6G1_TEST_Eleve_FR.pdf", pdf)

    def test_zip_valide(self):
        self.archive()
        self.assertEqual(len(app.load_campaign(self.path)["messages"]), 1)

    def test_refuse_destinataire_invalide(self):
        self.manifest["messages"][0]["to"] = ["adresse-invalide"]
        self.archive()
        with self.assertRaises(ValueError):
            app.load_campaign(self.path)

    def test_refuse_piece_absente(self):
        self.manifest["messages"][0]["attachments"] = ["pieces_jointes/absent.pdf"]
        self.archive()
        with self.assertRaises(ValueError):
            app.load_campaign(self.path)

    def test_mime_piece_jointe(self):
        self.archive()
        with zipfile.ZipFile(self.path) as z:
            msg = app.build_email(z, self.manifest["messages"][0], "test@example.org", {"accuse_lecture": True, "priorite": "high"}, "example.org")
        self.assertEqual(len(list(msg.iter_attachments())), 1)
        self.assertEqual(msg["Disposition-Notification-To"], "test@example.org")
        self.assertEqual(msg["X-Priority"], "1")


if __name__ == "__main__":
    unittest.main()
