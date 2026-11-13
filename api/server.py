"""
Pakistan Food Business Intelligence & Restaurant POS Sales Platform - API Server
Flask backend delivering high-performance REST endpoints, filtering, CRM management, and export downloads.
"""

import os
import sys
import sqlite3
import json
import datetime
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_manager import get_connection, DB_PATH
from exports.export_generator import run_exports, EXCEL_FILENAME, CSV_FILENAME, EXPORTS_DIR
from collector.orchestrator import run_pipeline
from collector.hunter.scheduler import hunter_scheduler

app = Flask(__name__, static_folder='../static', static_url_path='/static')
app.config['JSON_SORT_KEYS'] = False

# Automatically start 24/7 background scheduler on application boot
try:
    hunter_scheduler.start()
except Exception as _e:
    print(f"Warning starting hunter scheduler: {_e}")

@app.route('/')
def index():
    return send_from_directory('../static', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'platform': 'Pakistan Food Service & Restaurant POS Intelligence Platform',
        'timestamp': datetime.datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DB_PATH) else 'missing'
    })

@app.route('/api/overview')
def get_overview():
    conn = get_connection()
    c = conn.cursor()

    # Core Counts
    c.execute("SELECT COUNT(*) FROM businesses")
    total_discovered = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM businesses WHERE verification_status = 'Verified'")
    total_verified = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM business_contacts WHERE phone IS NOT NULL AND phone != ''")
    total_with_phone = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM business_contacts WHERE whatsapp IS NOT NULL AND whatsapp != '' AND whatsapp_status = 'Verified'")
    total_verified_whatsapp = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM business_contacts WHERE website IS NOT NULL AND website != ''")
    total_with_website = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM business_contacts WHERE email IS NOT NULL AND email != ''")
    total_with_email = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM businesses WHERE is_franchise = 1")
    total_multi_branch = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM businesses WHERE operating_status IN ('Newly Opened', 'New Opening')")
    total_newly_opened = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM businesses WHERE operating_status IN ('Opening Soon', 'Upcoming')")
    total_opening_soon = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM businesses WHERE pos_opportunity_score = 'High'")
    total_high_opportunity = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM pos_buyer_intent_signals")
    total_active_intent = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM existing_pos_info WHERE pos_provider_name NOT IN ('Unknown', 'None')")
    total_existing_pos_users = c.fetchone()[0]
    total_unknown_pos_users = total_discovered - total_existing_pos_users

    # Category Breakdown
    c.execute("""
        SELECT category_name, COUNT(*) as count 
        FROM businesses 
        GROUP BY category_name 
        ORDER BY count DESC
    """)
    category_distribution = [dict(r) for r in c.fetchall()]

    # Province Breakdown
    c.execute("""
        SELECT province, COUNT(*) as count 
        FROM locations 
        GROUP BY province 
        ORDER BY count DESC
    """)
    province_distribution = [dict(r) for r in c.fetchall()]

    # Lead Priority Breakdown
    c.execute("""
        SELECT lead_priority, COUNT(*) as count 
        FROM businesses 
        GROUP BY lead_priority 
        ORDER BY lead_priority ASC
    """)
    lead_priority_distribution = [dict(r) for r in c.fetchall()]

    # Pipeline Stage Breakdown
    c.execute("""
        SELECT pipeline_stage, COUNT(*) as count 
        FROM sales_leads 
        GROUP BY pipeline_stage 
        ORDER BY count DESC
    """)
    pipeline_distribution = [dict(r) for r in c.fetchall()]

    conn.close()

    return jsonify({
        'national_census_baseline': {
            'pbs_total_food_establishments': 272147,
            'micro_establishments_less_10_employees': 254022,
            'commercial_establishments_10_plus_employees': 18125,
            'fbr_pos_integrated_entities': 1212,
            'fbr_pos_integrated_branches': 1908,
            'tam_total_addressable_market': 272147,
            'sam_serviceable_available_market': 72500,
            'som_serviceable_obtainable_market': 16500,
            'market_digitization_white_space_pct': 97.4,
            'total_employment_in_sector': 1150525,
            'total_economic_units_all_sectors': 7140000,
            'pbs_provincial_tables': [
                {'province': 'Punjab', 'establishments': 160076, 'pct': 58.82, 'employment': 676500},
                {'province': 'Sindh', 'establishments': 58435, 'pct': 21.47, 'employment': 247100},
                {'province': 'Khyber Pakhtunkhwa', 'establishments': 35337, 'pct': 12.98, 'employment': 149500},
                {'province': 'Balochistan', 'establishments': 12200, 'pct': 4.48, 'employment': 51500},
                {'province': 'Islamabad Capital Territory', 'establishments': 6099, 'pct': 2.24, 'employment': 25925}
            ]
        },
        'platform_metrics': {
            'total_discovered': total_discovered,
            'total_verified': total_verified,
            'total_with_phone': total_with_phone,
            'total_verified_whatsapp': total_verified_whatsapp,
            'total_with_website': total_with_website,
            'total_with_email': total_with_email,
            'total_multi_branch': total_multi_branch,
            'total_newly_opened': total_newly_opened,
            'total_opening_soon': total_opening_soon,
            'total_high_opportunity': total_high_opportunity,
            'total_active_intent': total_active_intent,
            'total_existing_pos_users': total_existing_pos_users,
            'total_unknown_pos_users': total_unknown_pos_users
        },
        'distributions': {
            'categories': category_distribution,
            'provinces': province_distribution,
            'lead_priorities': lead_priority_distribution,
            'pipeline_stages': pipeline_distribution
        }
    })

