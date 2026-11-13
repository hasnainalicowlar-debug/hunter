-- Pakistan Food Service & POS Intelligence Platform - SQLite Schema
PRAGMA foreign_keys = ON;

-- 1. Administrative Regions Hierarchy
CREATE TABLE IF NOT EXISTS administrative_regions (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    province TEXT NOT NULL,
    division TEXT,
    district TEXT NOT NULL,
    tehsil TEXT,
    city TEXT NOT NULL,
    status TEXT DEFAULT 'Pending', -- Completed, Partially Completed, Pending, Unavailable
    total_businesses_discovered INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Business Categories
CREATE TABLE IF NOT EXISTS business_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    icon TEXT,
    description TEXT,
    default_pos_opportunity TEXT DEFAULT 'Medium'
);

-- 3. Research Sources
CREATE TABLE IF NOT EXISTS research_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    reliability_rating TEXT DEFAULT 'High',
    last_accessed DATETIME
);

-- 4. POS Software Vendors in Pakistan
CREATE TABLE IF NOT EXISTS pos_providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    website TEXT,
    sales_contact TEXT,
    sales_whatsapp TEXT,
    pricing_model TEXT,
    subscription_model TEXT,
    product_features TEXT,
    local_fbr_compliant INTEGER DEFAULT 1,
    market_positioning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Businesses (Core Table)
