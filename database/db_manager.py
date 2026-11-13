"""
Pakistan Food Business & POS Intelligence Platform - Database Manager
Handles SQLite connection, migrations, seeding, and core queries.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_intel.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema_sqlite.sql')

def get_connection(timeout=60.0):
    if not os.path.exists(DB_PATH):
        zip_path = DB_PATH + '.zip'
        if os.path.exists(zip_path):
            import zipfile
            print(f"Auto-extracting {zip_path} to {DB_PATH}...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(os.path.dirname(DB_PATH))
            print("Database extraction complete!")
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.row_factory = sqlite3.Row
    try:
        # Avoid WAL on NFS/PythonAnywhere filesystems where shared memory is unsupported
        if 'PYTHONANYWHERE_DOMAIN' in os.environ or 'pythonanywhere' in os.path.expanduser('~') or 'jytjty' in os.path.expanduser('~'):
            conn.execute("PRAGMA journal_mode = DELETE;")
        else:
            conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        conn.execute("PRAGMA journal_mode = DELETE;")
    conn.execute("PRAGMA busy_timeout = 60000;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())
    conn.commit()
    seed_initial_data(conn)
    conn.close()
    print("Database initialized successfully at", DB_PATH)

def seed_initial_data(conn):
    cursor = conn.cursor()

    # 1. Seed Business Categories
    categories = [
        ('RESTAURANT', 'Restaurants & Fine Dining', 'utensils', 'Family, fine-dining, desi, continental, and buffet restaurants', 'High'),
        ('FAST_FOOD', 'Fast Food & QSR', 'hamburger', 'Burgers, shawarma, fried chicken, pizzas, sandwiches, and wraps', 'High'),
        ('CAFE', 'Cafes & Coffee Shops', 'coffee', 'Specialty coffee, tea cafes, dessert cafes, and small lounges', 'High'),
        ('BAKERY', 'Bakeries & Confectioneries', 'birthday-cake', 'Commercial bakeries, cake shops, and pastry houses', 'High'),
        ('DHABA', 'Dhabas & Highway Food Points', 'truck', 'Roadside eateries, highway restaurants, truck-stop dhabas, local spots', 'Medium'),
        ('SWEETS', 'Sweet & Halwai Shops (Mithai)', 'candy-cane', 'Traditional Pakistani sweet marts, halwa puri shops, and confectioneries', 'Medium'),
        ('HOTEL_DINING', 'Hotels with Dining Services', 'hotel', 'Hotel restaurants, tourist resorts, motels, and guest house dining', 'High'),
        ('PIZZA', 'Pizza Outlets & Pizzerias', 'pizza-slice', 'Specialized pizza parlors and Italian casual dining', 'High'),
        ('BBQ', 'BBQ & Sajji Outlets', 'fire', 'Barbecue points, seekh kabab, tikka, and Balochi sajji outlets', 'Medium'),
        ('TANDOOR', 'Tandoor & Naan Centers', 'bread-slice', 'Traditional tandoors, roghni naan, and kulcha shops', 'Low'),
        ('ICE_CREAM', 'Ice Cream & Dessert Parlors', 'ice-cream', 'Gelaterias, ice cream shops, falooda, and kulfi spots', 'Medium'),
        ('JUICE_BAR', 'Juice Bars & Shake Corners', 'glass-whiskey', 'Fresh seasonal juice bars, shake shops, and smoothie corners', 'Low'),
        ('CLOUD_KITCHEN', 'Cloud Kitchens & Ghost Kitchens', 'cloud', 'Delivery-only virtual kitchens and dark kitchen clusters', 'High'),
        ('FOOD_COURT', 'Food Courts & Plaza Eateries', 'store', 'Mall food courts and commercial plaza stalls', 'High'),
        ('CATERING', 'Catering & Event Services', 'concierge-bell', 'Marriage hall caterers, institutional and corporate event catering', 'Medium'),
        ('CANTEEN', 'Cafeterias & Canteens', 'school', 'University canteens, college cafeterias, and hospital mess', 'Medium'),
        ('STREET_FOOD', 'Roadside Food Outlets & Carts', 'motorcycle', 'Chaat stalls, bun kabab points, and localized street vendors', 'Low'),
        ('FRANCHISE', 'Food Franchises & Chains', 'network-wired', 'National and multinational multi-unit franchise brands', 'High'),
        ('SEAFOOD', 'Seafood Specialists', 'fish', 'Fresh fish fry spots, prawn specialists, and coastal eateries', 'Medium'),
        ('OTHER_FOOD', 'Other Food-Service Establishments', 'utensil-spoon', 'Specialized and miscellaneous food-service operators', 'Medium')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO business_categories (code, name, icon, description, default_pos_opportunity)
        VALUES (?, ?, ?, ?, ?)
    """, categories)

    # 2. Seed Administrative Regions (Provinces, Major Districts & Cities)
    regions = [
        # Punjab
        ('Punjab', 'Lahore Division', 'Lahore', 'Lahore City', 'Lahore', 'Active', 0),
        ('Punjab', 'Rawalpindi Division', 'Rawalpindi', 'Rawalpindi', 'Rawalpindi', 'Active', 0),
        ('Punjab', 'Faisalabad Division', 'Faisalabad', 'Faisalabad City', 'Faisalabad', 'Active', 0),
        ('Punjab', 'Multan Division', 'Multan', 'Multan City', 'Multan', 'Active', 0),
        ('Punjab', 'Gujranwala Division', 'Gujranwala', 'Gujranwala City', 'Gujranwala', 'Active', 0),
        ('Punjab', 'Gujranwala Division', 'Sialkot', 'Sialkot City', 'Sialkot', 'Active', 0),
        ('Punjab', 'Gujranwala Division', 'Gujrat', 'Gujrat', 'Gujrat', 'Active', 0),
        ('Punjab', 'Sargodha Division', 'Sargodha', 'Sargodha', 'Sargodha', 'Active', 0),
        ('Punjab', 'Bahawalpur Division', 'Bahawalpur', 'Bahawalpur', 'Bahawalpur', 'Active', 0),
        ('Punjab', 'Sahiwal Division', 'Sahiwal', 'Sahiwal', 'Sahiwal', 'Active', 0),
        ('Punjab', 'Rawalpindi Division', 'Murree', 'Murree', 'Murree', 'Active', 0),
        ('Punjab', 'D.G. Khan Division', 'D.G. Khan', 'D.G. Khan', 'Dera Ghazi Khan', 'Active', 0),
        ('Punjab', 'Faisalabad Division', 'Jhang', 'Jhang', 'Jhang', 'Active', 0),
        ('Punjab', 'Bahawalpur Division', 'Rahim Yar Khan', 'Rahim Yar Khan', 'Rahim Yar Khan', 'Active', 0),
        ('Punjab', 'Sheikhupura Division', 'Sheikhupura', 'Sheikhupura', 'Sheikhupura', 'Active', 0),
        ('Punjab', 'Sargodha Division', 'Mianwali', 'Mianwali', 'Mianwali', 'Active', 0),
        ('Punjab', 'Gujranwala Division', 'Kasur', 'Kasur', 'Kasur', 'Active', 0),

        # Sindh
        ('Sindh', 'Karachi Division', 'Karachi South', 'Saddar / Clifton', 'Karachi', 'Active', 0),
        ('Sindh', 'Karachi Division', 'Karachi East', 'Gulshan / PECHS', 'Karachi', 'Active', 0),
        ('Sindh', 'Karachi Division', 'Karachi Central', 'Nazimabad / North Nazimabad', 'Karachi', 'Active', 0),
        ('Sindh', 'Karachi Division', 'Korangi', 'Korangi', 'Karachi', 'Active', 0),
        ('Sindh', 'Karachi Division', 'Malir', 'Malir', 'Karachi', 'Active', 0),
        ('Sindh', 'Karachi Division', 'Karachi West', 'SITE', 'Karachi', 'Active', 0),
        ('Sindh', 'Hyderabad Division', 'Hyderabad', 'City / Latifabad / Qasimabad', 'Hyderabad', 'Active', 0),
        ('Sindh', 'Sukkur Division', 'Sukkur', 'Sukkur', 'Sukkur', 'Active', 0),
        ('Sindh', 'Larkana Division', 'Larkana', 'Larkana', 'Larkana', 'Active', 0),
        ('Sindh', 'Mirpur Khas Division', 'Mirpur Khas', 'Mirpur Khas', 'Mirpur Khas', 'Active', 0),
        ('Sindh', 'Nawabshah Division', 'Shaheed Benazirabad', 'Nawabshah', 'Nawabshah', 'Active', 0),

        # Khyber Pakhtunkhwa (KP)
        ('Khyber Pakhtunkhwa', 'Peshawar Division', 'Peshawar', 'Peshawar', 'Peshawar', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'Mardan Division', 'Mardan', 'Mardan', 'Mardan', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'Hazara Division', 'Abbottabad', 'Abbottabad', 'Abbottabad', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'Malakand Division', 'Swat', 'Mingora', 'Mingora / Swat', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'Kohat Division', 'Kohat', 'Kohat', 'Kohat', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'D.I. Khan Division', 'Dera Ismail Khan', 'D.I. Khan', 'D.I. Khan', 'Active', 0),
        ('Khyber Pakhtunkhwa', 'Hazara Division', 'Mansehra', 'Mansehra', 'Mansehra', 'Active', 0),

        # Balochistan
        ('Balochistan', 'Quetta Division', 'Quetta', 'Quetta City', 'Quetta', 'Active', 0),
        ('Balochistan', 'Makran Division', 'Gwadar', 'Gwadar Port City', 'Gwadar', 'Active', 0),
        ('Balochistan', 'Makran Division', 'Turbat', 'Turbat', 'Turbat', 'Active', 0),
        ('Balochistan', 'Kalat Division', 'Khuzdar', 'Khuzdar', 'Khuzdar', 'Active', 0),
        ('Balochistan', 'Lasbela Division', 'Hub', 'Hub Chowki', 'Hub', 'Active', 0),
        ('Balochistan', 'Quetta Division', 'Chaman', 'Chaman', 'Chaman', 'Active', 0),

        # Islamabad Capital Territory
        ('Islamabad Capital Territory', 'Federal Capital', 'Islamabad', 'Islamabad Urban', 'Islamabad', 'Active', 0),

        # Azad Jammu & Kashmir (AJK)
        ('Azad Jammu and Kashmir', 'Muzaffarabad Division', 'Muzaffarabad', 'Muzaffarabad', 'Muzaffarabad', 'Active', 0),
        ('Azad Jammu and Kashmir', 'Mirpur Division', 'Mirpur', 'Mirpur City', 'Mirpur', 'Active', 0),
        ('Azad Jammu and Kashmir', 'Poonch Division', 'Rawalakot', 'Rawalakot', 'Rawalakot', 'Active', 0),

        # Gilgit-Baltistan (GB)
        ('Gilgit-Baltistan', 'Gilgit Division', 'Gilgit', 'Gilgit City', 'Gilgit', 'Active', 0),
        ('Gilgit-Baltistan', 'Baltistan Division', 'Skardu', 'Skardu City', 'Skardu', 'Active', 0),
        ('Gilgit-Baltistan', 'Gilgit Division', 'Hunza', 'Karimabad / Aliabad', 'Hunza', 'Active', 0)
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO administrative_regions 
        (province, division, district, tehsil, city, status, total_businesses_discovered)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, regions)

    # 3. Seed Existing POS Vendors in Pakistan
    pos_vendors = [
        (
            'Blink Technologies', 'BlinkPOS', 'https://blinkco.io',
            '+92 42 111 254 652', '+92 300 0702546',
            'SaaS Monthly / Tiered Enterprise', 'Subscription + Commission options',
            'Cloud POS, Delivery dispatch & fleet rider app, branded consumer ordering mobile apps, multi-branch inventory, recipe costing, Blink Pay financial reconciliation',
            1, 'Enterprise QSR chains, multi-location franchises, high delivery volume restaurants'
        ),
        (
            'Oscar Technologies', 'Oscar POS', 'https://oscar.pk',
            '+92 21 387 72222', '+92 311 1167227',
            'Freemium / Monthly Tiered (PKR 2,500 - 6,500/mo)', 'Monthly / Annual SaaS',
            'Full offline billing mode with cloud auto-sync, FBR and provincial PRA/SRB tax invoice integration with QR codes, KOT printer routing, JazzCash/Easypaisa local payment gateway, Foodpanda menu integration',
            1, 'Small-to-medium restaurants, independent cafes, bakeries, fast food points'
        ),
        (
            'Tossdown Inc.', 'Tossdown Platform', 'https://tossdown.com',
            '+92 42 357 81100', '+92 321 8677369',
            'Enterprise Custom SaaS + Onboarding', 'Subscription SaaS',
            'Centralized multi-channel POS integration, automated customer CRM & retention marketing, loyalty points, WhatsApp/SMS marketing campaigns, self-ordering kiosks, custom branded web & mobile app',
            1, 'Established restaurant groups, fine dining, scaling regional and international franchises'
        ),
        (
            'FoodBucket Software', 'FoodBucket', 'https://foodbucket.io',
            '+92 304 111 3663', '+92 304 1113663',
            'Monthly Subscription (PKR 3,500 - 8,000/mo)', 'Monthly SaaS',
            'Kitchen Order Ticket (KOT) automation, Kitchen Display Systems (KDS), table management, inventory raw material consumption deductions, third-party delivery aggregation',
            1, 'Fast food outlets, pizza chains, dine-in family restaurants'
        ),
        (
            'Indolj', 'Indolj Restaurant Engine', 'https://indolj.pk',
            '+92 21 343 20555', '+92 300 8274646',
            'Base Monthly + Transaction fee', 'SaaS',
            'Online ordering engine, native POS terminal, delivery driver tracking, menu catalog management, real-time sales reporting',
            1, 'Takeaway and delivery-centric restaurants, burger joints, cloud kitchens'
        ),
        (
            'LumenSoft Technologies', 'Candela Retail / Restaurant POS', 'https://candela.pk',
            '+92 42 111 888 777', '+92 321 4455888',
            'One-time License (PKR 45,000 - 95,000) + Annual Support', 'On-Premise Windows Desktop',
            'Robust on-premise offline database, barcoding, inventory control, accounts ledger, supplier management, multi-counter billing',
            1, 'Traditional high-inventory bakeries, sweet marts, departmental store cafeterias'
        ),
        (
            'Restroworks (formerly Posist)', 'Restroworks Cloud POS', 'https://www.restroworks.com',
            '+92 21 111 767 478', '+92 301 8292888',
            'Enterprise SaaS / Outlet basis', 'Annual Subscription',
            'Global cloud restaurant management platform, enterprise recipe management, franchise royalty reporting, kitchen display systems, inventory stock transfer',
            1, 'High-end fine dining, international franchise operators, multi-city restaurant groups'
        ),
        (
            'CloudCafe POS', 'CloudCafe', 'https://cloudcafe.pk',
            '+92 333 4567890', '+92 333 4567890',
            'Affordable SaaS (PKR 2,000 - 4,500/mo)', 'Monthly Subscription',
            'Simple touch billing, table layout builder, thermal printer support, daily sales summary WhatsApp notifications',
            1, 'Local cafes, tea bars, small pizza shops, fast-food startups'
        )
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO pos_providers 
        (vendor_name, product_name, website, sales_contact, sales_whatsapp, pricing_model, subscription_model, product_features, local_fbr_compliant, market_positioning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pos_vendors)

    # 4. Seed Research Sources
    sources = [
        ('Pakistan Bureau of Statistics (PBS)', 'Government Statistical Census', 'https://www.pbs.gov.pk', 'High'),
        ('Punjab Food Authority (PFA)', 'Provincial Food Safety Registry', 'https://pfa.gop.pk', 'High'),
        ('Sindh Food Authority (SFA)', 'Provincial Food Safety Registry', 'https://sfa.gos.pk', 'High'),
        ('Khyber Pakhtunkhwa Food Safety Authority', 'Provincial Food Safety Registry', 'https://kpfshfa.gov.pk', 'High'),
        ('Balochistan Food Authority (BFA)', 'Provincial Food Safety Registry', 'https://bfa.gob.pk', 'High'),
        ('Federal Board of Revenue (FBR) POS System', 'Tax Integration Registry', 'https://www.fbr.gov.pk/pos-integrated-retailers/163085/163089', 'High'),
        ('OpenStreetMap (OSM) Pakistan Geodatabase', 'Global Geospatial Registry', 'https://www.openstreetmap.org', 'High'),
        ('Pakistan Tourism Development Corporation (PTDC)', 'Tourism & Hospitality Registry', 'https://tourism.gov.pk', 'High'),
        ('Chambers of Commerce (LCCI, KCCI, ICCI)', 'Commercial Business Registries', 'https://lcci.com.pk', 'Medium-High')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO research_sources (source_name, source_type, base_url, reliability_rating)
        VALUES (?, ?, ?, ?)
    """, sources)

    conn.commit()

if __name__ == '__main__':
    init_db()
