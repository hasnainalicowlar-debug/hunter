-- Pakistan Food Service & POS Intelligence Platform - PostgreSQL + PostGIS DDL Schema
-- Compatible with PostgreSQL 14+ and PostGIS 3+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- 1. Administrative Regions
CREATE TABLE IF NOT EXISTS administrative_regions (
    region_id SERIAL PRIMARY KEY,
    province VARCHAR(100) NOT NULL,
    division VARCHAR(100),
    district VARCHAR(100) NOT NULL,
    tehsil VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    total_businesses_discovered INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Business Categories
CREATE TABLE IF NOT EXISTS business_categories (
    category_id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    default_pos_opportunity VARCHAR(50) DEFAULT 'Medium'
);

-- 3. Research Sources
CREATE TABLE IF NOT EXISTS research_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(150) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    base_url VARCHAR(255),
    reliability_rating VARCHAR(50) DEFAULT 'High',
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- 4. POS Software Vendors in Pakistan
CREATE TABLE IF NOT EXISTS pos_providers (
    provider_id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(150) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    website VARCHAR(255),
    sales_contact VARCHAR(100),
    sales_whatsapp VARCHAR(100),
    pricing_model VARCHAR(150),
    subscription_model VARCHAR(100),
    product_features TEXT,
    local_fbr_compliant BOOLEAN DEFAULT TRUE,
    market_positioning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Businesses Core Table
CREATE TABLE IF NOT EXISTS businesses (
    business_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    category_id INT REFERENCES business_categories(category_id),
    category_name VARCHAR(100),
    subcategory VARCHAR(100),
    business_description TEXT,
    is_franchise BOOLEAN DEFAULT FALSE,
    parent_company VARCHAR(255),
    year_established INT,
    operating_status VARCHAR(50) DEFAULT 'Open',
    business_size VARCHAR(50) DEFAULT 'Small',
    verification_status VARCHAR(50) DEFAULT 'Verified',
    data_confidence INT DEFAULT 85,
    pos_opportunity_score VARCHAR(50) DEFAULT 'Medium',
    pos_opportunity_reasons TEXT,
    lead_priority VARCHAR(10) DEFAULT 'P3',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Business Branches
CREATE TABLE IF NOT EXISTS business_branches (
    branch_id VARCHAR(64) PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_name VARCHAR(255) NOT NULL,
    branch_code VARCHAR(50),
    is_headquarters BOOLEAN DEFAULT FALSE,
    opening_date DATE,
    phone VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Business Contacts
CREATE TABLE IF NOT EXISTS business_contacts (
    contact_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id VARCHAR(64),
    phone VARCHAR(100),
    alternative_phone VARCHAR(100),
    whatsapp VARCHAR(100),
    whatsapp_status VARCHAR(50) DEFAULT 'Needs Verification',
    whatsapp_source VARCHAR(255),
    whatsapp_link VARCHAR(255),
    email VARCHAR(150),
    support_email VARCHAR(150),
    website VARCHAR(255),
    contact_page_url VARCHAR(255),
    online_ordering_url VARCHAR(255),
    menu_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Locations with PostGIS Geography
CREATE TABLE IF NOT EXISTS locations (
    location_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id VARCHAR(64),
    country VARCHAR(100) DEFAULT 'Pakistan',
    province VARCHAR(100) NOT NULL,
    division VARCHAR(100),
    district VARCHAR(100) NOT NULL,
    tehsil VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    area VARCHAR(150),
    market VARCHAR(150),
    neighborhood VARCHAR(150),
    full_address TEXT,
    nearby_landmark VARCHAR(255),
    postal_code VARCHAR(20),
    google_maps_url TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geom GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Social Profiles
CREATE TABLE IF NOT EXISTS social_profiles (
    profile_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL,
    handle VARCHAR(100),
    follower_range VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Websites
CREATE TABLE IF NOT EXISTS websites (
    website_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    url VARCHAR(255) NOT NULL,
    has_online_ordering BOOLEAN DEFAULT FALSE,
    ordering_system_detected VARCHAR(100),
    ssl_valid BOOLEAN DEFAULT TRUE,
    cms_platform VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Menus
CREATE TABLE IF NOT EXISTS menus (
    menu_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    menu_url TEXT,
    price_range VARCHAR(20) DEFAULT '$$',
    cuisines TEXT,
    opening_hours VARCHAR(50),
    closing_hours VARCHAR(50),
    weekly_closing_day VARCHAR(50),
    dine_in BOOLEAN DEFAULT TRUE,
    takeaway BOOLEAN DEFAULT TRUE,
    delivery BOOLEAN DEFAULT TRUE,
    table_reservations BOOLEAN DEFAULT FALSE,
    online_ordering BOOLEAN DEFAULT FALSE,
    seating_capacity INT,
    number_of_employees INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Existing POS Information
CREATE TABLE IF NOT EXISTS existing_pos_info (
    info_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id VARCHAR(64),
    pos_provider_id INT REFERENCES pos_providers(provider_id),
    pos_provider_name VARCHAR(150) DEFAULT 'Unknown',
    is_pos_verified BOOLEAN DEFAULT FALSE,
    evidence_source TEXT,
    evidence_url TEXT,
    detected_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. Active POS Buyer Intent Signals
CREATE TABLE IF NOT EXISTS pos_buyer_intent_signals (
    intent_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) REFERENCES businesses(business_id) ON DELETE SET NULL,
    business_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(100),
    whatsapp VARCHAR(100),
    website_url VARCHAR(255),
    intent_tier VARCHAR(50) NOT NULL,
    requirement_type VARCHAR(150) NOT NULL,
    source_platform VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    original_post_date VARCHAR(50),
    discovered_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    evidence_summary TEXT NOT NULL,
    verification_status VARCHAR(50) DEFAULT 'Verified',
    lead_priority VARCHAR(10) DEFAULT 'P1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. New Business Announcements
CREATE TABLE IF NOT EXISTS new_business_announcements (
    announcement_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) REFERENCES businesses(business_id) ON DELETE SET NULL,
    business_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    area VARCHAR(150),
    category VARCHAR(100) NOT NULL,
    announcement_type VARCHAR(50) NOT NULL,
    announcement_date VARCHAR(50),
    opening_date VARCHAR(50),
    contact_phone VARCHAR(100),
    website_url VARCHAR(255),
    source_url TEXT NOT NULL,
    verification_status VARCHAR(50) DEFAULT 'Verified',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. Sales Leads CRM
CREATE TABLE IF NOT EXISTS sales_leads (
    lead_id SERIAL PRIMARY KEY,
    business_id VARCHAR(64) NOT NULL UNIQUE REFERENCES businesses(business_id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    city VARCHAR(100),
    lead_priority VARCHAR(10) NOT NULL DEFAULT 'P2',
    pipeline_stage VARCHAR(50) NOT NULL DEFAULT 'New Lead',
    pos_opportunity_score VARCHAR(50) DEFAULT 'High',
    opportunity_reasons TEXT,
    assigned_rep VARCHAR(100) DEFAULT 'Unassigned',
    last_contact_date VARCHAR(50),
    next_followup_date VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostGIS Spatial Index & Standard B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category_id);
CREATE INDEX IF NOT EXISTS idx_locations_city ON locations(city);
CREATE INDEX IF NOT EXISTS idx_locations_province ON locations(province);
CREATE INDEX IF NOT EXISTS idx_businesses_lead_priority ON businesses(lead_priority);
CREATE INDEX IF NOT EXISTS idx_contacts_whatsapp ON business_contacts(whatsapp);
