"""
Intelligent Deduplicator, Branch Detector & Master Database Updater
Handles matching against master database, detects branch expansions,
tracks field-level changes in record_change_history, and routes uncertain updates
to human_review_queue.
"""

import math
import uuid
import datetime
from collector.deduplicator import normalize_name, normalize_phone

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates geographical distance between two coordinates in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999.0
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def match_existing_business(candidate, master_records):
    """
    Matches a candidate against master businesses.
    Returns:
      (match_type, matched_record)
      match_type can be:
        - 'EXACT_SAME_OUTLET' (Same name and location/phone - skip or update)
        - 'NEW_BRANCH' (Same brand name but distinct location/city/area - add as branch)
        - 'NONE' (New unique business)
    """
    c_name = normalize_name(candidate.get('name') or candidate.get('business_name') or '')
    c_brand = normalize_name(candidate.get('brand_name') or candidate.get('name') or '')
    c_phone = normalize_phone(candidate.get('phone') or candidate.get('contact_phone') or '')
    c_city = (candidate.get('city') or '').strip().lower()
    c_area = (candidate.get('area') or '').strip().lower()
    c_lat = candidate.get('latitude')
    c_lon = candidate.get('longitude')

    for master in master_records:
        m_name = normalize_name(master.get('name') or '')
        m_brand = normalize_name(master.get('brand_name') or master.get('name') or '')
        m_phone = normalize_phone(master.get('phone') or '')
        m_city = (master.get('city') or '').strip().lower()
        m_area = (master.get('area') or '').strip().lower()
        m_lat = master.get('latitude')
        m_lon = master.get('longitude')

        # Distance calculation
        dist_km = calculate_haversine_distance(c_lat, c_lon, m_lat, m_lon)

        # 1. Exact Phone Match
        if c_phone and m_phone and c_phone == m_phone:
            if c_city == m_city and (dist_km < 1.0 or not c_lat):
                return 'EXACT_SAME_OUTLET', master

        # 2. Exact Name Match in Same City
        if c_name and m_name and c_name == m_name:
            if c_city == m_city:
                if dist_km < 0.5:
                    return 'EXACT_SAME_OUTLET', master
                elif dist_km >= 0.5 or (c_area and m_area and c_area != m_area):
                    # Different location in same city = New branch of existing brand!
                    return 'NEW_BRANCH', master
                else:
                    return 'EXACT_SAME_OUTLET', master
            else:
                # Same brand name in different city = Inter-city branch expansion!
                return 'NEW_BRANCH', master

        # 3. Brand name match with branch keywords
        if c_brand and m_brand and (c_brand == m_brand or c_brand in m_name or m_brand in c_name):
            if c_city != m_city or (c_area and m_area and c_area != m_area):
                return 'NEW_BRANCH', master

    return 'NONE', None

def process_record_update(cursor, existing_record, new_data, source_url):
    """
    Safely updates an existing record, writing field changes to record_change_history,
    or enqueuing uncertain updates into human_review_queue.
    """
    b_id = existing_record['business_id']
    changes_made = 0
    review_queued = 0

    # Fields that can be safely updated if newly verified
    updatable_fields = [
        ('phone', new_data.get('phone')),
        ('whatsapp', new_data.get('whatsapp')),
        ('email', new_data.get('email')),
        ('website', new_data.get('website')),
        ('operating_status', new_data.get('operating_status')),
        ('price_range', new_data.get('price_range')),
        ('opening_hours', new_data.get('opening_hours'))
    ]

    for field, new_val in updatable_fields:
        if not new_val:
            continue
        old_val = existing_record.get(field)
        if not old_val or old_val in ['Not Found', 'Unknown', 'Needs Verification']:
            # Safe automatic enrichment
            if field in ['phone', 'whatsapp', 'email', 'website']:
                cursor.execute(f"UPDATE business_contacts SET {field} = ? WHERE business_id = ?", (new_val, b_id))
            elif field in ['operating_status']:
                cursor.execute("UPDATE businesses SET operating_status = ?, updated_at = CURRENT_TIMESTAMP WHERE business_id = ?", (new_val, b_id))

            # Record audit history
            cursor.execute("""
                INSERT INTO record_change_history (business_id, field_name, old_value, new_value, source_url, change_type)
                VALUES (?, ?, ?, ?, ?, 'auto_update')
            """, (b_id, field, str(old_val), str(new_val), source_url))
            changes_made += 1

        elif old_val != new_val:
            # Conflicting value detected! Do not overwrite without verification. Route to human review queue!
            rev_id = f"rev_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
                INSERT INTO human_review_queue (
                    review_id, business_id, business_name, city, field_name,
                    current_value, proposed_value, change_reason, source_url, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rev_id, b_id, existing_record.get('name', 'Business'), existing_record.get('city'), field,
                str(old_val), str(new_val), f"Discovered differing value from {source_url}", source_url, 80
            ))
            review_queued += 1

    # Refresh last verified date
    cursor.execute("UPDATE businesses SET last_verified_at = CURRENT_TIMESTAMP WHERE business_id = ?", (b_id,))
    return changes_made, review_queued

