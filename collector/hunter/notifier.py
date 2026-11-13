"""
Hunter Notifications & Alerting Dispatcher
Generates in-app notifications and external alerts for explicit POS buyers,
high-priority leads, new branch openings, job failures, and budget warnings.
"""

import uuid
import json
import datetime

def record_notification(cursor, title, message, alert_type, severity="info", business_id=None, meta=None):
    """
    Inserts a notification into hunter_notifications.
    """
    notif_id = f"notif_{uuid.uuid4().hex[:12]}"
    meta_json = json.dumps(meta) if meta else None
    cursor.execute("""
        INSERT INTO hunter_notifications (
            notification_id, title, message, alert_type, severity, business_id, meta_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (notif_id, title, message, alert_type, severity, business_id, meta_json))
    return notif_id

def notify_explicit_buyer(cursor, business_name, city, evidence_snippet, business_id=None):
    return record_notification(
        cursor,
        title=f"EXPLICIT POS BUYER: {business_name} ({city})",
        message=f"Public POS software request detected: '{evidence_snippet}'",
        alert_type="explicit_pos",
        severity="critical",
        business_id=business_id
    )

def notify_high_opportunity(cursor, business_name, city, priority="P1", business_id=None):
    return record_notification(
        cursor,
        title=f"High Priority Lead ({priority}): {business_name}",
        message=f"Qualified restaurant lead discovered in {city} with verified contacts.",
        alert_type="high_opportunity",
        severity="warning",
        business_id=business_id
    )

def notify_new_opening(cursor, business_name, city, timeline="Just Opened", business_id=None):
    return record_notification(
        cursor,
        title=f"New Restaurant Opening: {business_name}",
        message=f"Status: {timeline} in {city}. Public contact details verified.",
        alert_type="new_opening",
        severity="info",
        business_id=business_id
    )

def notify_new_branch(cursor, brand_name, city, area=None, business_id=None):
    return record_notification(
        cursor,
        title=f"New Branch Expansion: {brand_name}",
        message=f"New outlet identified in {city} ({area or 'New Area'}).",
        alert_type="new_branch",
        severity="info",
        business_id=business_id
    )

def notify_budget_warning(cursor, provider, current_calls, daily_limit):
    return record_notification(
        cursor,
        title=f"API Quota Alert: {provider}",
        message=f"Usage reached {current_calls}/{daily_limit} calls today.",
        alert_type="budget_alert",
        severity="warning"
    )

def notify_job_failure(cursor, job_id, error_message):
    return record_notification(
        cursor,
        title=f"Daily Lead Hunter Job Failed: {job_id}",
        message=f"Error encountered: {error_message}",
        alert_type="job_failure",
        severity="critical"
    )