@app.route('/api/businesses')
def get_businesses():
    conn = get_connection()
    c = conn.cursor()

    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    province = request.args.get('province', '').strip()
    city = request.args.get('city', '').strip()
    priority = request.args.get('priority', '').strip()
    opportunity = request.args.get('opportunity', '').strip()
    status = request.args.get('status', '').strip()
    has_whatsapp = request.args.get('has_whatsapp', '').strip()
    has_intent = request.args.get('has_intent', '').strip()
    limit = min(int(request.args.get('limit', 100)), 5000)
    page = int(request.args.get('page', 1))
    offset = int(request.args.get('offset', (page - 1) * limit if page > 1 else 0))

    where_clauses = ["1=1"]
    params = []

    if search:
        where_clauses.append("(b.name LIKE ? OR b.brand_name LIKE ? OR l.city LIKE ? OR l.area LIKE ? OR c.phone LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    if category:
        where_clauses.append("b.category_name LIKE ?")
        params.append(f"%{category}%")

    if province:
        where_clauses.append("l.province LIKE ?")
        params.append(f"%{province}%")

    if city:
        where_clauses.append("l.city LIKE ?")
        params.append(f"%{city}%")

    if priority:
        where_clauses.append("b.lead_priority = ?")
        params.append(priority)

    if opportunity:
        where_clauses.append("b.pos_opportunity_score = ?")
        params.append(opportunity)

    if status:
        where_clauses.append("b.operating_status LIKE ?")
        params.append(f"%{status}%")

    if has_whatsapp == '1':
        where_clauses.append("c.whatsapp IS NOT NULL AND c.whatsapp != ''")

    if has_intent == '1':
        where_clauses.append("b.business_id IN (SELECT business_id FROM pos_buyer_intent_signals WHERE business_id IS NOT NULL)")

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            b.business_id, b.name, b.brand_name, b.category_name, b.subcategory,
            b.operating_status, b.business_size, b.verification_status, b.data_confidence,
            b.pos_opportunity_score, b.pos_opportunity_reasons, b.lead_priority,
            l.province, l.district, l.city, l.area, l.market, l.full_address,
            l.latitude, l.longitude, l.google_maps_url,
            c.phone, c.whatsapp, c.whatsapp_status, c.whatsapp_link, c.email, c.website,
            m.price_range, m.dine_in, m.takeaway, m.delivery,
            e.pos_provider_name, e.is_pos_verified,
            s.pipeline_stage, s.assigned_rep, s.notes
        FROM businesses b
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        LEFT JOIN menus m ON b.business_id = m.business_id
        LEFT JOIN existing_pos_info e ON b.business_id = e.business_id
        LEFT JOIN sales_leads s ON b.business_id = s.business_id
        WHERE {where_sql}
        ORDER BY b.lead_priority ASC, b.name ASC
        LIMIT ? OFFSET ?
    """
    c.execute(query, params + [limit, offset])
    rows = [dict(r) for r in c.fetchall()]

    if len(where_clauses) == 1:
        c.execute("SELECT COUNT(*) FROM businesses")
        total_count = c.fetchone()[0]
    else:
        c.execute(f"SELECT COUNT(*) FROM businesses b LEFT JOIN locations l ON b.business_id = l.business_id LEFT JOIN business_contacts c ON b.business_id = c.business_id WHERE {where_sql}", params)
        total_count = c.fetchone()[0]

    conn.close()

    return jsonify({
        'total': total_count,
        'count': len(rows),
        'limit': limit,
        'offset': offset,
        'page': (offset // limit) + 1,
        'total_pages': max(1, (total_count + limit - 1) // limit),
        'results': rows
    })

@app.route('/api/businesses/<business_id>')
def get_business_detail(business_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT b.*, l.province, l.division, l.district, l.tehsil, l.city, l.area, l.market,
               l.full_address, l.nearby_landmark, l.postal_code, l.latitude, l.longitude, l.google_maps_url,
               c.phone, c.alternative_phone, c.whatsapp, c.whatsapp_status, c.whatsapp_source, c.whatsapp_link,
               c.email, c.support_email, c.website, c.contact_page_url, c.online_ordering_url, c.menu_url,
               m.price_range, m.cuisines, m.opening_hours, m.closing_hours, m.dine_in, m.takeaway, m.delivery,
               m.table_reservations, m.online_ordering, m.seating_capacity, m.number_of_employees,
               e.pos_provider_name, e.is_pos_verified, e.evidence_source, e.notes as pos_notes,
               s.lead_id, s.pipeline_stage, s.assigned_rep, s.last_contact_date, s.next_followup_date, s.notes as sales_notes
        FROM businesses b
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        LEFT JOIN menus m ON b.business_id = m.business_id
        LEFT JOIN existing_pos_info e ON b.business_id = e.business_id
        LEFT JOIN sales_leads s ON b.business_id = s.business_id
        WHERE b.business_id = ?
    """, (business_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Business not found'}), 404

    data = dict(row)

    # Branches
    c.execute("SELECT * FROM business_branches WHERE business_id = ?", (business_id,))
    data['branches'] = [dict(r) for r in c.fetchall()]

    # Socials
    c.execute("SELECT * FROM social_profiles WHERE business_id = ?", (business_id,))
    data['social_profiles'] = [dict(r) for r in c.fetchall()]

    # Buyer Intent Signals
    c.execute("SELECT * FROM pos_buyer_intent_signals WHERE business_id = ?", (business_id,))
    data['buyer_intent'] = [dict(r) for r in c.fetchall()]

    # Announcements
    c.execute("SELECT * FROM new_business_announcements WHERE business_id = ?", (business_id,))
    data['announcements'] = [dict(r) for r in c.fetchall()]

    # Sales Activities
    c.execute("SELECT * FROM sales_activity_history WHERE business_id = ? ORDER BY timestamp DESC", (business_id,))
    data['activity_history'] = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify(data)

@app.route('/api/buyer-intent')
def get_buyer_intent():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM pos_buyer_intent_signals 
        ORDER BY lead_priority ASC, original_post_date DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'count': len(rows), 'results': rows})

