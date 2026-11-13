"""
Automated 24/7 Scheduler for AI Lead Hunter
Manages continuous background execution on the server (even when laptop/client is off).
Default Schedule: Daily at 02:00 AM Pakistan Standard Time (Asia/Karachi).
Admins can dynamically modify the schedule time, timezone, and daily limits via the DB/API.
Supports instant non-blocking manual execution via the 'Run Now' action.
"""

import threading
import time
import datetime
from zoneinfo import ZoneInfo
import traceback
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from database.db_manager import get_connection
from collector.hunter.daily_hunter_engine import execute_lead_hunter_job

class HunterScheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(HunterScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.is_running = False
        self.current_job_id = None
        self.thread = None
        self.stop_event = threading.Event()
        self.job_lock = threading.Lock()

    def get_schedule_config(self):
        """Reads schedule and quota settings from the database."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT schedule_id, enabled, cron_time, timezone, frequency,
                   rotating_strategy, daily_api_limit, budget_cap_usd,
                   alert_email, alert_webhook, last_run_at, next_run_at
            FROM hunter_schedules
            ORDER BY schedule_id DESC LIMIT 1
        """)
        row = c.fetchone()
        conn.close()

        if row:
            return {
                "schedule_id": row["schedule_id"],
                "enabled": bool(row["enabled"]),
                "cron_time": row["cron_time"] or "02:00",
                "timezone": row["timezone"] or "Asia/Karachi",
                "frequency": row["frequency"] or "Daily",
                "rotating_strategy": row["rotating_strategy"] or "Balanced",
                "daily_api_limit": row["daily_api_limit"] or 500,
                "budget_cap_usd": row["budget_cap_usd"] or 5.0,
                "alert_email": row["alert_email"],
                "alert_webhook": row["alert_webhook"],
                "last_run_at": row["last_run_at"],
                "next_run_at": row["next_run_at"]
            }
        return {
            "schedule_id": 1, "enabled": True, "cron_time": "02:00",
            "timezone": "Asia/Karachi", "frequency": "Daily",
            "rotating_strategy": "Balanced", "daily_api_limit": 500,
            "budget_cap_usd": 5.0, "alert_email": "admin@pakistanfoodpos.com",
            "last_run_at": None, "next_run_at": None
        }

    def compute_next_run(self, cron_time="02:00", tz_str="Asia/Karachi"):
        """Calculates the upcoming scheduled run time in the specified timezone."""
        try:
            tz = ZoneInfo(tz_str)
        except Exception:
            tz = ZoneInfo("Asia/Karachi")

        now = datetime.datetime.now(tz)
        parts = cron_time.split(":")
        target_hour = int(parts[0]) if len(parts) > 0 else 2
        target_minute = int(parts[1]) if len(parts) > 1 else 0

        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if target_time <= now:
            # Already passed today, schedule for tomorrow
            target_time += datetime.timedelta(days=1)
        return target_time

    def update_schedule_config(self, cron_time=None, timezone=None, enabled=None, daily_api_limit=None, alert_email=None):
        """Updates schedule settings in database and recomputes next run."""
        conn = get_connection()
        c = conn.cursor()

        curr = self.get_schedule_config()
        new_cron = cron_time if cron_time is not None else curr["cron_time"]
        new_tz = timezone if timezone is not None else curr["timezone"]
        new_enabled = enabled if enabled is not None else (1 if curr["enabled"] else 0)
        new_limit = daily_api_limit if daily_api_limit is not None else curr["daily_api_limit"]
        new_email = alert_email if alert_email is not None else curr["alert_email"]

        next_run = self.compute_next_run(new_cron, new_tz)

        c.execute("""
            UPDATE hunter_schedules SET
                cron_time = ?,
                timezone = ?,
                enabled = ?,
                daily_api_limit = ?,
                alert_email = ?,
                next_run_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE schedule_id = ?
        """, (new_cron, new_tz, 1 if new_enabled else 0, new_limit, new_email, next_run.isoformat(), curr["schedule_id"]))
        conn.commit()
        conn.close()
        return self.get_schedule_config()

    def start(self):
        """Starts the background scheduler loop thread."""
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._scheduler_loop, name="HunterSchedulerDaemon", daemon=True)
        self.thread.start()
        print("AI Daily Lead Hunter 24/7 Scheduler daemon started.")

    def stop(self):
        """Signals the background loop to terminate gracefully."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        print("AI Daily Lead Hunter Scheduler stopped.")

    def _scheduler_loop(self):
        """Periodic background evaluation checking if 2:00 AM PKT has arrived."""
        last_executed_day = None

        while not self.stop_event.is_set():
            try:
                cfg = self.get_schedule_config()
                if not cfg["enabled"]:
                    time.sleep(15)
                    continue

                tz = ZoneInfo(cfg["timezone"])
                now = datetime.datetime.now(tz)
                target_parts = cfg["cron_time"].split(":")
                t_hour = int(target_parts[0])
                t_min = int(target_parts[1]) if len(target_parts) > 1 else 0

                # Check if it's the target scheduled minute
                if now.hour == t_hour and now.minute == t_min:
                    today_tag = now.strftime("%Y-%m-%d")
                    if last_executed_day != today_tag:
                        print(f"\n[SCHEDULER TRIGGER] Scheduled execution time reached ({cfg['cron_time']} {cfg['timezone']}).")
                        last_executed_day = today_tag
                        self.trigger_manual_run(run_type="scheduled")

                # Update next run in DB periodically
                next_run = self.compute_next_run(cfg["cron_time"], cfg["timezone"])
                conn = get_connection()
                conn.execute("UPDATE hunter_schedules SET next_run_at = ? WHERE schedule_id = ?",
                             (next_run.isoformat(), cfg["schedule_id"]))
                conn.commit()
                conn.close()

            except Exception as e:
                print(f"[Scheduler Loop Error]: {e}")

            # Sleep 25 seconds between clock checks
            time.sleep(25)

    def trigger_manual_run(self, run_type="manual"):
        """
        Triggers an immediate research cycle asynchronously.
        Guarantees that overlapping runs do not collide.
        """
        if self.is_running:
            return {
                "success": False,
                "message": f"A lead hunting job is already actively running (Job ID: {self.current_job_id}). Please wait for it to complete.",
                "is_running": True,
                "current_job_id": self.current_job_id
            }

        def _worker():
            with self.job_lock:
                self.is_running = True
                try:
                    stats, report = execute_lead_hunter_job(run_type=run_type, max_osm_cities=3, limit_per_city=15)
                    self.current_job_id = None
                except Exception as ex:
                    print(f"Background Hunter Job Error: {ex}")
                finally:
                    self.is_running = False

        worker_thread = threading.Thread(target=_worker, name="LeadHunterJobRunner", daemon=True)
        worker_thread.start()

        return {
            "success": True,
            "message": "AI Daily Restaurant Discovery & POS Sales Lead Hunter job launched successfully in background.",
            "is_running": True
        }

    def get_status(self):
        """Returns the current scheduler telemetry for the dashboard UI."""
        cfg = self.get_schedule_config()
        conn = get_connection()
        c = conn.cursor()

        c.execute("""
            SELECT job_id, status, run_type, start_time, end_time, duration_seconds,
                   businesses_discovered, branches_discovered, explicit_pos_found,
                   high_potential_found, contacts_found, whatsapp_verified
            FROM hunter_jobs
            ORDER BY start_time DESC LIMIT 1
        """)
        last_job = dict(c.fetchone()) if c.fetchone else None
        conn.close()

        next_run = self.compute_next_run(cfg["cron_time"], cfg["timezone"])

        return {
            "scheduler_enabled": cfg["enabled"],
            "schedule_time": cfg["cron_time"],
            "timezone": cfg["timezone"],
            "next_run_at": next_run.strftime("%Y-%m-%d %H:%M:%S PKT"),
            "is_job_active": self.is_running,
            "last_job": last_job,
            "daily_api_limit": cfg["daily_api_limit"],
            "budget_cap_usd": cfg["budget_cap_usd"]
        }

# Global singleton
hunter_scheduler = HunterScheduler()