CREATE TABLE IF NOT EXISTS businesses (
    business_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand_name TEXT,
    category_id INTEGER REFERENCES business_categories(category_id),
    category_name TEXT,
    subcategory TEXT,
    business_description TEXT,
    is_franchise INTEGER DEFAULT 0,
    parent_company TEXT,
    year_established INTEGER,
    operating_status TEXT DEFAULT 'Open', -- Open, Opening Soon, Renovating, Closed
    business_size TEXT DEFAULT 'Small', -- Micro, Small, Medium, Large, Enterprise
    verification_status TEXT DEFAULT 'Verified', -- Verified, Partially Verified, Needs Verification, Not Found
    data_confidence INTEGER DEFAULT 85, -- 0-100%
    pos_opportunity_score TEXT DEFAULT 'Medium', -- High, Medium, Low, Insufficient Information
    pos_opportunity_reasons TEXT,
    lead_priority TEXT DEFAULT 'P3', -- P1, P2, P3, P4, P5
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Business Branches (Outlets)
CREATE TABLE IF NOT EXISTS business_branches (
    branch_id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    branch_code TEXT,
    is_headquarters INTEGER DEFAULT 0,
    opening_date TEXT,
    phone TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. Business Contacts
CREATE TABLE IF NOT EXISTS business_contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id TEXT,
    phone TEXT,
    alternative_phone TEXT,
    whatsapp TEXT,
    whatsapp_status TEXT DEFAULT 'Needs Verification', -- Verified, Partially Verified, Needs Verification, Not Found
    whatsapp_source TEXT,
    whatsapp_link TEXT,
    email TEXT,
    support_email TEXT,
    website TEXT,
    contact_page_url TEXT,
    online_ordering_url TEXT,
    menu_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. Locations
CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id TEXT,
    country TEXT DEFAULT 'Pakistan',
    province TEXT NOT NULL,
    division TEXT,
    district TEXT NOT NULL,
    tehsil TEXT,
    city TEXT NOT NULL,
    area TEXT,
    market TEXT,
    neighborhood TEXT,
    full_address TEXT,
    nearby_landmark TEXT,
    postal_code TEXT,
    google_maps_url TEXT,
    latitude REAL,
    longitude REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 9. Social Profiles
CREATE TABLE IF NOT EXISTS social_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- Facebook, Instagram, TikTok, LinkedIn, YouTube
    url TEXT NOT NULL,
    handle TEXT,
    follower_range TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. Websites
CREATE TABLE IF NOT EXISTS websites (
    website_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    has_online_ordering INTEGER DEFAULT 0,
    ordering_system_detected TEXT,
    ssl_valid INTEGER DEFAULT 1,
    cms_platform TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 11. Menus and Operating Profiles
CREATE TABLE IF NOT EXISTS menus (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    menu_url TEXT,
    price_range TEXT DEFAULT '$$', -- $, $$, $$$, $$$$
    cuisines TEXT,
    opening_hours TEXT,
    closing_hours TEXT,
    weekly_closing_day TEXT,
    dine_in INTEGER DEFAULT 1,
    takeaway INTEGER DEFAULT 1,
    delivery INTEGER DEFAULT 1,
    table_reservations INTEGER DEFAULT 0,
    online_ordering INTEGER DEFAULT 0,
    seating_capacity INTEGER,
    number_of_employees INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 12. Existing POS Information
CREATE TABLE IF NOT EXISTS existing_pos_info (
    info_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    branch_id TEXT,
    pos_provider_id INTEGER REFERENCES pos_providers(provider_id),
    pos_provider_name TEXT DEFAULT 'Unknown',
    is_pos_verified INTEGER DEFAULT 0,
    evidence_source TEXT,
    evidence_url TEXT,
    detected_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 13. Active POS Buyer Intent Signals
CREATE TABLE IF NOT EXISTS pos_buyer_intent_signals (
    intent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT REFERENCES businesses(business_id) ON DELETE SET NULL,
    business_name TEXT NOT NULL,
    category TEXT,
    city TEXT NOT NULL,
    contact_phone TEXT,
    whatsapp TEXT,
    website_url TEXT,
    intent_tier TEXT NOT NULL, -- High Intent, Medium Intent, Early Intent, Unverified Intent
    requirement_type TEXT NOT NULL, -- New Restaurant Setup, Replace Legacy Software, Inventory & KOT, Cloud Billing, Quotation Request
    source_platform TEXT NOT NULL, -- Facebook Group, LinkedIn, Procurement Notice, Google Discussion, Vendor Request
    source_url TEXT NOT NULL,
    original_post_date TEXT,
    discovered_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    evidence_summary TEXT NOT NULL,
    verification_status TEXT DEFAULT 'Verified',
    lead_priority TEXT DEFAULT 'P1',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 14. New Business Announcements
CREATE TABLE IF NOT EXISTS new_business_announcements (
    announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT REFERENCES businesses(business_id) ON DELETE SET NULL,
    business_name TEXT NOT NULL,
    city TEXT NOT NULL,
    area TEXT,
    category TEXT NOT NULL,
    announcement_type TEXT NOT NULL, -- Newly Opened, Opening Soon, New Branch, Brand Launch
    announcement_date TEXT,
    opening_date TEXT,
    contact_phone TEXT,
    website_url TEXT,
    source_url TEXT NOT NULL,
    verification_status TEXT DEFAULT 'Verified',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 15. Sales Leads (CRM Engine)
CREATE TABLE IF NOT EXISTS sales_leads (
    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE REFERENCES businesses(business_id) ON DELETE CASCADE,
    business_name TEXT NOT NULL,
    category TEXT,
    city TEXT,
    lead_priority TEXT NOT NULL DEFAULT 'P2', -- P1, P2, P3, P4, P5
    pipeline_stage TEXT NOT NULL DEFAULT 'New Lead', -- New Lead, Verified Lead, Contacted, WhatsApp Sent, Call Completed, Demo Requested, Demo Scheduled, Proposal Sent, Negotiation, Won, Not Interested, Follow-up Required, Invalid Contact
    pos_opportunity_score TEXT DEFAULT 'High',
    opportunity_reasons TEXT,
    assigned_rep TEXT DEFAULT 'Unassigned',
    last_contact_date TEXT,
    next_followup_date TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 16. Verification Records (Audit Trail)
CREATE TABLE IF NOT EXISTS verification_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    verification_field TEXT NOT NULL,
    previous_value TEXT,
    verified_value TEXT,
    verifier_type TEXT DEFAULT 'System', -- System, Analyst, Field Agent
    verification_method TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 17. Data Collection Logs
CREATE TABLE IF NOT EXISTS data_collection_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    source TEXT NOT NULL,
    region TEXT,
    status TEXT NOT NULL, -- Success, Failed, Partial
    records_fetched INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    duplicates_skipped INTEGER DEFAULT 0,
    errors TEXT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME
);

-- 18. Sales Activity History
CREATE TABLE IF NOT EXISTS sales_activity_history (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER REFERENCES sales_leads(lead_id) ON DELETE CASCADE,
    business_id TEXT REFERENCES businesses(business_id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- Call, WhatsApp, Email, Visit, Demo, Proposal
    summary TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    outcome TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for fast querying & filtering
CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category_id);
CREATE INDEX IF NOT EXISTS idx_businesses_city ON locations(city);
CREATE INDEX IF NOT EXISTS idx_businesses_province ON locations(province);
CREATE INDEX IF NOT EXISTS idx_businesses_lead_priority ON businesses(lead_priority);
CREATE INDEX IF NOT EXISTS idx_businesses_pos_score ON businesses(pos_opportunity_score);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_contacts_whatsapp ON business_contacts(whatsapp);
CREATE INDEX IF NOT EXISTS idx_buyer_intent_tier ON pos_buyer_intent_signals(intent_tier);
CREATE INDEX IF NOT EXISTS idx_sales_leads_stage ON sales_leads(pipeline_stage);


-- ============================================================================
-- MODULE: AI-POWERED DAILY RESTAURANT DISCOVERY & POS SALES LEAD HUNTER
-- ============================================================================

-- 19. Hunter Jobs
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
);

-- 20. Hunter Schedules & Configuration
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
);

-- 21. Daily Intelligence Reports
CREATE TABLE IF NOT EXISTS daily_hunter_reports (
    report_id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES hunter_jobs(job_id),
    report_date TEXT NOT NULL,
    report_title TEXT NOT NULL,
    summary_json TEXT,
    markdown_content TEXT NOT NULL,
    is_sent INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 22. Human Review Queue
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
);

-- 23. Record Change History (Audit Log)
CREATE TABLE IF NOT EXISTS record_change_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL REFERENCES businesses(business_id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    source_url TEXT,
    change_type TEXT DEFAULT 'auto_update', -- auto_update, human_approved, manual_edit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 24. Hunter Notifications
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
);

-- 25. Source Checkpoints
CREATE TABLE IF NOT EXISTS source_checkpoints (
    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    last_cursor TEXT,
    last_scanned_at DATETIME,
    items_harvested INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'
);

-- 26. API Budget & Quota Tracking
CREATE TABLE IF NOT EXISTS api_budget_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_date TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    call_count INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0.0,
    daily_limit INTEGER DEFAULT 500,
    UNIQUE(tracking_date, provider_name)
);

CREATE INDEX IF NOT EXISTS idx_hunter_jobs_status ON hunter_jobs(status);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON human_review_queue(status);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON hunter_notifications(is_read);
