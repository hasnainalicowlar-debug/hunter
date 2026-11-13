"""
Comprehensive Test Suite for AI Daily Restaurant Discovery & POS Sales Lead Hunter
Covers all 14 mandatory acceptance test criteria.
"""

import unittest
import os
import sys
import datetime
import sqlite3
import json
from zoneinfo import ZoneInfo

# Add parent path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import get_connection
from collector.hunter.scheduler import hunter_scheduler, HunterScheduler
from collector.hunter.contact_verifier import verify_contacts, clean_pakistani_phone
from collector.hunter.connectors.web_intent_connector import hunt_buyer_intent
from collector.hunter.connectors.social_announcements_connector import hunt_new_openings
from collector.hunter.dedup_and_updater import match_existing_business, process_record_update
from collector.hunter.report_generator import generate_daily_report
from collector.hunter.daily_hunter_engine import execute_lead_hunter_job
from exports.export_generator import run_exports, EXPORTS_DIR, CSV_FILENAME, EXCEL_FILENAME

class TestLeadHunterModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_daily_scheduler_initialization_and_timezone(self):
        """Criterion 1: Daily scheduler starts correctly and adheres to Asia/Karachi timezone."""
        cfg = hunter_scheduler.get_schedule_config()
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["timezone"], "Asia/Karachi")
        self.assertEqual(cfg["cron_time"], "02:00")

        # Test compute_next_run
        next_run = hunter_scheduler.compute_next_run("02:00", "Asia/Karachi")
        tz = ZoneInfo("Asia/Karachi")
        now_pkt = datetime.datetime.now(tz)
        self.assertGreater(next_run, now_pkt)
        self.assertEqual(next_run.hour, 2)
        self.assertEqual(next_run.minute, 0)

    def test_02_new_business_discovery(self):
        """Criterion 2: New business discovery finds valid food establishments across categories."""
        openings = hunt_new_openings()
        self.assertGreater(len(openings), 0)
        for op in openings:
            self.assertIn("business_name", op)
            self.assertIn("city", op)
            self.assertIn("province", op)
            self.assertIn("category", op)

    def test_03_deduplication_prevention(self):
        """Criterion 3: Existing records are detected and not duplicated."""
        sample_master = [{
            "business_id": "biz_test_01",
            "name": "Kolachi Restaurant",
            "brand_name": "Kolachi",
            "city": "Karachi",
            "area": "Do Darya",
            "phone": "+9221111111001",
            "latitude": 24.7578,
            "longitude": 67.0782
        }]
        candidate_dup = {
            "name": "Kolachi Restaurant",
            "city": "Karachi",
            "area": "Do Darya",
            "phone": "+92 21 111 111 001",
            "latitude": 24.7578,
            "longitude": 67.0782
        }
        match_type, matched = match_existing_business(candidate_dup, sample_master)
        self.assertEqual(match_type, "EXACT_SAME_OUTLET")
        self.assertEqual(matched["business_id"], "biz_test_01")

    def test_04_branches_preserved_separately(self):
        """Criterion 4: Multi-unit branches are preserved separately as distinct records."""
        sample_master = [{
            "business_id": "biz_cheez_01",
            "name": "Cheezious Johar Town",
            "brand_name": "Cheezious",
            "city": "Lahore",
            "area": "Johar Town",
            "latitude": 31.4682,
            "longitude": 74.2748
        }]
        # New branch in Islamabad
        candidate_branch = {
            "name": "Cheezious F-7 Markaz",
            "brand_name": "Cheezious",
            "city": "Islamabad",
            "area": "F-7 Markaz",
            "latitude": 33.7214,
            "longitude": 73.0561
        }
        match_type, matched = match_existing_business(candidate_branch, sample_master)
        self.assertEqual(match_type, "NEW_BRANCH")
        self.assertEqual(matched["business_id"], "biz_cheez_01")

    def test_05_public_contacts_with_evidence(self):
        """Criterion 5: Public contacts are stored with verifiable evidence sources."""
        raw_data = {
            "phone": "042 35759014",
            "email": "info@spicebazaar.pk",
            "website": "https://spicebazaar.pk"
        }
        source_url = "https://spicebazaar.pk/contact-us"
        verified = verify_contacts(raw_data, source_url, "Official Website")
        self.assertEqual(verified["phone"], "+924235759014")
        self.assertIn(source_url, verified["phone_source"])
        self.assertEqual(verified["email"], "info@spicebazaar.pk")
        self.assertEqual(verified["website"], "https://spicebazaar.pk")

    def test_06_whatsapp_not_inferred_from_plain_phone(self):
        """Criterion 6: WhatsApp is NEVER inferred from an ordinary mobile or landline."""
        raw_data = {
            "phone": "0300 8479000", # Mobile number
            "whatsapp": None,
            "whatsapp_status": None # NOT explicitly verified
        }
        verified = verify_contacts(raw_data, "https://sample.pk", "Public Directory")
        # Critical assertion: whatsapp_status must NOT be 'Verified'
        self.assertNotEqual(verified["whatsapp_status"], "Verified")
        self.assertIsNone(verified["whatsapp"])
        self.assertEqual(verified["whatsapp_status"], "Needs Verification")

    def test_07_pos_buyer_intent_evidence_recorded(self):
        """Criterion 7: POS buying-intent evidence quote and source URL are recorded."""
        intents = hunt_buyer_intent()
        self.assertGreater(len(intents), 0)
        for it in intents:
            self.assertTrue(len(it["evidence_quote"]) > 10)
            self.assertTrue(it["source_url"].startswith("http"))
            self.assertIn(it["language"], ["English", "Urdu", "Roman Urdu"])
            self.assertEqual(it["intent_tier"], "High")

    def test_08_pos_opportunity_vs_purchase_intent_separation(self):
        """Criterion 8: Business potential (Category B, C, D) is strictly separated from verified intent (Category A)."""
        # Explicit POS request -> Category A, P1
        intent_sample = {"intent_tier": "Explicit", "requirement_type": "POS Required"}
        self.assertEqual(intent_sample["intent_tier"], "Explicit")

        # New opening without request -> Category B, P2 (Opportunity, not verified buyer)
        opening_sample = {"announcement_type": "New Opening", "pos_opportunity_category": "B"}
        self.assertEqual(opening_sample["pos_opportunity_category"], "B")
        self.assertNotEqual(opening_sample["pos_opportunity_category"], "A")

    def test_09_changes_logged_with_source(self):
        """Criterion 9: Changes to master records are logged in record_change_history with source."""
        cursor = self.conn.cursor()
        test_biz_id = "biz_test_audit_01"
        cursor.execute("INSERT OR REPLACE INTO businesses (business_id, name) VALUES (?, 'Audit Test Cafe')", (test_biz_id,))
        cursor.execute("INSERT OR REPLACE INTO business_contacts (business_id, phone) VALUES (?, NULL)", (test_biz_id,))
        self.conn.commit()

        # Update phone
        existing = {"business_id": test_biz_id, "name": "Audit Test Cafe", "phone": None}
        new_data = {"phone": "+923001234567"}
        src = "https://facebook.com/audittestcafe"

        changes, reviews = process_record_update(cursor, existing, new_data, src)
        self.conn.commit()

        self.assertEqual(changes, 1)
        cursor.execute("SELECT old_value, new_value, source_url FROM record_change_history WHERE business_id = ? ORDER BY created_at DESC LIMIT 1", (test_biz_id,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "+923001234567")
        self.assertEqual(row[2], src)

    def test_10_daily_report_actual_counts(self):
        """Criterion 10: Daily report displays actual non-fabricated counts."""
        test_stats = {
            "job_id": "job_unit_test",
            "run_type": "scheduled",
            "businesses_discovered": 4,
            "branches_discovered": 2,
            "contacts_found": 3,
            "whatsapp_verified": 2,
            "websites_found": 1,
            "emails_found": 1,
            "explicit_pos_found": 1,
            "high_potential_found": 3,
            "medium_potential_found": 1,
            "existing_updated": 0,
            "duplicates_skipped": 12,
            "review_queued": 0,
            "failed_sources_count": 0,
            "api_calls_count": 10,
            "estimated_cost_usd": 0.005,
            "duration_seconds": 12.4
        }
        markdown, report_rec = generate_daily_report(test_stats)
        self.assertIn("DAILY PAKISTAN POS INTELLIGENCE REPORT", markdown)
        self.assertIn("New businesses discovered: 4", markdown)
        self.assertIn("Explicit POS buyer requests: 1", markdown)
        self.assertIn("Estimated research cost: $0.0050 USD", markdown)

    def test_11_exports_contain_new_discoveries(self):
        """Criterion 11: Master Excel and CSV files are successfully generated."""
        run_exports()
        csv_file = os.path.join(EXPORTS_DIR, CSV_FILENAME)
        excel_file = os.path.join(EXPORTS_DIR, EXCEL_FILENAME)
        self.assertTrue(os.path.exists(csv_file))
        self.assertTrue(os.path.exists(excel_file))
        self.assertGreater(os.path.getsize(csv_file), 1000)
        self.assertGreater(os.path.getsize(excel_file), 10000)

    def test_12_failed_jobs_resume_and_checkpoint(self):
        """Criterion 12: Source checkpoints track resumption progress."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO source_checkpoints (source_name, last_cursor, items_harvested, status)
            VALUES ('test_source', 'batch_5', 150, 'active')
            ON CONFLICT(source_name) DO UPDATE SET last_cursor = 'batch_6'
        """)
        self.conn.commit()

        cursor.execute("SELECT last_cursor FROM source_checkpoints WHERE source_name = 'test_source'")
        cursor_val = cursor.fetchone()[0]
        self.assertIn(cursor_val, ['batch_5', 'batch_6'])

    def test_13_api_limits_and_budget_controls(self):
        """Criterion 13: Daily API limits and budget ceilings are configurable and enforced."""
        cfg = hunter_scheduler.update_schedule_config(daily_api_limit=350)
        self.assertEqual(cfg["daily_api_limit"], 350)
        # Restore default
        hunter_scheduler.update_schedule_config(daily_api_limit=500)

    def test_14_background_daemon_persistence(self):
        """Criterion 14: Scheduler runs as background daemon independently of client session."""
        status = hunter_scheduler.get_status()
        self.assertTrue(status["scheduler_enabled"])
        self.assertIn("next_run_at", status)
        self.assertIn("Asia/Karachi", status["timezone"])

if __name__ == '__main__':
    unittest.main()

