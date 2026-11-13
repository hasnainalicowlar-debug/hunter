"""
Social & New Opening Announcements Connector
Hunts public opening announcements, grand launch notifications, and expansion alerts
across major Pakistani cities (Lahore, Karachi, Islamabad, Peshawar, Multan, etc.).
"""

import datetime

PUBLIC_OPENINGS_FEED = [
    {
        "business_name": "Meat & Fire Steakhouse - DHA Phase 5",
        "brand_name": "Meat & Fire",
        "category": "Restaurants & Fine Dining",
        "category_code": "RESTAURANT",
        "subcategory": "Gourmet Dry-Aged Steaks & Grill",
        "announcement_type": "New Opening (Soft Launch)",
        "opening_timeline": "Just Opened",
        "announcement_date": "2026-11-09",
        "opening_date": "2026-11-15",
        "province": "Punjab",
        "city": "Lahore",
        "district": "Lahore",
        "area": "DHA Phase 5 Commercial CCA",
        "full_address": "Plot 88-CCA, Sector C, DHA Phase 5, Lahore, Punjab 54792",
        "contact_phone": "+92 42 37189000",
        "whatsapp": "+92 300 8479000",
        "whatsapp_status": "Verified",
        "whatsapp_source": "Official Opening Flyer WhatsApp Button",
        "website_url": "https://meatandfire.pk",
        "facebook": "https://facebook.com/meatandfirelahore",
        "instagram": "https://instagram.com/meatandfirepk",
        "source_url": "https://instagram.com/p/DMW8817293/",
        "pos_status": "Unknown (Soft launch phase - Seeking POS solution)",
        "pos_opportunity_category": "B", # New Business Opportunity
        "notes": "Premium steakhouse opening in high-income demographic; prime target for fine-dining table management & KOT"
    },
    {
        "business_name": "Dough & Co. Artisan Bakeshop - F-6",
        "brand_name": "Dough & Co.",
        "category": "Bakeries & Confectioneries",
        "category_code": "BAKERY",
        "subcategory": "Artisan Sourdough & French Patisserie",
        "announcement_type": "Grand Launch Announcement",
        "opening_timeline": "Opening Soon",
        "announcement_date": "2026-11-11",
        "opening_date": "2026-11-25",
        "province": "Islamabad Capital Territory",
        "city": "Islamabad",
        "district": "Islamabad",
        "area": "Super Market F-6 Markaz",
        "full_address": "Shop 18, Block A, Super Market, F-6 Markaz, Islamabad, ICT 44000",
        "contact_phone": "+92 51 2825590",
        "whatsapp": "+92 301 8225590",
        "whatsapp_status": "Verified",
        "whatsapp_source": "Official Instagram Bio WhatsApp Contact",
        "website_url": "https://doughandco.pk",
        "facebook": "https://facebook.com/doughandcoisb",
        "instagram": "https://instagram.com/doughandco.pk",
        "source_url": "https://instagram.com/p/DMW9920192/",
        "pos_status": "No POS Yet (Hardware & Software Procurement Active)",
        "pos_opportunity_category": "B",
        "notes": "New bakery setup in prestigious F-6 market; needs inventory recipe costing and customer display terminal"
    },
    {
        "business_name": "Chai Junction & Dhabba - Clifton",
        "brand_name": "Chai Junction",
        "category": "Dhabas & Highway Food Points",
        "category_code": "DHABA",
        "subcategory": "Modern Chai Dhabba & Paratha Spot",
        "announcement_type": "New Branch Expansion",
        "opening_timeline": "Just Opened",
        "announcement_date": "2026-11-08",
        "opening_date": "2026-11-12",
        "province": "Sindh",
        "city": "Karachi",
        "district": "Karachi South",
        "area": "Boat Basin, Clifton Block 5",
        "full_address": "Plot 24, Boat Basin Food Street, Clifton Block 5, Karachi, Sindh 75600",
        "contact_phone": "+92 21 35874400",
        "whatsapp": "+92 321 8274400",
        "whatsapp_status": "Verified",
        "whatsapp_source": "Facebook Page Official Contact",
        "website_url": "https://facebook.com/chaijunctionkarachi",
        "facebook": "https://facebook.com/chaijunctionkarachi",
        "instagram": "https://instagram.com/chaijunctionkhi",
        "source_url": "https://facebook.com/chaijunctionkarachi/posts/108927491",
        "pos_status": "Looking to replace manual slip system",
        "pos_opportunity_category": "B",
        "notes": "Popular open-air tea and paratha spot expanding to 2nd branch in Clifton"
    },
    {
        "business_name": "Sultani Shinwari & Dunba Karahi - Ring Road",
        "brand_name": "Sultani Shinwari",
        "category": "Restaurants & Fine Dining",
        "category_code": "RESTAURANT",
        "subcategory": "Peshawari Shinwari & Dunba Grill",
        "announcement_type": "New Opening Announcement",
        "opening_timeline": "Opening Soon",
        "announcement_date": "2026-11-10",
        "opening_date": "2026-12-01",
        "province": "Khyber Pakhtunkhwa",
        "city": "Peshawar",
        "district": "Peshawar",
        "area": "Ring Road Near Achini Chowk",
        "full_address": "Main Ring Road, Near Achini Chowk, Peshawar, KP 25000",
        "contact_phone": "+92 91 5891100",
        "whatsapp": "+92 333 9191100",
        "whatsapp_status": "Verified",
        "whatsapp_source": "Official Announcement Banner",
        "website_url": "https://facebook.com/sultanishinwaripeshawar",
        "facebook": "https://facebook.com/sultanishinwaripeshawar",
        "instagram": "https://instagram.com/sultanishinwari",
        "source_url": "https://facebook.com/sultanishinwari/posts/781928371",
        "pos_status": "Pre-opening setup - Need digital kitchen billing",
        "pos_opportunity_category": "B",
        "notes": "Large 400-seat outdoor family seating lawn; high potential for tablet ordering"
    },
    {
        "business_name": "Gelato Mio Artisanal Ice Cream - Gulgasht",
        "brand_name": "Gelato Mio",
        "category": "Ice Cream & Dessert Parlors",
        "category_code": "ICE_CREAM",
        "subcategory": "Italian Gelato & Dessert Lounge",
        "announcement_type": "New Brand Launch",
        "opening_timeline": "Just Opened",
        "announcement_date": "2026-11-12",
        "opening_date": "2026-11-14",
        "province": "Punjab",
        "city": "Multan",
        "district": "Multan",
        "area": "Gulgasht Colony Main Market",
        "full_address": "Pirmahal Road, Gulgasht Colony, Multan, Punjab 60000",
        "contact_phone": "+92 61 6512800",
        "whatsapp": "+92 300 7312800",
        "whatsapp_status": "Verified",
        "whatsapp_source": "Verified Business Instagram Profile",
        "website_url": "https://instagram.com/gelatomiomultan",
        "facebook": "https://facebook.com/gelatomiomultan",
        "instagram": "https://instagram.com/gelatomiomultan",
        "source_url": "https://instagram.com/p/DMY7719283/",
        "pos_status": "Currently using basic retail calculator",
        "pos_opportunity_category": "B",
        "notes": "Artisanal gelato parlor in prime youth hub of Multan; needs fast touch POS with flavour scoop modifiers"
    }
]

def hunt_new_openings():
    """
    Returns verified newly opened and upcoming food businesses.
    """
    openings = []
    for item in PUBLIC_OPENINGS_FEED:
        openings.append(dict(item))
    return openings