@app.route('/api/new-openings')
def get_new_openings():
    opening_type = request.args.get('type', '').strip().lower()
    conn = get_connection()
    c = conn.cursor()

    # Pre-calculate category counts across all announcements
    c.execute("""
        SELECT 
            SUM(CASE WHEN announcement_type IN ('Newly Opened', 'Brand Launch', 'New Brand Launch', 'Grand Launch Announcement', 'New Opening Announcement') THEN 1 ELSE 0 END) as opened_count,
            SUM(CASE WHEN announcement_type = 'Opening Soon' THEN 1 ELSE 0 END) as soon_count,
            SUM(CASE WHEN announcement_type IN ('New Branch', 'New Branch Expansion') THEN 1 ELSE 0 END) as branch_count,
            COUNT(*) as total_count
        FROM new_business_announcements
    """)
    stats = c.fetchone()
    opened_count = stats['opened_count'] or 0
    soon_count = stats['soon_count'] or 0
    branch_count = stats['branch_count'] or 0
    total_count = stats['total_count'] or 0

    base_query = """
        SELECT a.*, b.pos_opportunity_score, b.lead_priority, c.whatsapp, c.whatsapp_link, c.email
        FROM new_business_announcements a
        LEFT JOIN businesses b ON a.business_id = b.business_id
        LEFT JOIN business_contacts c ON a.business_id = c.business_id
    """

    if opening_type == 'opened':
        c.execute(base_query + """
            WHERE a.announcement_type IN ('Newly Opened', 'Brand Launch', 'New Brand Launch', 'Grand Launch Announcement', 'New Opening Announcement')
            ORDER BY a.announcement_date DESC
        """)
    elif opening_type == 'soon':
        c.execute(base_query + """
            WHERE a.announcement_type = 'Opening Soon'
            ORDER BY a.announcement_date DESC
        """)
    elif opening_type == 'branch':
        c.execute(base_query + """
            WHERE a.announcement_type IN ('New Branch', 'New Branch Expansion')
            ORDER BY a.announcement_date DESC
        """)
    else:
        c.execute(base_query + " ORDER BY a.announcement_date DESC")

    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({
        'count': len(rows),
        'results': rows,
        'opened_count': opened_count,
        'soon_count': soon_count,
        'branch_count': branch_count,
        'total': total_count
    })

