import tempfile
import unittest
from pathlib import Path

from site_builder_email.drafting import build_email_draft
from site_builder_email.storage import Database


class DraftingTests(unittest.TestCase):
    def test_build_email_draft_uses_custom_benefits(self) -> None:
        draft = build_email_draft(
            {
                "business_name": "Northside Plumbing",
                "contact_name": "Alex",
                "location": "Dallas",
                "benefits_focus": "show services clearly, get more quote requests, look more established",
                "offer_summary": "build and set up a personalized website for your business",
            },
            sender_name="Jordan",
        )

        self.assertIn("Northside Plumbing", draft["subject"])
        self.assertIn("Hi Alex", draft["body"])
        self.assertIn("- show services clearly", draft["body"])
        self.assertIn("Jordan", draft["body"])


class StorageTests(unittest.TestCase):
    def test_create_and_update_lead(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Database(Path(temp_dir) / "outreach.db")
            lead = database.create_lead(
                {
                    "business_name": "Luna Salon",
                    "email": "owner@example.com",
                }
            )

            self.assertEqual(lead["status"], "draft")

            updated = database.update_lead(
                lead["id"],
                {
                    "draft_subject": "A quick website idea",
                    "status": "ready_to_review",
                    "do_not_contact": True,
                },
            )

            self.assertEqual(updated["draft_subject"], "A quick website idea")
            self.assertTrue(updated["do_not_contact"])
            self.assertEqual(updated["status"], "ready_to_review")


if __name__ == "__main__":
    unittest.main()

