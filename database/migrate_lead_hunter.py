"""
Database Migration: AI Daily Restaurant Discovery & POS Sales Lead Hunter
Creates hunter_jobs, hunter_schedules, daily_hunter_reports, human_review_queue,
record_change_history, hunter_notifications, source_checkpoints, api_budget_tracking
and enriches businesses table.
"""

import sqlite3
import os
import json
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_intel.db')

def run_migration():
    print(f"Connecting to database at {DB_PATH} ...")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    # 1. Enrich businesses table with hunter columns if missing
    cursor.execute("PRAGMA table_info(businesses)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    alter_cols = [
        ("pos_opportunity_category", "TEXT DEFAULT 'D'"), # A, B, C, D, E, F
        ("is_new_opening", "INTEGER DEFAULT 0"),
        ("opening_timeline", "TEXT DEFAULT 'Established'"), # Just Opened, Opening Soon, Established
        ("branch_count", "INTEGER DEFAULT 1"),
        ("parent_brand_id", "TEXT"),
        ("source_url", "TEXT"),
        ("last_verified_at", "DATETIME")
    ]

    for col_name, col_def in alter_cols:
        if col_name not in existing_cols:
            print(f"Adding column '{col_name}' to 'businesses' table...")
            cursor.execute(f"ALTER TABLE businesses ADD COLUMN {col_name} {col_def}")

    # 2. Enrich pos_buyer_intent_signals if missing
    cursor.execute("PRAGMA table_info(pos_buyer_intent_signals)")
    intent_cols = {row[1] for row in cursor.fetchall()}
    intent_alters = [
        ("required_features", "TEXT"),
        ("evidence_quote", "TEXT"),
        ("language", "TEXT DEFAULT 'English'")
    ]
    for col_name, col_def in intent_alters:
        if col_name not in intent_cols:
            print(f"Adding column '{col_name}' to 'pos_buyer_intent_signals' table...")
            cursor.execute(f"ALTER TABLE pos_buyer_intent_signals ADD COLUMN {col_name} {col_def}")

    # 3. Create hunter_jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hunter_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'running', -- running, completed, failed
            run_type TEXT DEFAULT 'scheduled', -- scheduled, manual
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            duration_seconds REAL DEFAULT 0.0,
            businesses_discovered INTEGER DEFAULT 0,
            branches_discovered INTEGER DEFAULT 0,
            contacts_found INTEGER DEFAULT 0,
            whatsapp_verified INTEGER DEFAULT 0,
            websites_found INTEGER DEFAULT 0,
            emails_found INTEGER DEFAULT 0,
            explicit_pos_found INTEGER DEFAULT 0,
            high_potential_found INTEGER DEFAULT 0,
            medium_potential_found INTEGER DEFAULT 0,
            existing_updated INTEGER DEFAULT 0,
            duplicates_skipped INTEGER DEFAULT 0,
            review_queued INTEGER DEFAULT 0,
            failed_sources_count INTEGER DEFAULT 0,
            api_calls_count INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            summary_markdown TEXT,
            errors_log TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Create hunter_schedules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hunter_schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            enabled INTEGER DEFAULT 1,
            cron_time TEXT DEFAULT '02:00',
            timezone TEXT DEFAULT 'Asia/Karachi',
            frequency TEXT DEFAULT 'Daily',
            rotating_strategy TEXT DEFAULT 'Balanced',
            daily_api_limit INTEGER DEFAULT 500,
            budget_cap_usd REAL DEFAULT 5.0,
            alert_email TEXT DEFAULT 'admin@pakistanfoodpos.com',
            alert_webhook TEXT,
            notify_on_explicit_pos INTEGER DEFAULT 1,
            notify_on_high_opp INTEGER DEFAULT 1,
            notify_on_job_failure INTEGER DEFAULT 1,
            notify_on_budget_alert INTEGER DEFAULT 1,
            last_run_at DATETIME,
            next_run_at DATETIME,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default schedule if table is empty
    cursor.execute("SELECT COUNT(*) FROM hunter_schedules")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO hunter_schedules (
                enabled, cron_time, timezone, frequency, rotating_strategy,
                daily_api_limit, budget_cap_usd, alert_email, notify_on_explicit_pos,
                notify_on_high_opp, notify_on_job_failure, notify_on_budget_alert
            ) VALUES (1, '02:00', 'Asia/Karachi', 'Daily', 'Balanced', 500, 5.0, 'admin@pakistanfoodpos.com', 1, 1, 1, 1)
        """)

    # 5. Create daily_hunter_reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_hunter_reports (
            report_id TEXT PRIMARY KEY,
            job_id TEXT REFERENCES hunter_jobs(job_id),
            report_date TEXT NOT NULL,
            report_title TEXT NOT NULL,
            summary_json TEXT,
            markdown_content TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Create human_review_queue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS human_review_queue (
            review_id TEXT PRIMARY KEY,
            business_id TEXT REFERENCES businesses(business_id),
            business_name TEXT NOT NULL,
            city TEXT,
            field_name TEXT NOT NULL,
            current_value TEXT,
            proposed_value TEXT,
            change_reason TEXT,
            source_url TEXT,
            confidence_score INTEGER DEFAULT 75,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            reviewer_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
    """)

    # 7. Create record_change_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS record_change_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            source_url TEXT,
            change_type TEXT DEFAULT 'auto_update', -- auto_update, human_approved, manual_edit
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. Create hunter_notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hunter_notifications (
            notification_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            alert_type TEXT NOT NULL, -- explicit_pos, high_opportunity, new_opening, new_branch, budget_alert, job_failure
            severity TEXT DEFAULT 'info', -- info, warning, critical, success
            business_id TEXT,
            is_read INTEGER DEFAULT 0,
            meta_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. Create source_checkpoints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_checkpoints (
            checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL UNIQUE,
            last_cursor TEXT,
            last_scanned_at DATETIME,
            items_harvested INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    """)

    # 10. Create api_budget_tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_budget_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_date TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            call_count INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            daily_limit INTEGER DEFAULT 500,
            UNIQUE(tracking_date, provider_name)
        )
    """)

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == '__main__':
    run_migration()

