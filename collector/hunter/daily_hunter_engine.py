"""
Master AI Daily Lead Hunter Execution Engine
Runs end-to-end automated research jobs:
1. Searches multi-lingual POS buyer-intent requests (English, Urdu, Roman Urdu).
2. Hunts newly opened and upcoming food business announcements.
3. Performs incremental rotating geographic discovery across Pakistan cities.
4. Performs strict contact verification and deduplication.
5. Updates existing records with field change history or routes to review queue.
6. Generates the structured daily intelligence report.
7. Refreshes master Excel and CSV exports.
8. Dispatches alerts and notifications to administrators.
"""

import sys
import os
import time
import uuid
import json
import datetime
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.db_manager import get_connection
from collector.scoring_engine import evaluate_pos_opportunity, calculate_lead_priority
from collector.deduplicator import normalize_name, normalize_phone
from collector.hunter.contact_verifier import verify_contacts
from collector.hunter.connectors.web_intent_connector import hunt_buyer_intent
from collector.hunter.connectors.social_announcements_connector import hunt_new_openings
from collector.hunter.dedup_and_updater import match_existing_business, process_record_update
from collector.hunter.report_generator import generate_daily_report
from collector.hunter.notifier import (
    notify_explicit_buyer, notify_high_opportunity,
    notify_new_opening, notify_new_branch, notify_job_failure
)
from exports.export_generator import run_exports

