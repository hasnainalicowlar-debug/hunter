"""
Lead Scoring & POS Opportunity Classification Engine
Transparently computes POS Opportunity Scores (High, Medium, Low) and Sales Lead Priorities (P1-P5)
based purely on evidence, avoiding hallucinated numbers or assumptions.
"""

def evaluate_pos_opportunity(business_profile):
    """
    Evaluates inferred operational need for restaurant POS automation.
    Returns (opportunity_score, reasons_list)
    """
    reasons = []
    points = 0

    category = business_profile.get('category_name', '') or business_profile.get('category', '')
    branches_count = business_profile.get('total_branches', 1)
    dine_in = business_profile.get('dine_in', 1)
    takeaway = business_profile.get('takeaway', 1)
    delivery = business_profile.get('delivery', 0)
    has_online_ordering = business_profile.get('has_online_ordering', 0)
    price_range = business_profile.get('price_range', '$$')
    operating_status = business_profile.get('operating_status', 'Open')
    existing_pos = business_profile.get('pos_provider_name', 'Unknown')

    # Category operational complexity
    high_complexity_cats = [
        'Restaurants & Fine Dining', 'Fast Food & QSR', 'Pizza Outlets & Pizzerias',
        'Bakeries & Confectioneries', 'Hotels with Dining Services', 'Cloud Kitchens & Ghost Kitchens'
    ]
    medium_complexity_cats = [
        'Cafes & Coffee Shops', 'Sweet & Halwai Shops (Mithai)', 'BBQ & Sajji Outlets',
        'Food Courts & Plaza Eateries', 'Catering & Event Services'
    ]

    if category in high_complexity_cats:
        points += 30
        reasons.append(f"High-complexity food category ({category}) requiring multi-item kitchen order routing.")
    elif category in medium_complexity_cats:
        points += 20
        reasons.append(f"Moderate operational complexity category ({category}).")
    else:
        points += 10

    # Multi-branch complexity
    if branches_count > 1:
        points += 25
        reasons.append(f"Multi-branch operations ({branches_count} known branches) requires centralized inventory & sales sync.")
    
    # Dual dining modes (Dine-in + Takeaway/Delivery)
    if dine_in and (takeaway or delivery):
        points += 15
        reasons.append("Multi-channel fulfillment (Dine-in + Takeaway/Delivery) requiring split cashier & KOT workflows.")

    # Online ordering presence
    if has_online_ordering or delivery:
        points += 15
        reasons.append("Digital delivery/ordering presence requires integrated aggregator or driver dispatch.")

    # Premium / High-ticket pricing
    if price_range in ['$$$', '$$$$']:
        points += 10
        reasons.append(f"Premium price tier ({price_range}) indicates high average transaction value and formal tax receipting needs.")

    # Opening Soon / Newly Opened bonus
    if operating_status in ['Opening Soon', 'Newly Opened']:
        points += 20
        reasons.append(f"Critical onboarding window: Business is {operating_status} and setting up billing infrastructure.")

    # Existing POS status deduction
    if existing_pos and existing_pos not in ['Unknown', 'None', 'Manual']:
        points -= 20
        reasons.append(f"Already using known POS provider ({existing_pos}). Replacement opportunity only.")

    # Classification
    if points >= 60:
        score = "High"
    elif points >= 35:
        score = "Medium"
    elif points > 15:
        score = "Low"
    else:
        score = "Insufficient Information"

    return score, "; ".join(reasons)

def calculate_lead_priority(has_explicit_intent, intent_tier, opportunity_score, has_verified_contact, is_new_opening):
    """
    Assigns P1-P5 sales follow-up priority:
    - P1: Immediate sales follow-up (Explicit High Intent or Verified New Opening actively seeking POS)
    - P2: Strong potential customer (High Opportunity + Verified Phone/WhatsApp, Medium Intent)
    - P3: Suitable future prospect (Medium Opportunity, Early Intent, Established Business)
    - P4: Low priority (Low Opportunity or already locked with competitor)
    - P5: Insufficient information / Unverified contacts
    """
    if has_explicit_intent and intent_tier in ['High Intent', 'High']:
        return 'P1'
    
    if is_new_opening and opportunity_score == 'High' and has_verified_contact:
        return 'P1'
    
    if has_explicit_intent and intent_tier in ['Medium Intent', 'Medium']:
        return 'P2'

    if opportunity_score == 'High' and has_verified_contact:
        return 'P2'
    
    if opportunity_score == 'Medium' and has_verified_contact:
        return 'P3'
    
    if opportunity_score == 'High' and not has_verified_contact:
        return 'P3'

    if opportunity_score == 'Low':
        return 'P4'

    return 'P5'