@app.route('/api/pos-vendors')
def get_pos_vendors():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM pos_providers ORDER BY provider_id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'count': len(rows), 'results': rows})

@app.route('/api/locations')
def get_locations():
    conn = get_connection()
    c = conn.cursor()
    # Administrative Regions
    c.execute("SELECT * FROM administrative_regions ORDER BY province ASC, city ASC")
    regions = [dict(r) for r in c.fetchall()]

    # Geo Map Markers (all businesses with lat/lon)
    c.execute("""
        SELECT b.business_id, b.name, b.category_name, b.lead_priority, b.pos_opportunity_score,
               l.city, l.area, l.latitude, l.longitude, c.phone, c.whatsapp_link
        FROM businesses b
        JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
        ORDER BY b.lead_priority ASC
        LIMIT 1500
    """)
    markers = [dict(r) for r in c.fetchall()]
    conn.close()

    return jsonify({
        'regions': regions,
        'markers': markers
    })

@app.route('/api/crm/leads')
def get_crm_leads():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, b.category_name, l.city, l.province, c.phone, c.whatsapp, c.whatsapp_link, c.email
        FROM sales_leads s
        JOIN businesses b ON s.business_id = b.business_id
        LEFT JOIN locations l ON s.business_id = l.business_id
        LEFT JOIN business_contacts c ON s.business_id = c.business_id
        ORDER BY s.lead_priority ASC, s.updated_at DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'count': len(rows), 'results': rows})

@app.route('/api/crm/lead/<business_id>', methods=['POST'])
def update_crm_lead(business_id):
    payload = request.json or {}
    stage = payload.get('pipeline_stage')
    assigned_rep = payload.get('assigned_rep')
    notes = payload.get('notes')
    next_followup = payload.get('next_followup_date')

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE sales_leads
        SET pipeline_stage = COALESCE(?, pipeline_stage),
            assigned_rep = COALESCE(?, assigned_rep),
            notes = COALESCE(?, notes),
            next_followup_date = COALESCE(?, next_followup_date),
            last_contact_date = DATE('now'),
            updated_at = CURRENT_TIMESTAMP
        WHERE business_id = ?
    """, (stage, assigned_rep, notes, next_followup, business_id))

    # Add activity
    c.execute("""
        INSERT INTO sales_activity_history (business_id, activity_type, summary, agent_name, outcome)
        VALUES (?, ?, ?, ?, ?)
    """, (business_id, 'Status Update', f"Stage changed to '{stage}'. Notes: {notes or 'N/A'}", assigned_rep or 'Sales Manager', 'Updated'))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Lead updated successfully'})

@app.route('/api/export/excel')
def download_excel():
    excel_path = os.path.join(EXPORTS_DIR, EXCEL_FILENAME)
    if not os.path.exists(excel_path):
        run_exports()
    return send_file(
        excel_path,
        as_attachment=True,
        download_name=EXCEL_FILENAME,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/api/export/csv')
def download_csv():
    csv_path = os.path.join(EXPORTS_DIR, CSV_FILENAME)
    if not os.path.exists(csv_path):
        run_exports()
    return send_file(
        csv_path,
        as_attachment=True,
        download_name=CSV_FILENAME,
        mimetype='text/csv'
    )

@app.route('/api/collector/run', methods=['POST'])
def trigger_collector():
    data = request.json or {}
    targets = data.get('targets', 3)
    res = run_pipeline(include_live_osm=True, osm_limit_targets=targets)
    # Refresh exports automatically
    run_exports()
    return jsonify({'success': True, 'result': res})

@app.route('/api/collector/status')
def get_collector_status():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM data_collection_logs ORDER BY start_time DESC LIMIT 10")
    logs = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'logs': logs})

# ============================================================================
# MODULE: AI DAILY RESTAURANT DISCOVERY & POS SALES LEAD HUNTER ENDPOINTS
# ============================================================================

@app.route('/api/hunter/status')
def get_hunter_status():
    return jsonify(hunter_scheduler.get_status())

@app.route('/api/hunter/run-now', methods=['POST'])
def trigger_hunter_now():
    res = hunter_scheduler.trigger_manual_run(run_type="manual")
    return jsonify(res)

@app.route('/api/hunter/config', methods=['GET', 'POST'])
def hunter_config():
    if request.method == 'POST':
        data = request.json or {}
        updated = hunter_scheduler.update_schedule_config(
            cron_time=data.get('cron_time'),
            timezone=data.get('timezone'),
            enabled=data.get('enabled'),
            daily_api_limit=data.get('daily_api_limit'),
            alert_email=data.get('alert_email')
        )
        return jsonify({'success': True, 'config': updated})
    return jsonify(hunter_scheduler.get_schedule_config())

@app.route('/api/hunter/jobs')
def get_hunter_jobs():
    limit = int(request.args.get('limit', 25))
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM hunter_jobs
        ORDER BY start_time DESC LIMIT ?
    """, (limit,))
    jobs = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'jobs': jobs})

