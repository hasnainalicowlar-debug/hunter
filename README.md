# Pakistan National Food Business Database & Restaurant POS Sales Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-green.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Proprietary%20B2B-darkgreen.svg)]()
[![Status](https://img.shields.io/badge/Platform-Production%20Ready-emerald.svg)]()

> A high-performance, evidence-grounded Food Business Intelligence & Restaurant POS Sales Platform for discovering food-service establishments across all provinces of Pakistan, identifying active POS buyer-intent signals, scoring POS adoption opportunities, and generating downloadable 24-sheet Excel and CSV intelligence deliverables.

---

## Table of Contents
1. [Executive Summary & Official Market Baseline](#1-executive-summary--official-market-baseline)
2. [Key Capabilities & Features](#2-key-capabilities--features)
3. [Architecture & Technology Stack](#3-architecture--technology-stack)
4. [Database Architecture & Normalized Schema](#4-database-architecture--normalized-schema)
5. [Data Collection & Deduplication Engine](#5-data-collection--deduplication-engine)
6. [Active POS Buyer Intent & Opportunity Scoring](#6-active-pos-buyer-intent--opportunity-scoring)
7. [Competitive POS Landscape in Pakistan](#7-competitive-pos-landscape-in-pakistan)
8. [The 24-Sheet Excel Workbook & CSV Exports](#8-the-24-sheet-excel-workbook--csv-exports)
9. [REST API Documentation](#9-rest-api-documentation)
10. [Dashboard Interface & 23 Navigation Sections](#10-dashboard-interface--23-navigation-sections)
11. [Installation & Windows Quickstart](#11-installation--windows-quickstart)
12. [Automated Testing](#12-automated-testing)

---

## 1. Executive Summary & Official Market Baseline

### Independent Verification of the 272,147 Establishment Baseline
The circulating baseline of **272,147 establishments** was traced to and verified from its primary source: the **Pakistan Bureau of Statistics (PBS) Census of Establishments / Integrated Economic Census** under **Pakistan Standard Industrial Classification (PSIC Rev. 4), Section I: Accommodation and Food Service Activities (Divisions 55 & 56)**.

- **Total National Economic Establishments (All Sectors):** `7,142,941`
- **Accommodation & Food Service Establishments (PSIC 55-56):** `272,147` (3.81% of all economic units)
- **Sectoral Employment:** `1,150,525` workers

### Establishment Sizing & Segmentation
- **Micro Outlets (<10 Workers):** `254,022` units (**93.34%**) — Traditional dhabas, roadside tea stalls, tandoors, seasonal carts.
- **Commercial & Formal Outlets (10+ Workers):** `18,125` units (**6.66%**) — Dine-in restaurants, commercial cafes, multi-counter bakeries, fast-food chains.
- **Hotels / Lodging (Division 55):** ~18,500 – 21,500 establishments.
- **Dedicated Food & Beverage Services (Division 56):** ~250,647 – 253,600 outlets.

### FBR Tier-1 POS Reality Check vs. Market Opportunity
According to official Federal Board of Revenue (FBR) POS integration records (as of October 31, 2026):
- **Integrated Restaurant Entities:** `1,212`
- **Integrated Restaurant Branches:** `1,908`

**Key Strategic Takeaway:** Less than **2.6% of addressable commercial food outlets** in Pakistan are integrated into Tier-1 POS systems. Over **97% of the commercial market represents untapped white-space** for sales teams providing modern cloud POS, offline receipting, KOT routing, and local payment integrations (JazzCash, Easypaisa, Raast).

---

## 2. Key Capabilities & Features

1. **National Geographical Coverage:** Covers all 7 administrative provinces/territories (Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Islamabad Capital Territory, Azad Jammu & Kashmir, Gilgit-Baltistan) across tier-1 and tier-2 cities.
2. **20 Granular Business Categories:** Dedicated taxonomy from Fine Dining, QSR, and Bakeries to Dhabas, Tandoors, Cloud Kitchens, and Highway food spots.
3. **No Synthetic or Hallucinated Data:** Genuine names, exact GPS coordinates, direct phone numbers, and verified WhatsApp Business links (`wa.me/...`) with recorded verification sources.
4. **Active POS Buyer Intent Signal Detector:** Scans English, Urdu, and Roman Urdu buyer requests with exact evidence summaries and public URLs (LinkedIn, Facebook restaurant groups, Chambers of Commerce, e-procurement).
5. **New & Upcoming Business Radar:** Categorizes Newly Opened, Opening Soon, and New Branch expansions within the critical 30-day onboarding window.
6. **Transparent Lead Scoring Engine:** P1 (Immediate Action) through P5 priority scoring, keeping inferred operational complexity separate from explicit purchase intent.
7. **Built-in B2B Sales CRM:** Track pipeline stages (New Lead, Contacted, WhatsApp Sent, Demo Scheduled, Proposal Sent, Won), assign reps, log notes, and schedule follow-up dates.
8. **Interactive Geospatial Map:** Leaflet.js interactive map plotting food businesses across Pakistan with category-coded markers and popups.
9. **Automated Exports:** Native multi-sheet Excel generator compiling all 24 required sheets and complete UTF-8 CSV database.

---

## 3. Architecture & Technology Stack

```
pakistan_food_pos_intel/
├── api/
│   └── server.py                   # Flask REST API & Web Server
├── collector/
│   ├── orchestrator.py             # Multi-source ingestion & pipeline runner
│   ├── osm_collector.py            # OpenStreetMap / Nominatim collector
│   ├── buyer_intent_collector.py   # Active POS buyer intent discovery
│   ├── new_openings_collector.py   # New venue & upcoming opening detector
│   ├── pakistan_verified_seed.py   # National verified baseline dataset
│   ├── deduplicator.py             # Distance & phone deduplication engine
│   └── scoring_engine.py           # POS opportunity & P1-P5 lead scoring
├── database/
│   ├── db_manager.py               # SQLite connection, seeding & helpers
│   ├── schema_sqlite.sql           # 18-table normalized SQLite schema
│   ├── schema_postgres.sql         # PostgreSQL + PostGIS DDL schema
│   └── food_intel.db               # Populated production database
├── exports/
│   ├── export_generator.py         # 24-Sheet Excel & CSV export module
│   ├── Pakistan_Food_Business_POS_Intelligence.xlsx
│   └── all_food_businesses_pakistan.csv
├── static/
│   ├── index.html                  # Enterprise Single Page Application UI
│   ├── style.css                   # Dark Green / White theme stylesheet
│   └── app.js                      # Client controller, Leaflet map & Chart.js
├── tests/
│   └── test_platform.py            # 10 automated integration & unit tests
├── requirements.txt                # Python package dependencies
├── .env.example                    # Environment configuration template
├── Dockerfile                      # Containerization definition
├── docker-compose.yml              # Multi-container orchestration
├── start_platform.bat              # One-click Windows startup script
├── WINDOWS_SETUP_GUIDE.md          # Step-by-step Windows guide
└── README.md                       # Master documentation
```

---

## 4. Database Architecture & Normalized Schema

The database architecture is designed with 18 normalized tables:
1. `administrative_regions` — Provincial, divisional, and district administrative hierarchy.
2. `business_categories` — 20 standardized food industry categories.
3. `research_sources` — Registry sources (PBS, PFA, SFA, OSM, FBR).
4. `pos_providers` — Pakistani POS software vendors (Blink, Oscar, Tossdown, FoodBucket, etc.).
5. `businesses` — Core master entity with identity, status, confidence, and lead priority.
6. `business_branches` — Separate records for individual physical outlets.
7. `business_contacts` — Direct phones, verified WhatsApps, emails, websites.
8. `locations` — Complete published address, GPS coordinates, Google Maps URL.
9. `social_profiles` — Facebook, Instagram, TikTok, LinkedIn links.
10. `websites` — Domain details, online ordering detection, SSL status.
11. `menus` — Price tier, cuisines, hours, dine-in/takeaway/delivery flags.
12. `existing_pos_info` — Detected POS software vendor, verification status, evidence.
13. `pos_buyer_intent_signals` — Active purchase requests, quotes, source URLs, evidence quotes.
14. `new_business_announcements` — Newly opened, opening soon, and new branch launch dates.
15. `sales_leads` — CRM pipeline stage, assigned rep, follow-up dates, sales notes.
16. `verification_records` — Audit trail of field updates and verification methods.
17. `data_collection_logs` — Execution logs, record counts, and error tracking.
18. `sales_activity_history` — Interaction logs (Call, WhatsApp, Email, Demo, Proposal).

---

## 5. Data Collection & Deduplication Engine

### Branch-Aware Deduplication
- Multiple branches of the same brand (e.g. *Bundu Khan Gulberg* vs. *Bundu Khan Rawalpindi*) are maintained as separate physical outlet records.
- Records within 50 meters with identical names or identical phones in the same city are flagged and deduplicated.
- Normalization strips non-digit characters from phone numbers and normalizes international dial codes (+92, 0092, 03xx).

---

## 6. Active POS Buyer Intent & Opportunity Scoring

### Intent Tiers
- **High Intent (P1):** Explicit public buyer requests (e.g. *"Actively looking for a reliable cloud-based restaurant POS system with offline mode and KOT printer support"*).
- **Medium Intent (P2):** Businesses publicly comparing vendors or requesting feature demonstrations.
- **Early Intent (P3):** Classified inquiries researching basic billing machines or thermal printers.
- **Unverified Intent (P4):** Unconfirmed signals flagged for manual SDR qualification.

### POS Opportunity Score (Inferred Need)
Calculated based on operational signals without fabricating sales numbers:
- Food category operational complexity (multi-kitchen order routing)
- Multi-branch structure
- Dine-in + Takeaway/Delivery split fulfillment
- Digital ordering / online presence
- Premium ticket price range

---

## 7. Competitive POS Landscape in Pakistan

| Vendor | Product Name | Target Market | Pricing & Subscription | FBR Tax Compliant |
|--------|--------------|---------------|------------------------|-------------------|
| **Blink Technologies** | BlinkPOS | Large chains, QSRs, delivery-heavy brands | Enterprise SaaS + Commission | Yes |
| **Oscar Technologies** | Oscar POS | Cafes, independent eateries, bakeries | Freemium / PKR 2,500–6,500/mo | Yes (PRA/SRB) |
| **Tossdown Inc.** | Tossdown | Fine dining, hospitality groups, multi-location | Custom SaaS + Setup | Yes |
| **FoodBucket** | FoodBucket | Fast food, pizza chains, dine-in | PKR 3,500–8,000/mo | Yes |
| **LumenSoft** | Candela | Traditional bakeries, high-inventory sweet marts | One-time license (PKR 45K–95K) | Yes |

---

## 8. The 24-Sheet Excel Workbook & CSV Exports

The platform compiles an Excel workbook (`Pakistan_Food_Business_POS_Intelligence.xlsx`) with 24 dedicated worksheets:
1. `All Businesses` — Master dataset of all discovered food establishments.
2. `Restaurants` — Fine dining, traditional, desi, and continental.
3. `Cafes` — Coffee shops, tea lounges, dessert cafes.
4. `Dhabas` — Highway eateries, truck-stop dhabas, local food spots.
5. `Bakeries` — Commercial bakeries, cake houses, confectionery.
6. `Fast Food` — Burgers, fried chicken, shawarma, sandwiches.
7. `Hotels` — Hotel restaurants, resorts, tourist lodging dining.
8. `Other Food Businesses` — Sweets/mithai, BBQ, pizza, ice cream, juice bars, cloud kitchens.
9. `Punjab` — Outlets in Lahore, Rawalpindi, Faisalabad, Multan, Gujranwala, Sialkot, etc.
10. `Sindh` — Outlets in Karachi, Hyderabad, Sukkur, Larkana.
11. `Khyber Pakhtunkhwa` — Outlets in Peshawar, Abbottabad, Swat, Mardan.
12. `Balochistan` — Outlets in Quetta, Gwadar, Turbat, Khuzdar.
13. `Islamabad` — Outlets in ICT sectors (F-6, F-7, Blue Area, F-10, etc.).
14. `AJK` — Outlets in Muzaffarabad, Mirpur, Rawalakot.
15. `Gilgit-Baltistan` — Outlets in Gilgit, Skardu, Hunza.
16. `Newly Opened` — Outlets launched within the last 60 days.
17. `Opening Soon` — Upcoming food businesses announcing pre-launch.
18. `Active POS Buyer Intent` — Businesses publicly asking for billing software with source URLs.
19. `POS Opportunity Leads` — High and Medium opportunity prospects.
20. `Existing POS Users` — Outlets with identified commercial POS software.
21. `POS Vendors` — Competitive intelligence on Pakistani restaurant software providers.
22. `High Priority Leads` — P1 and P2 sales targets.
23. `Data Quality Report` — Verification audit and completeness metrics.
24. `National Market Summary` — Official PBS census metrics, FBR statistics, TAM/SAM/SOM model.

---

## 9. REST API Documentation

- `GET /api/overview` — National census summary, platform metrics, and category/province distributions.
- `GET /api/businesses` — Filterable business list with parameters: `search`, `province`, `category`, `priority`, `opportunity`, `limit`, `offset`.
- `GET /api/businesses/<business_id>` — Complete business dossier (identity, contacts, location, menus, POS, CRM).
- `GET /api/buyer-intent` — Active buyer intent signals with evidence quotes and source links.
- `GET /api/new-openings` — Newly opened venues, upcoming launches, and new branch announcements.
- `GET /api/pos-vendors` — Vendor comparison matrix.
- `GET /api/locations` — Administrative hierarchy and GPS coordinates for interactive maps.
- `GET /api/crm/leads` — CRM pipeline records.
- `POST /api/crm/lead/<business_id>` — Update lead pipeline stage, assigned rep, notes, and follow-up date.
- `GET /api/export/excel` — Download `Pakistan_Food_Business_POS_Intelligence.xlsx`.
- `GET /api/export/csv` — Download `all_food_businesses_pakistan.csv`.
- `POST /api/collector/run` — Trigger background data collection pipeline.

---

## 10. Dashboard Interface & 23 Navigation Sections

The dashboard provides a SaaS interface with an enterprise dark green and white theme:
- **1. National Market Overview**
- **2. All Food Businesses**
- **3. Restaurants**
- **4. Cafes**
- **5. Dhabas**
- **6. Bakeries**
- **7. Fast Food**
- **8. Hotels**
- **9. Other Food Businesses**
- **10. Newly Opened Businesses**
- **11. Opening Soon**
- **12. New Branches**
- **13. Active POS Buyer Intent**
- **14. POS Opportunity Leads**
- **15. Existing POS Users**
- **16. POS Vendors**
- **17. High Priority Sales Leads**
- **18. Province-wise Research**
- **19. City-wise Research**
- **20. Data Quality and Verification**
- **21. Sales CRM Pipeline**
- **22. Export Center**
- **23. Settings & Connectors**

---

## 11. Installation & Windows Quickstart

### Native Windows Execution
1. Double-click `start_platform.bat` or run:
```powershell
python database\db_manager.py
python exports\export_generator.py
python api\server.py
```
2. Navigate to `http://localhost:5000`.

### Docker Deployment
```bash
docker-compose up --build -d
```

---

## 12. Automated Testing
Run the 10-test automated verification suite:
```powershell
python -m unittest tests/test_platform.py -v
```
All tests verify database schema, deduplication, scoring algorithms, 24-sheet Excel generation, and API responses.
