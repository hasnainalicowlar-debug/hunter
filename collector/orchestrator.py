"""
Master Data Orchestrator & Ingestion Engine
Coordinates discovery, deduplication, scoring, enrichment, and normalized storage.
"""

import sys
import os
import uuid
import datetime
import traceback

# Add parent path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import get_connection, init_db
from collector.scoring_engine import evaluate_pos_opportunity, calculate_lead_priority
from collector.deduplicator import is_duplicate_outlet, normalize_phone
from collector.pakistan_verified_seed import get_verified_businesses
from collector.buyer_intent_collector import get_buyer_intent_records
from collector.new_openings_collector import get_new_openings_records
from collector.osm_collector import collect_osm_data

def run_pipeline(include_live_osm=True, osm_limit_targets=6):
    print("=" * 70)
    print("Starting Pakistan Food Business Intelligence Ingestion Pipeline...")
    print("=" * 70)
    
    conn = get_connection()
    cursor = conn.cursor()

    log_start = datetime.datetime.now()
    records_fetched = 0
    records_created = 0
    records_updated = 0
    duplicates_skipped = 0
    errors = []

    # Category code to ID map
    cursor.execute("SELECT category_id, code, name FROM business_categories")
    cat_map = {row['code']: row['category_id'] for row in cursor.fetchall()}
    
    # Existing outlets for deduplication
    cursor.execute("""
        SELECT b.business_id, b.name, l.city, l.latitude, l.longitude, c.phone
        FROM businesses b
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
    """)
    existing_outlets = [dict(row) for row in cursor.fetchall()]

    # 1. Ingest Verified National Baseline Businesses
    verified_items = get_verified_businesses()
    records_fetched += len(verified_items)
    print(f"Processing {len(verified_items)} verified national baseline establishments...")

    for item in verified_items:
        # Check duplicate
        dup = False
        for ext in existing_outlets:
            is_dup, reason = is_duplicate_outlet(ext, item)
            if is_dup:
                dup = True
                duplicates_skipped += 1
                break
        if dup:
            continue

        b_id = f"biz_{uuid.uuid4().hex[:12]}"
        cat_id = cat_map.get(item['category_code'], 1)
        
        # Scoring
        pos_score, pos_reasons = evaluate_pos_opportunity({
            'category_name': item['category_name'],
            'total_branches': 1,
            'dine_in': item.get('dine_in', 1),
            'takeaway': item.get('takeaway', 1),
            'delivery': item.get('delivery', 0),
            'price_range': item.get('price_range', '$$'),
            'operating_status': item.get('operating_status', 'Open'),
            'pos_provider_name': item.get('pos_provider_name', 'Unknown')
        })

        lead_priority = calculate_lead_priority(
            has_explicit_intent=False,
            intent_tier='None',
            opportunity_score=pos_score,
            has_verified_contact=bool(item.get('phone') or item.get('whatsapp')),
            is_new_opening=False
        )

        # Insert businesses
        cursor.execute("""
            INSERT INTO businesses (
                business_id, name, brand_name, category_id, category_name, subcategory,
                business_description, is_franchise, parent_company, year_established,
                operating_status, business_size, verification_status, data_confidence,
                pos_opportunity_score, pos_opportunity_reasons, lead_priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, item['name'], item.get('brand_name'), cat_id, item['category_name'],
            item.get('subcategory'), item.get('description'), item.get('is_franchise', 0),
            item.get('parent_company'), item.get('year_established'), item.get('operating_status', 'Open'),
            item.get('business_size', 'Small'), item.get('verification_status', 'Verified'),
            item.get('data_confidence', 90), pos_score, pos_reasons, lead_priority
        ))

        # Insert branch
        branch_id = f"br_{uuid.uuid4().hex[:10]}"
        cursor.execute("""
            INSERT INTO business_branches (branch_id, business_id, branch_name, is_headquarters, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (branch_id, b_id, item['name'], 1, item.get('phone')))

        # Insert contacts
        cursor.execute("""
            INSERT INTO business_contacts (
                business_id, branch_id, phone, alternative_phone, whatsapp, whatsapp_status,
                whatsapp_source, whatsapp_link, email, website, contact_page_url, online_ordering_url, menu_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, branch_id, item.get('phone'), item.get('alternative_phone'),
            item.get('whatsapp'), item.get('whatsapp_status', 'Needs Verification'),
            item.get('whatsapp_source'), item.get('whatsapp_link'), item.get('email'),
            item.get('website'), item.get('website'), item.get('online_ordering_url'), item.get('menu_url')
        ))

        # Insert location
        cursor.execute("""
            INSERT INTO locations (
                business_id, branch_id, country, province, division, district, tehsil, city,
                area, market, full_address, nearby_landmark, postal_code, google_maps_url,
                latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, branch_id, 'Pakistan', item.get('province'), item.get('division'),
            item.get('district'), item.get('tehsil'), item.get('city'), item.get('area'),
            item.get('market'), item.get('full_address'), item.get('nearby_landmark'),
            item.get('postal_code'), item.get('google_maps_url'), item.get('latitude'), item.get('longitude')
        ))

        # Insert social
        if item.get('facebook'):
            cursor.execute("INSERT INTO social_profiles (business_id, platform, url) VALUES (?, ?, ?)", (b_id, 'Facebook', item['facebook']))
        if item.get('instagram'):
            cursor.execute("INSERT INTO social_profiles (business_id, platform, url) VALUES (?, ?, ?)", (b_id, 'Instagram', item['instagram']))

        # Insert website
        if item.get('website'):
            cursor.execute("INSERT INTO websites (business_id, url) VALUES (?, ?)", (b_id, item['website']))

        # Insert menu
        cursor.execute("""
            INSERT INTO menus (
                business_id, price_range, cuisines, opening_hours, closing_hours,
                dine_in, takeaway, delivery, seating_capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, item.get('price_range', '$$'), item.get('cuisines'), item.get('opening_hours'),
            item.get('closing_hours'), item.get('dine_in', 1), item.get('takeaway', 1),
            item.get('delivery', 1), item.get('seating_capacity', 50)
        ))

        # Insert existing POS info
        pos_name = item.get('pos_provider_name', 'Unknown')
        cursor.execute("""
            INSERT INTO existing_pos_info (
                business_id, branch_id, pos_provider_name, is_pos_verified, evidence_source, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            b_id, branch_id, pos_name, item.get('is_pos_verified', 0),
            item.get('pos_status', 'Unknown'), item.get('notes', '')
        ))

        # Insert Sales Lead CRM
        stage = 'New Lead'
        assigned = 'Sarah Khan (Senior AE)' if lead_priority in ['P1', 'P2'] else 'Hamza Malik (Inside Sales)'
        cursor.execute("""
            INSERT INTO sales_leads (
                business_id, business_name, category, city, lead_priority,
                pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, item['name'], item['category_name'], item['city'], lead_priority,
            stage, pos_score, pos_reasons, assigned, f"Initial system discovery. {item.get('notes', '')}"
        ))

        records_created += 1
        existing_outlets.append({
            'business_id': b_id,
            'name': item['name'],
            'city': item['city'],
            'latitude': item.get('latitude'),
            'longitude': item.get('longitude'),
            'phone': item.get('phone')
        })

    conn.commit()

    # 2. Ingest Active Buyer Intent Signals
    intent_items = get_buyer_intent_records()
    records_fetched += len(intent_items)
    print(f"Processing {len(intent_items)} active POS buyer-intent records...")

    for intent in intent_items:
        # Check if already in intent table
        cursor.execute("SELECT intent_id FROM pos_buyer_intent_signals WHERE business_name = ?", (intent['business_name'],))
        if cursor.fetchone():
            continue

        b_id = f"biz_{uuid.uuid4().hex[:12]}"
        cat_code = 'RESTAURANT'
        for code, cname in [('CAFE', 'Cafe'), ('FAST_FOOD', 'Fast Food'), ('BAKERY', 'Bakery'), ('PIZZA', 'Pizza'), ('DHABA', 'Dhaba'), ('SWEETS', 'Sweet')]:
            if cname.lower() in intent['category'].lower():
                cat_code = code
                break
        cat_id = cat_map.get(cat_code, 1)

        # High priority lead
        pos_score = "High"
        pos_reasons = f"Explicit buyer-intent signal: {intent['requirement_type']}. Evaluating vendors: Yes."
        lead_priority = intent['lead_priority']

        cursor.execute("""
            INSERT INTO businesses (
                business_id, name, brand_name, category_id, category_name,
                business_description, operating_status, business_size, verification_status,
                data_confidence, pos_opportunity_score, pos_opportunity_reasons, lead_priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, intent['business_name'], intent['business_name'], cat_id, intent['category'],
            intent['evidence_summary'], 'Open', 'Small', 'Verified',
            95, pos_score, pos_reasons, lead_priority
        ))

        # Contacts
        wa_link = f"https://wa.me/{normalize_phone(intent.get('whatsapp'))}" if intent.get('whatsapp') else None
        cursor.execute("""
            INSERT INTO business_contacts (
                business_id, phone, whatsapp, whatsapp_status, whatsapp_source,
                whatsapp_link, website
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, intent.get('contact_phone'), intent.get('whatsapp'), 'Verified',
            f"Buyer Intent Listing ({intent['source_platform']})", wa_link, intent.get('website_url')
        ))

        # Location
        cursor.execute("""
            INSERT INTO locations (
                business_id, country, province, district, city, area, full_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, 'Pakistan', 'Punjab' if intent['city'] in ['Lahore', 'Rawalpindi', 'Multan', 'Faisalabad', 'Gujranwala'] else ('Sindh' if intent['city'] == 'Karachi' else ('Khyber Pakhtunkhwa' if intent['city'] == 'Peshawar' else ('Balochistan' if intent['city'] == 'Quetta' else 'Islamabad Capital Territory'))),
            intent['city'], intent['city'], intent.get('area'), f"{intent.get('area', '')}, {intent['city']}, Pakistan"
        ))

        # Record Intent Signal
        cursor.execute("""
            INSERT INTO pos_buyer_intent_signals (
                business_id, business_name, category, city, contact_phone, whatsapp,
                website_url, intent_tier, requirement_type, source_platform, source_url,
                original_post_date, evidence_summary, verification_status, lead_priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, intent['business_name'], intent['category'], intent['city'],
            intent.get('contact_phone'), intent.get('whatsapp'), intent.get('website_url'),
            intent['intent_tier'], intent['requirement_type'], intent['source_platform'],
            intent['source_url'], intent.get('original_post_date'), intent['evidence_summary'],
            'Verified', lead_priority
        ))

        # Sales Lead CRM
        cursor.execute("""
            INSERT INTO sales_leads (
                business_id, business_name, category, city, lead_priority,
                pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, intent['business_name'], intent['category'], intent['city'], lead_priority,
            'Verified Lead', pos_score, pos_reasons, 'Bilal Tariq (Key Account Lead)',
            f"HIGH INTENT SIGNAL: {intent['requirement_type']}. Evidence: {intent['evidence_summary']}"
        ))

        records_created += 1

    conn.commit()

    # 3. Ingest New Business Announcements
    opening_items = get_new_openings_records()
    records_fetched += len(opening_items)
    print(f"Processing {len(opening_items)} new and upcoming business announcements...")

    for op in opening_items:
        cursor.execute("SELECT announcement_id FROM new_business_announcements WHERE business_name = ?", (op['business_name'],))
        if cursor.fetchone():
            continue

        b_id = f"biz_{uuid.uuid4().hex[:12]}"
        cat_code = 'RESTAURANT'
        for code, cname in [('CAFE', 'Cafe'), ('FAST_FOOD', 'Fast Food'), ('BAKERY', 'Bakery'), ('PIZZA', 'Pizza'), ('DHABA', 'Dhaba'), ('SWEETS', 'Sweet'), ('CLOUD_KITCHEN', 'Cloud'), ('HOTEL_DINING', 'Hotel')]:
            if cname.lower() in op['category'].lower():
                cat_code = code
                break
        cat_id = cat_map.get(cat_code, 1)

        pos_score = op.get('opportunity_score', 'High')
        lead_priority = 'P1' if pos_score == 'High' else 'P2'
        pos_reasons = f"New market opening ({op['announcement_type']}). Status: {op.get('pos_status', 'No POS')}"

        cursor.execute("""
            INSERT INTO businesses (
                business_id, name, brand_name, category_id, category_name,
                operating_status, business_size, verification_status, data_confidence,
                pos_opportunity_score, pos_opportunity_reasons, lead_priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, op['business_name'], op['business_name'], cat_id, op['category'],
            op['announcement_type'], 'Small', 'Verified', 96,
            pos_score, pos_reasons, lead_priority
        ))

        wa_link = f"https://wa.me/{normalize_phone(op.get('whatsapp'))}" if op.get('whatsapp') else None
        cursor.execute("""
            INSERT INTO business_contacts (
                business_id, phone, whatsapp, whatsapp_status, whatsapp_source,
                whatsapp_link, website
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, op.get('contact_phone'), op.get('whatsapp'), 'Verified',
            f"New Opening Announcement ({op['source_url']})", wa_link, op.get('website_url')
        ))

        cursor.execute("""
            INSERT INTO locations (
                business_id, country, province, district, city, area, full_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, 'Pakistan', 'Punjab' if op['city'] in ['Lahore', 'Rawalpindi', 'Multan', 'Faisalabad', 'Sialkot', 'Dera Ghazi Khan'] else ('Sindh' if op['city'] == 'Karachi' else ('Khyber Pakhtunkhwa' if op['city'] in ['Peshawar', 'Abbottabad'] else ('Balochistan' if op['city'] == 'Quetta' else ('Gilgit-Baltistan' if op['city'] == 'Hunza' else 'Islamabad Capital Territory')))),
            op['city'], op['city'], op.get('area'), f"{op.get('area', '')}, {op['city']}, Pakistan"
        ))

        # Record Announcement
        cursor.execute("""
            INSERT INTO new_business_announcements (
                business_id, business_name, city, area, category, announcement_type,
                announcement_date, opening_date, contact_phone, website_url, source_url, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, op['business_name'], op['city'], op.get('area'), op['category'],
            op['announcement_type'], op.get('announcement_date'), op.get('opening_date'),
            op.get('contact_phone'), op.get('website_url'), op['source_url'], 'Verified'
        ))

        cursor.execute("""
            INSERT INTO sales_leads (
                business_id, business_name, category, city, lead_priority,
                pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b_id, op['business_name'], op['category'], op['city'], lead_priority,
            'New Lead', pos_score, pos_reasons, 'Zainab Qureshi (Growth Lead)',
            f"NEW OPENING: {op['announcement_type']}. Opening date: {op.get('opening_date')}. Current POS: {op.get('pos_status')}"
        ))

        records_created += 1

    conn.commit()

    # 4. Ingest Live OSM Nominatim Data (with duplicate prevention)
    if include_live_osm:
        try:
            print("Running OpenStreetMap Nominatim discovery across selected cities...")
            osm_items = collect_osm_data(max_targets=osm_limit_targets)
            records_fetched += len(osm_items)

            for item in osm_items:
                dup = False
                for ext in existing_outlets:
                    is_dup, reason = is_duplicate_outlet(ext, item)
                    if is_dup:
                        dup = True
                        duplicates_skipped += 1
                        break
                if dup:
                    continue

                b_id = f"biz_{uuid.uuid4().hex[:12]}"
                cat_id = cat_map.get(item['category_code'], 1)

                pos_score, pos_reasons = evaluate_pos_opportunity({
                    'category_name': item['category_name'],
                    'total_branches': 1,
                    'dine_in': 1,
                    'takeaway': 1,
                    'price_range': '$$',
                    'operating_status': 'Open',
                    'pos_provider_name': 'Unknown'
                })

                lead_priority = calculate_lead_priority(
                    has_explicit_intent=False,
                    intent_tier='None',
                    opportunity_score=pos_score,
                    has_verified_contact=False, # OSM nodes frequently lack phone initially
                    is_new_opening=False
                )

                cursor.execute("""
                    INSERT INTO businesses (
                        business_id, name, brand_name, category_id, category_name,
                        operating_status, business_size, verification_status, data_confidence,
                        pos_opportunity_score, pos_opportunity_reasons, lead_priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b_id, item['name'], item['name'], cat_id, item['category_name'],
                    'Open', 'Small', 'Verified', 88,
                    pos_score, pos_reasons, lead_priority
                ))

                # Contacts
                cursor.execute("""
                    INSERT INTO business_contacts (
                        business_id, phone, whatsapp_status
                    ) VALUES (?, ?, ?)
                """, (b_id, None, 'Not Found'))

                # Location
                cursor.execute("""
                    INSERT INTO locations (
                        business_id, country, province, district, city, area,
                        full_address, postal_code, google_maps_url, latitude, longitude
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b_id, 'Pakistan', item.get('province'), item.get('district'),
                    item.get('city'), item.get('area'), item.get('full_address'),
                    item.get('postal_code'), item.get('google_maps_url'),
                    item.get('latitude'), item.get('longitude')
                ))

                # Lead CRM
                cursor.execute("""
                    INSERT INTO sales_leads (
                        business_id, business_name, category, city, lead_priority,
                        pipeline_stage, pos_opportunity_score, opportunity_reasons, assigned_rep, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b_id, item['name'], item['category_name'], item['city'], lead_priority,
                    'New Lead', pos_score, pos_reasons, 'Unassigned', 'Discovered via OpenStreetMap geodatabase. Contact phone research pending.'
                ))

                records_created += 1
                existing_outlets.append({
                    'business_id': b_id,
                    'name': item['name'],
                    'city': item['city'],
                    'latitude': item.get('latitude'),
                    'longitude': item.get('longitude'),
                    'phone': ''
                })

            conn.commit()
        except Exception as e:
            err_msg = f"OSM Collection Error: {e}\n{traceback.format_exc()}"
            print(err_msg)
            errors.append(err_msg)

    # Update Administrative Regions Total Count
    cursor.execute("""
        SELECT l.city, COUNT(b.business_id) as cnt
        FROM businesses b
        JOIN locations l ON b.business_id = l.business_id
        GROUP BY l.city
    """)
    city_counts = cursor.fetchall()
    for row in city_counts:
        cursor.execute("""
            UPDATE administrative_regions
            SET total_businesses_discovered = ?, status = 'Active'
            WHERE city = ?
        """, (row['cnt'], row['city']))

    log_end = datetime.datetime.now()
    status_str = "Success" if not errors else "Partial"
    cursor.execute("""
        INSERT INTO data_collection_logs (
            job_name, source, region, status, records_fetched, records_created,
            records_updated, duplicates_skipped, errors, start_time, end_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'Pakistan National Multi-Source Ingestion', 'Multi-Source (Verified + OSM + Intent + Openings)',
        'Pakistan Nationwide', status_str, records_fetched, records_created,
        records_updated, duplicates_skipped, "\n".join(errors) if errors else None,
        log_start.isoformat(), log_end.isoformat()
    ))
    conn.commit()
    conn.close()

    print("=" * 70)
    print(f"Pipeline Completed! Fetched: {records_fetched}, Created: {records_created}, Duplicates Skipped: {duplicates_skipped}")
    print("=" * 70)
    return {
        'records_fetched': records_fetched,
        'records_created': records_created,
        'duplicates_skipped': duplicates_skipped,
        'status': status_str
    }

if __name__ == '__main__':
    run_pipeline(include_live_osm=True, osm_limit_targets=6)
