"""
Automated Test Suite for Pakistan Food Business Intelligence & POS Platform
Uses standard Python unittest for zero-dependency execution.
"""

import os
import sys
import unittest
import sqlite3
import openpyxl

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_manager import get_connection, DB_PATH
from collector.scoring_engine import evaluate_pos_opportunity, calculate_lead_priority
from collector.deduplicator import is_duplicate_outlet, normalize_phone
from exports.export_generator import EXCEL_FILENAME, CSV_FILENAME, EXPORTS_DIR
from api.server import app

class TestPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_database_tables_exist(self):
        """Verify that all core tables exist in the database."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row['name'] for row in c.fetchall()}
        conn.close()

        required_tables = [
            'businesses', 'business_branches', 'business_categories', 'business_contacts',
            'locations', 'social_profiles', 'websites', 'menus', 'pos_providers',
            'existing_pos_info', 'pos_buyer_intent_signals', 'new_business_announcements',
            'sales_leads', 'research_sources', 'verification_records', 'data_collection_logs',
            'sales_activity_history', 'administrative_regions'
        ]
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Table '{tbl}' is missing from database schema.")

    def test_02_seeded_pos_vendors(self):
        """Verify that established Pakistani POS vendors are seeded."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT vendor_name, product_name FROM pos_providers")
        vendors = [r['vendor_name'] for r in c.fetchall()]
        conn.close()

        self.assertTrue(any("Blink" in v for v in vendors))
        self.assertTrue(any("Oscar" in v for v in vendors))
        self.assertTrue(any("Tossdown" in v for v in vendors))
        self.assertTrue(any("FoodBucket" in v for v in vendors))

    def test_03_scoring_engine_high_opportunity(self):
        """Verify that complex multi-branch restaurants receive High Opportunity score."""
        profile = {
            'category_name': 'Restaurants & Fine Dining',
            'total_branches': 3,
            'dine_in': 1,
            'takeaway': 1,
            'delivery': 1,
            'has_online_ordering': 1,
            'price_range': '$$$',
            'operating_status': 'Open',
            'pos_provider_name': 'Unknown'
        }
        score, reasons = evaluate_pos_opportunity(profile)
        self.assertEqual(score, "High")
        self.assertIn("Multi-branch operations", reasons)

    def test_04_lead_priority_calculation(self):
        """Verify that explicit buyer intent leads receive P1 or P2 priority."""
        p1 = calculate_lead_priority(has_explicit_intent=True, intent_tier='High Intent', opportunity_score='High', has_verified_contact=True, is_new_opening=False)
        self.assertEqual(p1, 'P1')

        p2 = calculate_lead_priority(has_explicit_intent=False, intent_tier='None', opportunity_score='High', has_verified_contact=True, is_new_opening=False)
        self.assertEqual(p2, 'P2')

    def test_05_deduplicator_branch_preservation(self):
        """Verify that different branches in different cities are NOT considered duplicates."""
        outlet1 = {'name': 'Bundu Khan', 'city': 'Lahore', 'latitude': 31.52, 'longitude': 74.35, 'phone': '+9242111444411'}
        outlet2 = {'name': 'Bundu Khan', 'city': 'Rawalpindi', 'latitude': 33.60, 'longitude': 73.06, 'phone': '+9251111444411'}
        
        is_dup, reason = is_duplicate_outlet(outlet1, outlet2)
        self.assertFalse(is_dup)
        self.assertIn("Different cities", reason)

    def test_06_excel_export_24_sheets(self):
        """Verify that the generated Excel workbook contains all 24 required sheets."""
        excel_path = os.path.join(EXPORTS_DIR, EXCEL_FILENAME)
        self.assertTrue(os.path.exists(excel_path), f"Excel file {excel_path} does not exist.")
        
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        self.assertEqual(len(wb.sheetnames), 24, f"Expected 24 sheets, got {len(wb.sheetnames)}")
        self.assertIn("All Businesses", wb.sheetnames)
        self.assertIn("Active POS Buyer Intent", wb.sheetnames)
        self.assertIn("National Market Summary", wb.sheetnames)

    def test_07_api_health_endpoint(self):
        """Verify health endpoint."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')

    def test_08_api_overview_endpoint(self):
        """Verify overview endpoint returns national census baseline and platform metrics."""
        res = self.client.get('/api/overview')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['national_census_baseline']['pbs_total_food_establishments'], 272147)
        self.assertGreaterEqual(data['platform_metrics']['total_discovered'], 40)

    def test_09_api_businesses_filtering(self):
        """Verify filtering businesses by province."""
        res = self.client.get('/api/businesses?province=Punjab')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(data['count'], 0)
        for b in data['results']:
            self.assertIn('Punjab', b['province'])

    def test_10_api_buyer_intent_endpoint(self):
        """Verify buyer intent endpoint returns verified signals with evidence."""
        res = self.client.get('/api/buyer-intent')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data['count'], 10)
        first = data['results'][0]
        self.assertIn(first['intent_tier'], ['Explicit', 'High Intent', 'Medium Intent', 'Early Intent'])
        self.assertTrue(first['source_url'].startswith('http'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
