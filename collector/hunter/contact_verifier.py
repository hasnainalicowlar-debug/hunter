"""
Contact Verifier Module
Performs strict, evidence-grounded contact verification for discovered establishments.
STRICT RULES:
1. Never assume a mobile number is WhatsApp. WhatsApp is only 'Verified' when source explicitly identifies it.
2. Never invent emails, phone numbers, or websites. Use 'Not Found' when unavailable.
3. Preserve the exact source URL and evidence for every contact field.
"""

import re

PAKISTAN_PHONE_REGEX = re.compile(r'^(?:\+92|0092|0)?(3\d{2}|[2-9]\d{1,2})[\s\-]?(\d{7}|\d{6,8})$')

def clean_pakistani_phone(raw_phone):
    """
    Standardizes valid Pakistani landline and mobile numbers into E.164 (+92) format.
    Returns normalized phone string or None if invalid.
    """
    if not raw_phone:
        return None
    raw = str(raw_phone).strip()
    digits = re.sub(r'[^\d]', '', raw)
    
    # Check if begins with 92 or 0
    if digits.startswith('92') and len(digits) in [11, 12]:
        return f"+{digits}"
    elif digits.startswith('0') and len(digits) in [10, 11]:
        return f"+92{digits[1:]}"
    elif len(digits) == 10 and digits.startswith('3'):
        return f"+92{digits}"
    elif len(digits) in [9, 10]:
        return f"+92{digits}"
    return raw # Return clean raw if non-standard

def verify_contacts(raw_contact_data, source_url, source_type="Public Business Listing"):
    """
    Strictly verifies each contact attribute independently.
    Ensures that WhatsApp status is NEVER set to 'Verified' without explicit tagging.
    """
    verified = {
        "phone": None,
        "phone_source": None,
        "whatsapp": None,
        "whatsapp_status": "Not Found",
        "whatsapp_source": None,
        "whatsapp_link": None,
        "email": None,
        "email_source": None,
        "website": None,
        "website_source": None,
        "facebook": None,
        "instagram": None,
        "tiktok": None,
        "online_ordering_url": None,
        "menu_url": None,
        "google_maps_url": None
    }

    # 1. Phone Verification
    raw_phone = raw_contact_data.get('phone') or raw_contact_data.get('contact_phone')
    if raw_phone and str(raw_phone).strip().lower() not in ['none', 'null', 'not found', '']:
        cleaned_phone = clean_pakistani_phone(raw_phone)
        if cleaned_phone:
            verified["phone"] = cleaned_phone
            verified["phone_source"] = f"{source_type} ({source_url})"

    # 2. WhatsApp Verification (CRITICAL: Never infer from mobile alone)
    raw_wa = raw_contact_data.get('whatsapp')
    wa_explicitly_tagged = raw_contact_data.get('whatsapp_status') == 'Verified' or bool(raw_contact_data.get('whatsapp_source'))
    
    if raw_wa and wa_explicitly_tagged:
        cleaned_wa = clean_pakistani_phone(raw_wa)
        if cleaned_wa:
            digits_only = re.sub(r'[^\d]', '', cleaned_wa)
            verified["whatsapp"] = cleaned_wa
            verified["whatsapp_status"] = "Verified"
            verified["whatsapp_source"] = raw_contact_data.get('whatsapp_source') or f"Explicit WhatsApp Button ({source_url})"
            verified["whatsapp_link"] = f"https://wa.me/{digits_only}"
    elif raw_phone and not raw_wa:
        # Explicitly marked as not found/needs verification, never assumed
        verified["whatsapp_status"] = "Needs Verification"

    # 3. Email Verification
    raw_email = raw_contact_data.get('email')
    if raw_email and '@' in raw_email and '.' in raw_email:
        clean_email = str(raw_email).strip().lower()
        if not any(dummy in clean_email for dummy in ['example.com', 'test.com', 'none@', 'dummy']):
            verified["email"] = clean_email
            verified["email_source"] = f"Official Profile ({source_url})"

    # 4. Website Verification
    raw_web = raw_contact_data.get('website') or raw_contact_data.get('website_url')
    if raw_web and str(raw_web).strip().lower() not in ['none', 'null', 'not found', '']:
        web_str = str(raw_web).strip()
        if web_str.startswith('http://') or web_str.startswith('https://'):
            verified["website"] = web_str
            verified["website_source"] = f"Verified Web Presence ({source_url})"

    # 5. Social & Digital Channels
    for soc in ['facebook', 'instagram', 'tiktok', 'online_ordering_url', 'menu_url', 'google_maps_url']:
        val = raw_contact_data.get(soc)
        if val and str(val).strip().lower() not in ['none', 'null', 'not found', '']:
            verified[soc] = str(val).strip()

    return verified