@app.route('/api/hunter/reports')
def get_hunter_reports():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT report_id, job_id, report_date, report_title, summary_json, created_at
        FROM daily_hunter_reports
        ORDER BY created_at DESC LIMIT 30
    """)
    reports = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'reports': reports})

@app.route('/api/hunter/reports/latest')
def get_latest_hunter_report():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT report_id, job_id, report_date, report_title, summary_json, markdown_content, created_at
        FROM daily_hunter_reports
        ORDER BY created_at DESC LIMIT 1
    """)
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'found': False, 'message': 'No daily reports generated yet.'}), 404
    return jsonify({'found': True, 'report': dict(row)})

@app.route('/api/hunter/reports/<report_id>')
def get_hunter_report_by_id(report_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_hunter_reports WHERE report_id = ?", (report_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify(dict(row))

@app.route('/api/hunter/buyer-intent')
def get_buyer_intent_leads():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, b.name as business_name, l.city, l.area, l.province,
               c.phone, c.whatsapp, c.whatsapp_link, c.website
        FROM pos_buyer_intent_signals s
        JOIN businesses b ON s.business_id = b.business_id
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        ORDER BY s.discovered_date DESC
    """)
    intents = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'buyer_intents': intents, 'total': len(intents)})

@app.route('/api/hunter/review-queue')
def get_review_queue():
    status = request.args.get('status', 'pending')
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM human_review_queue WHERE status = ? ORDER BY created_at DESC", (status,))
    items = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'items': items, 'total': len(items)})

@app.route('/api/hunter/review-queue/<review_id>/resolve', methods=['POST'])
def resolve_review_item(review_id):
    data = request.json or {}
    action = data.get('action', 'approve')
    notes = data.get('notes', '')

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM human_review_queue WHERE review_id = ?", (review_id,))
    item = c.fetchone()
    if not item:
        conn.close()
        return jsonify({'error': 'Review item not found'}), 404

    b_id = item['business_id']
    field = item['field_name']
    proposed_val = item['proposed_value']
    old_val = item['current_value']
    src_url = item['source_url']
    new_status = 'approved' if action == 'approve' else 'rejected'

    if action == 'approve':
        if field in ['phone', 'whatsapp', 'email', 'website']:
            c.execute(f"UPDATE business_contacts SET {field} = ? WHERE business_id = ?", (proposed_val, b_id))
        elif field in ['operating_status', 'price_range', 'name']:
            c.execute(f"UPDATE businesses SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE business_id = ?", (proposed_val, b_id))

        c.execute("""
            INSERT INTO record_change_history (business_id, field_name, old_value, new_value, source_url, change_type)
            VALUES (?, ?, ?, ?, ?, 'human_approved')
        """, (b_id, field, old_val, proposed_val, src_url))

    c.execute("""
        UPDATE human_review_queue SET
            status = ?,
            reviewer_notes = ?,
            resolved_at = CURRENT_TIMESTAMP
        WHERE review_id = ?
    """, (new_status, notes, review_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'review_id': review_id, 'status': new_status})

@app.route('/api/hunter/notifications')
def get_hunter_notifications():
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM hunter_notifications "
    if unread_only:
        query += "WHERE is_read = 0 "
    query += "ORDER BY created_at DESC LIMIT 50"
    c.execute(query)
    notifs = [dict(r) for r in c.fetchall()]
    c.execute("SELECT COUNT(*) FROM hunter_notifications WHERE is_read = 0")
    unread_count = c.fetchone()[0]
    conn.close()
    return jsonify({'notifications': notifs, 'unread_count': unread_count})

@app.route('/api/hunter/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    conn = get_connection()
    conn.execute("UPDATE hunter_notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Pakistan Food Intel & POS Sales Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
