import copy
import tempfile
import unittest
from unittest.mock import patch
from app.domain import DEMO, process
from app.runtime import Store


class InvoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name + "/test.db")

    def tearDown(self):
        self.store.connection.close()
        self.temp.cleanup()

    def ingest(self, text=None):
        return process(dict(DEMO, ocr_text=text or DEMO["ocr_text"]), self.store)

    def test_valid_invoice_enters_outbox(self):
        result = self.ingest()
        self.assertEqual(result["state"], "validated")
        self.assertEqual(result["fields"]["total"], "143.75")
        self.assertEqual(len(process({"action": "export"}, self.store)["items"]), 1)

    def test_same_invoice_is_not_exported_twice(self):
        first = self.ingest()
        second = self.ingest()
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["document_id"], second["document_id"])
        self.assertEqual(len(process({"action": "export"}, self.store)["items"]), 1)

    def test_conflicting_duplicate_rejected(self):
        self.ingest()
        with self.assertRaises(ValueError):
            self.ingest(DEMO["ocr_text"].replace("143.75", "143.76"))

    def test_bad_total_requires_review_and_no_export(self):
        result = self.ingest(DEMO["ocr_text"].replace("143.75", "143.76"))
        self.assertIn("total_mismatch", result["review_reasons"])
        self.assertEqual(process({"action": "export"}, self.store)["items"], [])

    def test_missing_fields_remain_reviewable(self):
        result = self.ingest("factura: F-1\nsubtotal: 12.00")
        self.assertEqual(result["state"], "manual_review")
        self.assertIn("missing_supplier_tax_id", result["review_reasons"])

    def test_invalid_amount_is_not_rounded_into_validity(self):
        result = self.ingest(DEMO["ocr_text"].replace("125.00", "125.001"))
        self.assertIn("invalid_subtotal", result["review_reasons"])

    def test_negative_amount_requires_review(self):
        result = self.ingest(DEMO["ocr_text"].replace("125.00", "-125.00"))
        self.assertIn("invalid_subtotal", result["review_reasons"])

    def test_explicit_review_corrects_total(self):
        result = self.ingest(DEMO["ocr_text"].replace("143.75", "143.76"))
        approved = process({"action": "review", "document_id": result["document_id"], "decision": "approve", "reviewer": "finance-01", "reason": "Contraste con documento fuente", "corrections": {"total": "143.75"}}, self.store)
        self.assertEqual(approved["state"], "validated")
        self.assertEqual(len(process({"action": "export"}, self.store)["items"]), 1)
        with self.assertRaises(ValueError):
            process({"action": "review", "document_id": result["document_id"], "decision": "approve", "reviewer": "f", "reason": "test"}, self.store)

    def test_review_cannot_bypass_accounting_rules(self):
        result = self.ingest(DEMO["ocr_text"].replace("143.75", "143.76"))
        with self.assertRaises(ValueError):
            process({"action": "review", "document_id": result["document_id"], "decision": "approve", "reviewer": "finance-01", "reason": "Sin corregir"}, self.store)

    def test_export_only_marks_delivered_after_receipt(self):
        invoice = self.ingest()
        item = process({"action": "export"}, self.store)["items"][0]
        result = process({"action": "acknowledge", "outbox_id": item["outbox_id"], "receipt": "ERP-DEMO-52"}, self.store)
        self.assertEqual(result["state"], "exported")
        self.assertEqual(result["document_id"], invoice["document_id"])
        self.assertEqual(process({"action": "export"}, self.store)["items"], [])
        with self.assertRaises(ValueError):
            process({"action": "acknowledge", "outbox_id": item["outbox_id"], "receipt": "another"}, self.store)

    def test_repeated_ocr_key_with_different_values_is_rejected(self):
        with self.assertRaises(ValueError):
            self.ingest(DEMO["ocr_text"] + "\ntotal: 0.00")

    def test_oversized_or_empty_ocr_rejected(self):
        for text in ("", "x" * 100001):
            with self.assertRaises(ValueError):
                process({"ocr_text": text}, self.store)

    def test_model_extraction_cannot_bypass_total_validation(self):
        values = dict(line.split(": ", 1) for line in DEMO["ocr_text"].splitlines())
        values["total"] = "1.00"
        with patch.dict("os.environ", {"MODEL_BACKEND": "ollama"}), patch("app.providers.structured", return_value=values):
            result = process(dict(DEMO, use_model=True), self.store)
        self.assertEqual(result["state"], "manual_review")
        self.assertIn("total_mismatch", result["review_reasons"])

    def test_model_output_with_unexpected_fields_rejected(self):
        with patch.dict("os.environ", {"MODEL_BACKEND": "ollama"}), patch("app.providers.structured", return_value={"approve": True}):
            with self.assertRaises(ValueError):
                process(dict(DEMO, use_model=True), self.store)

    def test_compact_iso_date_requires_review(self):
        result = self.ingest(DEMO["ocr_text"].replace("2026-10-26", "20261026"))
        self.assertIn("invalid_issue_date", result["review_reasons"])

    def test_unsupported_currency_cannot_enter_export_queue(self):
        for currency in ("ZZZ", "JPY"):
            with self.subTest(currency=currency):
                result = self.ingest(DEMO["ocr_text"].replace("USD", currency).replace("F-2026-0042", "F-" + currency))
                self.assertEqual(result["state"], "manual_review")
                self.assertIn("invalid_currency", result["review_reasons"])
        self.assertEqual(process({"action": "export"}, self.store)["items"], [])

    def test_model_fields_require_source_review_even_when_totals_agree(self):
        values = dict(line.split(": ", 1) for line in DEMO["ocr_text"].splitlines())
        with patch.dict("os.environ", {"MODEL_BACKEND": "ollama"}), patch("app.providers.structured", return_value=values):
            result = process({"action": "ingest", "ocr_text": "Documento ilegible", "use_model": True}, self.store)
        self.assertEqual(result["state"], "manual_review")
        self.assertIn("model_extraction_requires_review", result["review_reasons"])
        self.assertEqual(process({"action": "export"}, self.store)["items"], [])
        approved = process({"action": "review", "document_id": result["document_id"], "decision": "approve", "reviewer": "finance-01", "reason": "Campos contrastados con el documento fuente"}, self.store)
        self.assertEqual(approved["state"], "validated")
        self.assertEqual(len(process({"action": "export"}, self.store)["items"]), 1)

    def test_extraction_option_requires_actual_boolean(self):
        with self.assertRaises(ValueError):
            process(dict(DEMO, use_model="true"), self.store)

    def test_invoice_and_outbox_roll_back_if_audit_fails(self):
        process({"action": "export"}, self.store)
        with patch.object(self.store, "event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.store.run(DEMO, "invoice-audit-failure", process)
        self.assertEqual(self.store.connection.execute("SELECT count(*) FROM invoices").fetchone()[0], 0)
        self.assertEqual(process({"action": "export"}, self.store)["items"], [])
        self.store.run(DEMO, "invoice-audit-failure", process)
        self.assertEqual(len(process({"action": "export"}, self.store)["items"]), 1)

    def test_missing_supplier_does_not_create_an_empty_identity_collision(self):
        text = DEMO["ocr_text"].replace("supplier_tax_id: DEMO-179001", "supplier_tax_id: ")
        first = self.ingest(text)
        second = self.ingest(text)
        self.assertEqual(first["state"], "manual_review")
        self.assertNotEqual(first["document_id"], second["document_id"])


if __name__ == "__main__":
    unittest.main()
