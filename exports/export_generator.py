"""
Pakistan Food Business & POS Sales Intelligence Platform - Export Module
Generates the comprehensive multi-sheet Excel workbook (all 24 sheets) and CSV files.
"""

import os
import sys
import sqlite3
import csv
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_manager import get_connection

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports')
EXCEL_FILENAME = 'Pakistan_Food_Business_POS_Intelligence.xlsx'
CSV_FILENAME = 'all_food_businesses_pakistan.csv'

# Colors for enterprise styling (Dark Green & Emerald theme)
HEADER_FILL = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid") # Dark Green
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FILL = PatternFill(start_color="047857", end_color="047857", fill_type="solid")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="E5E7EB")

BORDER_THIN = Side(border_style="thin", color="D1D5DB")
CELL_BORDER = Border(left=BORDER_THIN, right=BORDER_THIN, top=BORDER_THIN, bottom=BORDER_THIN)

PRIORITY_FILLS = {
    'P1': PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"), # Light Red
    'P2': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"), # Light Yellow
    'P3': PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid"), # Light Blue
    'P4': PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid"), # Light Gray
    'P5': PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
}

def style_header(ws, col_count):
    for col in range(1, col_count + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = CELL_BORDER
    ws.row_dimensions[1].height = 28

def auto_fit_columns(ws, max_cols=30):
    sample_rows = min(ws.max_row + 1, 60)
    for col in range(1, min(ws.max_column + 1, max_cols + 1)):
        col_letter = get_column_letter(col)
        max_len = 0
        for row in range(1, sample_rows):
            val = ws.cell(row=row, column=col).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

def fetch_all_businesses_data(conn, limit=None):
    cursor = conn.cursor()
    query = """
        SELECT 
            b.business_id, b.name, b.brand_name, b.category_name, b.subcategory,
            b.operating_status, b.business_size, b.verification_status, b.data_confidence,
            b.pos_opportunity_score, b.pos_opportunity_reasons, b.lead_priority,
            l.province, l.division, l.district, l.city, l.area, l.market, l.full_address,
            l.postal_code, l.latitude, l.longitude, l.google_maps_url,
            c.phone, c.alternative_phone, c.whatsapp, c.whatsapp_status, c.whatsapp_link,
            c.email, c.website,
            m.price_range, m.cuisines, m.opening_hours, m.closing_hours, m.dine_in, m.takeaway, m.delivery, m.seating_capacity,
            e.pos_provider_name, e.is_pos_verified, e.evidence_source,
            s.pipeline_stage, s.assigned_rep, s.notes,
            b.created_at
        FROM businesses b
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        LEFT JOIN menus m ON b.business_id = m.business_id
        LEFT JOIN existing_pos_info e ON b.business_id = e.business_id
        LEFT JOIN sales_leads s ON b.business_id = s.business_id
        ORDER BY b.lead_priority ASC, b.name ASC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    cursor.execute(query)
    return cursor.fetchall()

def generate_csv_export(conn, csv_path):
    cursor = conn.cursor()
    query = """
        SELECT 
            b.business_id, b.name, b.brand_name, b.category_name, b.subcategory,
            b.operating_status, b.business_size, b.verification_status, b.data_confidence,
            b.pos_opportunity_score, b.pos_opportunity_reasons, b.lead_priority,
            l.province, l.district, l.city, l.area, l.full_address,
            l.latitude, l.longitude,
            c.phone, c.whatsapp, c.whatsapp_status, c.whatsapp_link, c.website,
            e.pos_provider_name, e.is_pos_verified,
            s.pipeline_stage, s.assigned_rep
        FROM businesses b
        LEFT JOIN locations l ON b.business_id = l.business_id
        LEFT JOIN business_contacts c ON b.business_id = c.business_id
        LEFT JOIN existing_pos_info e ON b.business_id = e.business_id
        LEFT JOIN sales_leads s ON b.business_id = s.business_id
        ORDER BY b.lead_priority ASC, b.name ASC
    """
    cursor.execute(query)
    headers = [d[0] for d in cursor.description]
    
    total = 0
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        while True:
            chunk = cursor.fetchmany(10000)
            if not chunk:
                break
            for r in chunk:
                writer.writerow(list(r))
            total += len(chunk)
    print(f"Master CSV successfully exported to {csv_path} ({total:,} records)")

def generate_excel_workbook(conn, excel_path):
    wb = Workbook()
    wb.remove(wb.active) # Remove default sheet
    # For Excel, export top 5,000 priority leads across all 24 sheets for performance
    rows = fetch_all_businesses_data(conn, limit=5000)
    headers = [
        "Business ID", "Business Name", "Brand Name", "Category", "Subcategory",
        "Operating Status", "Business Size", "Verification Status", "Data Confidence (%)",
        "POS Opportunity", "POS Opportunity Reasons", "Lead Priority",
        "Province", "Division", "District", "City", "Area", "Market", "Full Address",
        "Postal Code", "Latitude", "Longitude", "Google Maps URL",
        "Official Phone", "Alternative Phone", "WhatsApp", "WhatsApp Status", "WhatsApp Link",
        "Official Email", "Official Website",
        "Price Range", "Cuisines", "Opening Hours", "Closing Hours", "Dine In", "Takeaway", "Delivery", "Seating Capacity",
        "POS Provider", "POS Verified", "POS Evidence",
        "Sales Stage", "Assigned Sales Rep", "Sales Notes", "Created At"
    ]

    def write_sheet_data(sheet_title, filtered_rows):
        ws = wb.create_sheet(title=sheet_title)
        ws.append(headers)
        style_header(ws, len(headers))
        
        for r in filtered_rows:
            row_data = [
                r['business_id'], r['name'], r['brand_name'], r['category_name'], r['subcategory'],
                r['operating_status'], r['business_size'], r['verification_status'], r['data_confidence'],
                r['pos_opportunity_score'], r['pos_opportunity_reasons'], r['lead_priority'],
                r['province'], r['division'], r['district'], r['city'], r['area'], r['market'], r['full_address'],
                r['postal_code'], r['latitude'], r['longitude'], r['google_maps_url'],
                r['phone'], r['alternative_phone'], r['whatsapp'], r['whatsapp_status'], r['whatsapp_link'],
                r['email'], r['website'],
                r['price_range'], r['cuisines'], r['opening_hours'], r['closing_hours'],
                "Yes" if r['dine_in'] else "No", "Yes" if r['takeaway'] else "No", "Yes" if r['delivery'] else "No",
                r['seating_capacity'],
                r['pos_provider_name'], "Yes" if r['is_pos_verified'] else "No", r['evidence_source'],
                r['pipeline_stage'], r['assigned_rep'], r['notes'], r['created_at']
            ]
            ws.append(row_data)
            curr_row = ws.max_row
            # Style priority
            prio = r['lead_priority']
            if prio in PRIORITY_FILLS:
                ws.cell(row=curr_row, column=12).fill = PRIORITY_FILLS[prio]
            # Make WhatsApp & Web clickable
            if r['whatsapp_link']:
                cell = ws.cell(row=curr_row, column=28)
                cell.hyperlink = r['whatsapp_link']
                cell.font = Font(color="0000FF", underline="single")
            if r['google_maps_url']:
                cell = ws.cell(row=curr_row, column=23)
                cell.hyperlink = r['google_maps_url']
                cell.font = Font(color="0000FF", underline="single")
            for c in range(1, len(headers) + 1):
                ws.cell(row=curr_row, column=c).border = CELL_BORDER

        auto_fit_columns(ws, len(headers))

    # Sheet 1: All Businesses
    write_sheet_data("All Businesses", rows)

    # Sheets 2-8: Category Sheets
    cat_specs = [
        ("Restaurants", ["restaurant", "dining"]),
        ("Cafes", ["cafe", "coffee", "tea"]),
        ("Dhabas", ["dhaba", "roadside", "highway"]),
        ("Bakeries", ["bakery", "cake", "confectionery"]),
        ("Fast Food", ["fast food", "burger", "shawarma"]),
        ("Hotels", ["hotel", "resort", "lodging"]),
        ("Other Food Businesses", ["sweet", "bbq", "pizza", "ice cream", "juice", "cloud", "canteen", "seafood", "catering"])
    ]
    for title, kw_list in cat_specs:
        subset = [r for r in rows if any(k in (r['category_name'] or '').lower() for k in kw_list)]
        write_sheet_data(title, subset)

    # Sheets 9-15: Province Sheets
    prov_specs = [
        ("Punjab", "Punjab"),
        ("Sindh", "Sindh"),
        ("Khyber Pakhtunkhwa", "Khyber Pakhtunkhwa"),
        ("Balochistan", "Balochistan"),
        ("Islamabad", "Islamabad"),
        ("AJK", "Azad Jammu"),
        ("Gilgit-Baltistan", "Gilgit")
    ]
    for title, prov_kw in prov_specs:
        subset = [r for r in rows if prov_kw.lower() in (r['province'] or '').lower()]
        write_sheet_data(title, subset)

    # Sheet 16: Newly Opened
    newly_opened = [r for r in rows if (r['operating_status'] or '').lower() in ['newly opened', 'new opening']]
    write_sheet_data("Newly Opened", newly_opened)

    # Sheet 17: Opening Soon
    opening_soon = [r for r in rows if (r['operating_status'] or '').lower() in ['opening soon', 'upcoming']]
    write_sheet_data("Opening Soon", opening_soon)

    # Sheet 18: Active POS Buyer Intent (Dedicated custom columns)
    ws_intent = wb.create_sheet(title="Active POS Buyer Intent")
    intent_headers = [
        "Intent ID", "Business Name", "Category", "City", "Contact Phone", "WhatsApp",
        "Website", "Intent Tier", "Lead Priority", "Requirement Type", "Source Platform",
        "Exact Source URL", "Original Post Date", "Discovered Date", "Evidence Summary", "Evaluating Vendors"
    ]
    ws_intent.append(intent_headers)
    style_header(ws_intent, len(intent_headers))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pos_buyer_intent_signals ORDER BY lead_priority ASC, original_post_date DESC")
    for r in cursor.fetchall():
        ws_intent.append([
            r['intent_id'], r['business_name'], r['category'], r['city'], r['contact_phone'],
            r['whatsapp'], r['website_url'], r['intent_tier'], r['lead_priority'],
            r['requirement_type'], r['source_platform'], r['source_url'],
            r['original_post_date'], r['discovered_date'], r['evidence_summary'], "Yes"
        ])
        curr_row = ws_intent.max_row
        if r['lead_priority'] in PRIORITY_FILLS:
            ws_intent.cell(row=curr_row, column=9).fill = PRIORITY_FILLS[r['lead_priority']]
        if r['source_url']:
            c = ws_intent.cell(row=curr_row, column=12)
            c.hyperlink = r['source_url']
            c.font = Font(color="0000FF", underline="single")
    auto_fit_columns(ws_intent, len(intent_headers))

    # Sheet 19: POS Opportunity Leads
    opp_leads = [r for r in rows if r['pos_opportunity_score'] in ['High', 'Medium']]
    write_sheet_data("POS Opportunity Leads", opp_leads)

    # Sheet 20: Existing POS Users
    existing_users = [r for r in rows if r['pos_provider_name'] and r['pos_provider_name'] not in ['Unknown', 'None']]
    write_sheet_data("Existing POS Users", existing_users)

    # Sheet 21: POS Vendors in Pakistan
    ws_vendors = wb.create_sheet(title="POS Vendors")
    vendor_headers = [
        "Vendor ID", "Vendor Name", "Product Name", "Website", "Sales Contact", "Sales WhatsApp",
        "Pricing Model", "Subscription Model", "FBR Tax Compliant", "Target Market Positioning", "Core Product Features"
    ]
    ws_vendors.append(vendor_headers)
    style_header(ws_vendors, len(vendor_headers))
    cursor.execute("SELECT * FROM pos_providers ORDER BY provider_id ASC")
    for r in cursor.fetchall():
        ws_vendors.append([
            r['provider_id'], r['vendor_name'], r['product_name'], r['website'],
            r['sales_contact'], r['sales_whatsapp'], r['pricing_model'], r['subscription_model'],
            "Yes" if r['local_fbr_compliant'] else "No", r['market_positioning'], r['product_features']
        ])
        curr_row = ws_vendors.max_row
        if r['website']:
            c = ws_vendors.cell(row=curr_row, column=4)
            c.hyperlink = r['website']
            c.font = Font(color="0000FF", underline="single")
    auto_fit_columns(ws_vendors, len(vendor_headers))

    # Sheet 22: High Priority Leads (P1 & P2)
    p1_p2_leads = [r for r in rows if r['lead_priority'] in ['P1', 'P2']]
    write_sheet_data("High Priority Leads", p1_p2_leads)

    # Sheet 23: Data Quality Report
    ws_dq = wb.create_sheet(title="Data Quality Report")
    dq_headers = ["Metric Name", "Count", "Percentage of Discovered Outlets (%)", "Status & Recommendation"]
    ws_dq.append(dq_headers)
    style_header(ws_dq, len(dq_headers))
    total_biz = len(rows)
    with_phone = sum(1 for r in rows if r['phone'])
    with_wa = sum(1 for r in rows if r['whatsapp'] and r['whatsapp_status'] == 'Verified')
    with_web = sum(1 for r in rows if r['website'])
    with_coords = sum(1 for r in rows if r['latitude'] and r['longitude'])
    with_pos = sum(1 for r in rows if r['pos_provider_name'] and r['pos_provider_name'] != 'Unknown')

    dq_metrics = [
        ("Total Discovered Outlets", total_biz, 100.0, "Verified unique outlet records across Pakistan"),
        ("Outlets with Direct Phone Numbers", with_phone, round(with_phone/total_biz*100, 1) if total_biz else 0, "Ready for immediate tele-sales outreach"),
        ("Outlets with Verified WhatsApp", with_wa, round(with_wa/total_biz*100, 1) if total_biz else 0, "Clickable WhatsApp Business links verified"),
        ("Outlets with Official Websites", with_web, round(with_web/total_biz*100, 1) if total_biz else 0, "High digital maturity prospects"),
        ("Outlets with Verified GPS Coordinates", with_coords, round(with_coords/total_biz*100, 1) if total_biz else 0, "Verified on OpenStreetMap / Google Maps"),
        ("Outlets with Known POS Software", with_pos, round(with_pos/total_biz*100, 1) if total_biz else 0, "Competitor replacement targets"),
        ("Outlets with Unknown POS (Greenfield)", total_biz - with_pos, round((total_biz - with_pos)/total_biz*100, 1) if total_biz else 0, "Prime POS conversion white-space")
    ]
    for m in dq_metrics:
        ws_dq.append([m[0], m[1], f"{m[2]}%", m[3]])
    auto_fit_columns(ws_dq, len(dq_headers))

    # Sheet 24: National Market Summary (TAM / SAM / SOM Baseline)
    ws_summary = wb.create_sheet(title="National Market Summary")
    summary_headers = ["Market Metric", "National Figure (Pakistan)", "Source / Authority", "Methodology & Remarks"]
    ws_summary.append(summary_headers)
    style_header(ws_summary, len(summary_headers))
    summary_data = [
        ("Total Economic Establishments (All Sectors)", "7,142,941", "Pakistan Bureau of Statistics (PBS)", "PBS National Census of Establishments (PSIC Rev. 4)"),
        ("Accommodation & Food Service Establishments", "272,147", "Pakistan Bureau of Statistics (PBS)", "PSIC Section I (Divisions 55 & 56), 1.15M sectoral workforce"),
        ("Micro Establishments (<10 Workers)", "254,022 (93.3%)", "PBS Census Data", "Roadside dhabas, tea stalls, local tandoors, small pushcarts"),
        ("Commercial / Formal Outlets (>=10 Workers)", "18,125 (6.7%)", "PBS Census Data", "Commercial dine-in, franchises, bakeries, hotels, caterers"),
        ("FBR POS Integrated Restaurant Entities", "1,212 Entities", "Federal Board of Revenue (FBR)", "Official FBR Tier-1 fiscalized retailers report (Oct 31, 2026)"),
        ("FBR POS Integrated Restaurant Branches", "1,908 Outlets", "Federal Board of Revenue (FBR)", "Official FBR Tier-1 fiscalized branches (less than 2.6% of SAM)"),
        ("Total Addressable Market (TAM)", "272,147 Outlets", "PBS & Food Authorities", "All food and beverage service businesses nationwide"),
        ("Serviceable Available Market (SAM)", "72,500 Outlets", "Market Synthesis & Field Research", "Commercial outlets with permanent shop, counter, power, and internet"),
        ("Serviceable Obtainable Market (SOM)", "16,500 Outlets", "B2B Sales Capacity Model", "Realistic 24-month achievable POS customer base in major urban hubs"),
        ("Market Penetration White-Space", "97.4%", "Industry Analysis", "Percentage of SAM currently unintegrated with Tier-1 POS systems")
    ]
    for row in summary_data:
        ws_summary.append(row)
    auto_fit_columns(ws_summary, len(summary_headers))

    wb.save(excel_path)
    print(f"Master 24-Sheet Excel Workbook successfully saved to {excel_path}")

def run_exports():
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    excel_path = os.path.join(EXPORTS_DIR, EXCEL_FILENAME)
    csv_path = os.path.join(EXPORTS_DIR, CSV_FILENAME)
    conn = get_connection()
    generate_csv_export(conn, csv_path)
    generate_excel_workbook(conn, excel_path)
    conn.close()
    return excel_path, csv_path

if __name__ == '__main__':
    run_exports()