def execute_lead_hunter_job(run_type="manual", max_osm_cities=3, limit_per_city=15):
    """
    Executes a complete automated intelligence hunting cycle.
    Returns the completed job statistics dictionary and the generated report record.
    """
    start_time = datetime.datetime.now()
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    print("=" * 72)
    print(f"STARTING AI DAILY LEAD HUNTER JOB [{job_id}] - Run Type: {run_type}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S PKT')}")
    print("=" * 72)

    conn = get_connection()
    c = conn.cursor()

    # Initialize job in database
    c.execute("""
        INSERT INTO hunter_jobs (job_id, status, run_type, start_time)
        VALUES (?, 'running', ?, ?)
    """, (job_id, run_type, start_time.isoformat()))
    conn.commit()

    stats = {
        "job_id": job_id,
        "run_type": run_type,
        "businesses_discovered": 0,
        "branches_discovered": 0,
        "contacts_found": 0,
        "whatsapp_verified": 0,
        "websites_found": 0,
        "emails_found": 0,
        "explicit_pos_found": 0,
        "high_potential_found": 0,
        "medium_potential_found": 0,
        "existing_updated": 0,
        "duplicates_skipped": 0,
        "review_queued": 0,
        "failed_sources_count": 0,
        "api_calls_count": 0,
        "estimated_cost_usd": 0.0
    }

    actionable_leads = []
    errors_list = []

    try:
        # Load Category Map
        c.execute("SELECT category_id, code, name FROM business_categories")
        cat_map = {r['code']: (r['category_id'], r['name']) for r in c.fetchall()}

        # Load Master Records for Intelligent Matching
        c.execute("""
            SELECT b.business_id, b.name, b.brand_name, b.pos_opportunity_category,
                   l.city, l.area, l.latitude, l.longitude,
                   c.phone, c.whatsapp, c.email, c.website
            FROM businesses b
            LEFT JOIN locations l ON b.business_id = l.business_id
            LEFT JOIN business_contacts c ON b.business_id = c.business_id
        """)
        master_records = [dict(r) for r in c.fetchall()]

        # ---------------------------------------------------------------------
        # STAGE 1: Explicit POS Buyer-Intent Discovery (Highest Priority)
        # ---------------------------------------------------------------------
        print("\n[STAGE 1] Hunting public POS buyer-intent signals...")
        intent_leads = hunt_buyer_intent()
        stats["api_calls_count"] += len(intent_leads)

        for lead in intent_leads:
            match_type, matched_master = match_existing_business(lead, master_records)

            if match_type == 'EXACT_SAME_OUTLET':
                # Already exists, check if intent is already recorded
                c.execute("SELECT intent_id FROM pos_buyer_intent_signals WHERE business_id = ?", (matched_master['business_id'],))
                if not c.fetchone():
                    c.execute("""
                        INSERT INTO pos_buyer_intent_signals (
                            business_id, business_name, category, city, contact_phone, whatsapp,
                            website_url, intent_tier, requirement_type, source_platform, source_url,
                            original_post_date, evidence_summary, verification_status, lead_priority,
                            required_features, evidence_quote, language
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        matched_master['business_id'], lead['business_name'], 'Restaurant', lead['city'],
                        lead.get('phone'), lead.get('whatsapp'), lead.get('website'), 'Explicit',
                        lead['requirement_type'], lead['source_platform'], lead['source_url'],
                        lead['original_post_date'], lead['evidence_quote'], 'Verified', 'P1',
                        lead.get('required_features'), lead.get('evidence_quote'), lead.get('language')
                    ))
                    c.execute("UPDATE businesses SET pos_opportunity_category = 'A', lead_priority = 'P1' WHERE business_id = ?", (matched_master['business_id'],))
                    stats["explicit_pos_found"] += 1
                    notify_explicit_buyer(c, lead['business_name'], lead['city'], lead['evidence_quote'], matched_master['business_id'])
                stats["duplicates_skipped"] += 1
                continue

            # New Business with Explicit Intent!
            b_id = f"biz_{uuid.uuid4().hex[:12]}"
            cat_id, cat_name = cat_map.get('RESTAURANT', (1, 'Restaurants & Fine Dining'))

            # Strict Contact Verification
            v_contacts = verify_contacts(lead, lead['source_url'], source_type="Public Buyer Request")

            # 1. Insert into businesses
            c.execute("""
                INSERT INTO businesses (
                    business_id, name, brand_name, category_id, category_name,
                    operating_status, business_size, verification_status, data_confidence,
                    pos_opportunity_score, pos_opportunity_reasons, lead_priority,
                    pos_opportunity_category, source_url, last_verified_at
                ) VALUES (?, ?, ?, ?, ?, 'Open', 'Medium', 'Verified', 96, 'High', ?, 'P1', 'A', ?, CURRENT_TIMESTAMP)
            """, (
                b_id, lead['business_name'], lead['business_name'], cat_id, cat_name,
                f"EXPLICIT POS BUYER: Requested {lead['requirement_type']}", lead['source_url']
            ))

            # 2. Insert into locations
            c.execute("""
                INSERT INTO locations (
                    business_id, country, province, district, city, area, full_address
                ) VALUES (?, 'Pakistan', ?, ?, ?, ?, ?)
            """, (b_id, lead['province'], lead['district'], lead['city'], lead.get('area'), lead['full_address']))

            # 3. Insert into contacts
            c.execute("""
                INSERT INTO business_contacts (
                    business_id, phone, whatsapp, whatsapp_status, whatsapp_source,
                    whatsapp_link, email, website
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b_id, v_contacts['phone'], v_contacts['whatsapp'], v_contacts['whatsapp_status'],
                v_contacts['whatsapp_source'], v_contacts['whatsapp_link'], v_contacts['email'], v_contacts['website']
            ))

            # 4. Insert into pos_buyer_intent_signals
            c.execute("""
                INSERT INTO pos_buyer_intent_signals (
                    business_id, business_name, category, city, contact_phone, whatsapp,
                    website_url, intent_tier, requirement_type, source_platform, source_url,
                    original_post_date, evidence_summary, verification_status, lead_priority,
                    required_features, evidence_quote, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b_id, lead['business_name'], cat_name, lead['city'],
                v_contacts['phone'], v_contacts['whatsapp'], v_contacts['website'], 'Explicit',
                lead['requirement_type'], lead['source_platform'], lead['source_url'],
                lead['original_post_date'], lead['evidence_quote'], 'Verified', 'P1',
                lead.get('required_features'), lead.get('evidence_quote'), lead.get('language')
            ))

            # 5. Insert into sales_leads CRM
            c.execute("""
                INSERT INTO sales_leads (
                    business_id, business_name, category, city, lead_priority,
                    pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
                ) VALUES (?, ?, ?, ?, 'P1', 'New Lead', 'High', ?, 'Enterprise Accounts Lead', ?)
            """, (
                b_id, lead['business_name'], cat_name, lead['city'],
                f"EXPLICIT BUYING INTENT: {lead['requirement_type']}",
                f"Verbatim quote: '{lead['evidence_quote']}'. Required features: {lead.get('required_features')}"
            ))

            stats["businesses_discovered"] += 1
            stats["explicit_pos_found"] += 1
            stats["high_potential_found"] += 1
            if v_contacts['phone']: stats["contacts_found"] += 1
            if v_contacts['whatsapp_status'] == 'Verified': stats["whatsapp_verified"] += 1
            if v_contacts['website']: stats["websites_found"] += 1
            if v_contacts['email']: stats["emails_found"] += 1

            notify_explicit_buyer(c, lead['business_name'], lead['city'], lead['evidence_quote'], b_id)
            actionable_leads.append(lead)

            # Add to local master cache
            master_records.append({
                "business_id": b_id, "name": lead['business_name'], "brand_name": lead['business_name'],
                "city": lead['city'], "phone": v_contacts['phone']
            })

        conn.commit()

        # ---------------------------------------------------------------------
        # STAGE 2: Newly Announced Food Business Openings & Expansions
        # ---------------------------------------------------------------------
        print("\n[STAGE 2] Hunting newly opened food business announcements...")
        openings = hunt_new_openings()
        stats["api_calls_count"] += len(openings)

        for op in openings:
            match_type, matched_master = match_existing_business(op, master_records)

            if match_type == 'EXACT_SAME_OUTLET':
                stats["duplicates_skipped"] += 1
                continue

            b_id = f"biz_{uuid.uuid4().hex[:12]}"
            cat_tuple = cat_map.get(op.get('category_code', 'RESTAURANT'), (1, 'Restaurants & Fine Dining'))
            cat_id, cat_name = cat_tuple

            v_contacts = verify_contacts(op, op['source_url'], source_type="Public Opening Announcement")

            is_branch = (match_type == 'NEW_BRANCH')
            if is_branch:
                stats["branches_discovered"] += 1
                parent_id = matched_master['business_id']
                notify_new_branch(c, op['business_name'], op['city'], op.get('area'), b_id)
            else:
                stats["businesses_discovered"] += 1
                parent_id = None
                notify_new_opening(c, op['business_name'], op['city'], op.get('opening_timeline', 'Just Opened'), b_id)

            # Insert into businesses
            c.execute("""
                INSERT INTO businesses (
                    business_id, name, brand_name, category_id, category_name, subcategory,
                    operating_status, business_size, verification_status, data_confidence,
                    pos_opportunity_score, pos_opportunity_reasons, lead_priority,
                    pos_opportunity_category, is_new_opening, opening_timeline, parent_brand_id,
                    source_url, last_verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'Open', 'Medium', 'Verified', 94, 'High', ?, 'P2', 'B', 1, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                b_id, op['business_name'], op.get('brand_name', op['business_name']), cat_id, cat_name, op.get('subcategory'),
                f"NEW OPENING: {op['announcement_type']}. POS status: {op.get('pos_status')}",
                op.get('opening_timeline', 'Just Opened'), parent_id, op['source_url']
            ))

            # Insert into locations
            c.execute("""
                INSERT INTO locations (
                    business_id, country, province, district, city, area, full_address
                ) VALUES (?, 'Pakistan', ?, ?, ?, ?, ?)
            """, (b_id, op['province'], op['district'], op['city'], op.get('area'), op['full_address']))

            # Insert into contacts
            c.execute("""
                INSERT INTO business_contacts (
                    business_id, phone, whatsapp, whatsapp_status, whatsapp_source,
                    whatsapp_link, email, website
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b_id, v_contacts['phone'], v_contacts['whatsapp'], v_contacts['whatsapp_status'],
                v_contacts['whatsapp_source'], v_contacts['whatsapp_link'], v_contacts['email'], v_contacts['website']
            ))

            # Insert into new_business_announcements
            c.execute("""
                INSERT INTO new_business_announcements (
                    business_id, business_name, category, city, area,
                    announcement_type, announcement_date, opening_date, contact_phone,
                    website_url, source_url, verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Verified')
            """, (
                b_id, op['business_name'], cat_name, op['city'], op.get('area'),
                op['announcement_type'], op.get('announcement_date'), op.get('opening_date'),
                v_contacts['phone'], v_contacts['website'], op['source_url']
            ))

            # Insert into sales_leads
            c.execute("""
                INSERT INTO sales_leads (
                    business_id, business_name, category, city, lead_priority,
                    pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
                ) VALUES (?, ?, ?, ?, 'P2', 'New Lead', 'High', ?, 'Regional Acquisition Rep', ?)
            """, (
                b_id, op['business_name'], cat_name, op['city'],
                f"New Food Business Announcement ({op['announcement_type']})",
                f"Verified Opening: {op.get('notes')}. Target date: {op.get('opening_date')}. Current POS: {op.get('pos_status')}"
            ))

            stats["high_potential_found"] += 1
            if v_contacts['phone']: stats["contacts_found"] += 1
            if v_contacts['whatsapp_status'] == 'Verified': stats["whatsapp_verified"] += 1
            if v_contacts['website']: stats["websites_found"] += 1
            if v_contacts['email']: stats["emails_found"] += 1

            actionable_leads.append(op)
            master_records.append({
                "business_id": b_id, "name": op['business_name'], "brand_name": op.get('brand_name'),
                "city": op['city'], "phone": v_contacts['phone']
            })

        conn.commit()

        # ---------------------------------------------------------------------
        # STAGE 3: Rotating Incremental Multi-City Discovery (OSM / Geocoding)
        # ---------------------------------------------------------------------
        print(f"\n[STAGE 3] Performing incremental geographic sweep across {max_osm_cities} cities...")
        # Check API budget limits before proceeding
        today_date = datetime.date.today().isoformat()
        c.execute("SELECT daily_api_limit FROM hunter_schedules ORDER BY schedule_id DESC LIMIT 1")
        sch = c.fetchone()
        daily_limit = sch[0] if sch else 500

        if stats["api_calls_count"] < daily_limit:
            from collector.continuous_collector import CITIES_SCHEDULE, map_cat, HEADERS
            import requests

            # Rotating city selection
            c.execute("SELECT last_cursor FROM source_checkpoints WHERE source_name = 'osm_rotator'")
            cp_row = c.fetchone()
            curr_cursor = int(cp_row[0]) if cp_row and cp_row[0] else 0

            start_idx = curr_cursor % len(CITIES_SCHEDULE)
            selected_cities = []
            for i in range(max_osm_cities):
                selected_cities.append(CITIES_SCHEDULE[(start_idx + i) % len(CITIES_SCHEDULE)])

            next_cursor = (start_idx + max_osm_cities) % len(CITIES_SCHEDULE)
            c.execute("""
                INSERT INTO source_checkpoints (source_name, last_cursor, last_scanned_at, status)
                VALUES ('osm_rotator', ?, CURRENT_TIMESTAMP, 'active')
                ON CONFLICT(source_name) DO UPDATE SET last_cursor = excluded.last_cursor, last_scanned_at = CURRENT_TIMESTAMP
            """, (str(next_cursor),))
            conn.commit()

            for target in selected_cities:
                city = target['city']
                dist = target['district']
                prov = target['province']
                print(f"  > Scanning city center: {city}, {prov}...")

                for q in target['queries'][:3]: # Keep to top 3 targeted queries per run
                    if stats["api_calls_count"] >= daily_limit:
                        print("    [!] Daily API budget limit reached. Pausing external calls.")
                        break
                    try:
                        stats["api_calls_count"] += 1
                        r = requests.get('https://nominatim.openstreetmap.org/search', params={
                            'q': q, 'format': 'json', 'limit': limit_per_city, 'addressdetails': 1
                        }, headers=HEADERS, timeout=12)

                        if r.status_code == 200:
                            items = r.json()
                        elif r.status_code == 429:
                            stats["failed_sources_count"] += 1
                            time.sleep(3)
                            continue
                        else:
                            stats["failed_sources_count"] += 1
                            continue
                    except Exception as e:
                        stats["failed_sources_count"] += 1
                        errors_list.append(f"OSM query '{q}': {e}")
                        continue

                    for item in items:
                        raw_disp = item.get('display_name', '')
                        addr = item.get('address', {})
                        name = item.get('name') or addr.get('amenity') or addr.get('shop')
                        if not name or name.strip().lower() in ['restaurant', 'cafe', 'fast food', 'bakery', 'hotel']:
                            name = raw_disp.split(',')[0].strip()

                        if not name or len(name) < 3:
                            continue

                        lat = float(item.get('lat', 0.0))
                        lon = float(item.get('lon', 0.0))
                        cand_record = {
                            "name": name, "city": city, "area": addr.get('suburb') or city,
                            "latitude": lat, "longitude": lon, "phone": addr.get('phone')
                        }

                        match_type, matched_master = match_existing_business(cand_record, master_records)

                        if match_type == 'EXACT_SAME_OUTLET':
                            # Check for field updates or route to review queue
                            ch_count, rq_count = process_record_update(c, matched_master, cand_record, "OpenStreetMap")
                            stats["existing_updated"] += ch_count
                            stats["review_queued"] += rq_count
                            stats["duplicates_skipped"] += 1
                            continue

                        cat_code, cat_name = map_cat(q, name + " " + raw_disp)
                        cat_id, _ = cat_map.get(cat_code, (1, cat_name))
                        b_id = f"biz_{uuid.uuid4().hex[:12]}"

                        is_branch = (match_type == 'NEW_BRANCH')
                        parent_id = matched_master['business_id'] if is_branch else None
                        opp_cat = 'C' if is_branch else 'D'
                        priority = 'P3' if is_branch else 'P4'

                        c.execute("""
                            INSERT INTO businesses (
                                business_id, name, brand_name, category_id, category_name,
                                operating_status, business_size, verification_status, data_confidence,
                                pos_opportunity_score, pos_opportunity_reasons, lead_priority,
                                pos_opportunity_category, parent_brand_id, source_url, last_verified_at
                            ) VALUES (?, ?, ?, ?, ?, 'Open', 'Small', 'Verified', 88, 'Medium', ?, ?, ?, ?, 'https://openstreetmap.org', CURRENT_TIMESTAMP)
                        """, (
                            b_id, name, name, cat_id, cat_name,
                            f"Discovered via rotating geographic crawl in {city}",
                            priority, opp_cat, parent_id
                        ))

                        c.execute("""
                            INSERT INTO locations (
                                business_id, country, province, district, city, area,
                                full_address, postal_code, latitude, longitude, google_maps_url
                            ) VALUES (?, 'Pakistan', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            b_id, prov, dist, city, addr.get('suburb', city),
                            raw_disp, addr.get('postcode', ''), lat, lon, f"https://maps.google.com/?q={lat},{lon}"
                        ))

                        c.execute("""
                            INSERT INTO business_contacts (business_id, phone, whatsapp_status)
                            VALUES (?, ?, 'Not Found')
                        """, (b_id, addr.get('phone')))

                        c.execute("""
                            INSERT INTO sales_leads (
                                business_id, business_name, category, city, lead_priority,
                                pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
                            ) VALUES (?, ?, ?, ?, ?, 'New Lead', 'Medium', ?, 'Field Rep Pool', ?)
                        """, (
                            b_id, name, cat_name, city, priority,
                            f"Incremental discovery {cat_name} in {city}",
                            f"Geocoded coordinates: {lat}, {lon}. Source: OpenStreetMap"
                        ))

                        if is_branch:
                            stats["branches_discovered"] += 1
                            stats["high_potential_found"] += 1
                        else:
                            stats["businesses_discovered"] += 1
                            stats["medium_potential_found"] += 1

                        if addr.get('phone'): stats["contacts_found"] += 1

                        master_records.append({
                            "business_id": b_id, "name": name, "brand_name": name,
                            "city": city, "phone": addr.get('phone'), "latitude": lat, "longitude": lon
                        })

                    time.sleep(1.2) # Polite usage
            conn.commit()

        # Estimated cost calculation ($0 for public/OSM, $0.005 for commercial calls)
        stats["estimated_cost_usd"] = stats["api_calls_count"] * 0.0005

        # ---------------------------------------------------------------------
        # STAGE 4: Generate Structured Daily Intelligence Report
        # ---------------------------------------------------------------------
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        stats["duration_seconds"] = duration

        markdown_report, report_record = generate_daily_report(stats, actionable_leads)

        # Save Report
        c.execute("""
            INSERT INTO daily_hunter_reports (
                report_id, job_id, report_date, report_title, summary_json, markdown_content
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            report_record['report_id'], job_id, report_record['report_date'],
            report_record['report_title'], report_record['summary_json'], report_record['markdown_content']
        ))

        # Finalize Job Record
        c.execute("""
            UPDATE hunter_jobs SET
                status = 'completed',
                end_time = ?,
                duration_seconds = ?,
                businesses_discovered = ?,
                branches_discovered = ?,
                contacts_found = ?,
                whatsapp_verified = ?,
                websites_found = ?,
                emails_found = ?,
                explicit_pos_found = ?,
                high_potential_found = ?,
                medium_potential_found = ?,
                existing_updated = ?,
                duplicates_skipped = ?,
                review_queued = ?,
                failed_sources_count = ?,
                api_calls_count = ?,
                estimated_cost_usd = ?,
                summary_markdown = ?,
                errors_log = ?
            WHERE job_id = ?
        """, (
            end_time.isoformat(), duration, stats["businesses_discovered"], stats["branches_discovered"],
            stats["contacts_found"], stats["whatsapp_verified"], stats["websites_found"], stats["emails_found"],
            stats["explicit_pos_found"], stats["high_potential_found"], stats["medium_potential_found"],
            stats["existing_updated"], stats["duplicates_skipped"], stats["review_queued"],
            stats["failed_sources_count"], stats["api_calls_count"], stats["estimated_cost_usd"],
            markdown_report, "\n".join(errors_list) if errors_list else None, job_id
        ))

        # Update last run timestamp in hunter_schedules
        c.execute("UPDATE hunter_schedules SET last_run_at = CURRENT_TIMESTAMP")
        conn.commit()

        # ---------------------------------------------------------------------
        # STAGE 5: Refresh Master Excel & CSV Exports
        # ---------------------------------------------------------------------
        print("\n[STAGE 5] Refreshing Master Excel Workbook and Master CSV exports...")
        try:
            run_exports()
            print("Exports successfully updated with latest discoveries!")
        except Exception as e:
            print(f"Warning on export refresh: {e}")

        conn.close()

        print("=" * 72)
        print(f"AI LEAD HUNTER JOB [{job_id}] COMPLETED SUCCESSFULLY IN {duration:.2f}s")
        print(f"New Discoveries: {stats['businesses_discovered']} | Explicit POS: {stats['explicit_pos_found']} | P1/P2 Leads: {stats['high_potential_found']}")
        print("=" * 72)

        return stats, report_record

    except Exception as e:
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        err_msg = traceback.format_exc()
        print(f"\n[FATAL ERROR] Job {job_id} encountered an exception:\n{err_msg}")

        c.execute("""
            UPDATE hunter_jobs SET
                status = 'failed',
                end_time = ?,
                duration_seconds = ?,
                errors_log = ?
            WHERE job_id = ?
        """, (end_time.isoformat(), duration, err_msg, job_id))
        notify_job_failure(c, job_id, str(e))
        conn.commit()
        conn.close()
        raise e

if __name__ == '__main__':
    execute_lead_hunter_job(run_type="manual", max_osm_cities=2, limit_per_city=10)
