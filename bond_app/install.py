import frappe
from frappe.utils import today, add_days, add_months


def after_install():
    try:
        _create_settings()
        _create_rms()
        _create_issuers()
        _create_bonds()
        _create_clients()
        frappe.db.commit()
        frappe.msgprint("Bond App installed successfully with sample data!")
    except Exception as e:
        frappe.log_error(str(e), "bond_app_install")


def _safe_insert(doc_dict):
    try:
        doc = frappe.get_doc(doc_dict)
        doc.insert(ignore_permissions=True)
        return doc
    except Exception as e:
        frappe.log_error(str(e), f"safe_insert_{doc_dict.get('doctype')}")
        return None


def _create_settings():
    try:
        s = frappe.get_single("Bond Settings")
        s.company_name = "Bizaxl Bond Markets"
        s.tagline = "Your Gateway to Fixed Income & Bond Markets"
        s.sebi_registration = "INZ000XXXXXX"
        s.phone = "+91-9876543210"
        s.email = "bonds@bizaxl.com"
        s.address = "Mumbai, Maharashtra, India"
        s.upi_id = "bizaxl@upi"
        s.gstin = "27AAAAA0000A1Z5"
        s.whatsapp_number = "+919876543210"
        s.ai_model = "claude-sonnet-4-20250514"
        s.max_tokens_per_query = 2000
        s.monthly_statement_day = 1
        s.coupon_reminder_days_before = 3
        s.working_days = "Monday,Tuesday,Wednesday,Thursday,Friday"
        s.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(str(e), "create_settings")


def _create_rms():
    rms = [
        {"rm_name": "Rajesh Kumar", "email": "rajesh@bizaxl.com", "phone": "9876543201", "employee_id": "BZ001", "is_active": 1},
        {"rm_name": "Priya Sharma", "email": "priya@bizaxl.com", "phone": "9876543202", "employee_id": "BZ002", "is_active": 1},
    ]
    for rm in rms:
        if not frappe.db.exists("Bond Relationship Manager", rm["rm_name"]):
            _safe_insert({"doctype": "Bond Relationship Manager", **rm})


def _create_issuers():
    issuers = [
        {
            "issuer_name": "HDFC Bank Limited",
            "issuer_type": "Corporate",
            "registered_country": "India",
            "sector": "Banking",
            "credit_rating": "AAA",
            "rating_agency": "CRISIL",
            "sebi_registration": "INE040A01034",
            "is_active": 1,
            "esg_framework": "ICMA Green Bond Principles"
        },
        {
            "issuer_name": "Government of India",
            "issuer_type": "Government",
            "registered_country": "India",
            "sector": "Government",
            "credit_rating": "Sovereign",
            "rating_agency": "CRISIL",
            "is_active": 1
        },
        {
            "issuer_name": "Adani Green Energy Limited",
            "issuer_type": "Corporate",
            "registered_country": "India",
            "sector": "Power",
            "credit_rating": "BB+",
            "rating_agency": "S&P",
            "is_active": 1,
            "esg_framework": "ICMA Green Bond Principles"
        },
        {
            "issuer_name": "Tata Motors Finance",
            "issuer_type": "NBFC",
            "registered_country": "India",
            "sector": "Auto",
            "credit_rating": "AA",
            "rating_agency": "ICRA",
            "is_active": 1
        },
        {
            "issuer_name": "Larsen & Toubro Limited",
            "issuer_type": "Corporate",
            "registered_country": "India",
            "sector": "Infrastructure",
            "credit_rating": "AAA",
            "rating_agency": "CRISIL",
            "is_active": 1
        },
    ]
    for issuer in issuers:
        if not frappe.db.exists("Bond Issuer", issuer["issuer_name"]):
            _safe_insert({"doctype": "Bond Issuer", **issuer})


def _create_bonds():
    bonds_data = [
        # 1. HDFC Corporate Bond
        {
            "bond_name": "HDFC Bank Bond 2034",
            "isin": "INE040A08382",
            "issuer_name": "HDFC Bank Limited",
            "issuer_type": "Financial Institution",
            "issue_date": "2024-01-15",
            "maturity_date": "2034-01-15",
            "tenor_years": 10,
            "tenor_description": "Long Term 10Y+",
            "principal_amount": 1000000,
            "issue_currency": "INR",
            "face_value": 1000000,
            "total_issue_size": 50000000000,
            "outstanding_amount": 50000000000,
            "coupon_type": "Fixed",
            "coupon_rate": 8.65,
            "benchmark_rate": "NA",
            "coupon_frequency": "Semi-Annual",
            "first_coupon_date": "2024-07-15",
            "penultimate_date": "2033-07-15",
            "day_count_convention": "Actual/Actual",
            "business_day_convention": "Modified Following",
            "governing_law": "Indian Law",
            "exchange_listing": "BSE",
            "credit_rating": "AAA",
            "credit_rating_agency": "CRISIL",
            "rating_outlook": "Stable",
            "bond_type": "Corporate Bond",
            "security_type": "Unsecured",
            "domestic_foreign": "Domestic",
            "esg_classification": "None",
            "is_callable": 0,
            "is_puttable": 0,
            "is_convertible": 0,
            "is_amortizing": 0,
            "is_active": 1,
            "sebi_registration": "INZ000XXXXXX",
        },
        # 2. GoI G-Sec
        {
            "bond_name": "GoI 2031 G-Sec",
            "isin": "IN0020210123",
            "issuer_name": "Government of India",
            "issuer_type": "Central Government",
            "issue_date": "2021-01-22",
            "maturity_date": "2031-01-22",
            "tenor_years": 10,
            "tenor_description": "Long Term 10Y+",
            "principal_amount": 100,
            "issue_currency": "INR",
            "face_value": 100,
            "total_issue_size": 100000000000,
            "outstanding_amount": 100000000000,
            "coupon_type": "Fixed",
            "coupon_rate": 6.54,
            "benchmark_rate": "NA",
            "coupon_frequency": "Semi-Annual",
            "first_coupon_date": "2021-07-22",
            "penultimate_date": "2030-07-22",
            "day_count_convention": "Actual/Actual",
            "business_day_convention": "Modified Following",
            "governing_law": "Indian Law",
            "exchange_listing": "NSE+BSE",
            "credit_rating": "Sovereign",
            "credit_rating_agency": "CRISIL",
            "rating_outlook": "Stable",
            "bond_type": "Government Bond",
            "security_type": "Unsecured",
            "domestic_foreign": "Domestic",
            "esg_classification": "None",
            "is_active": 1,
        },
        # 3. Adani Green Bond
        {
            "bond_name": "Adani Green Energy Bond",
            "isin": "INE999X08001",
            "issuer_name": "Adani Green Energy Limited",
            "issuer_type": "Corporate",
            "issue_date": "2024-03-01",
            "maturity_date": "2029-03-01",
            "tenor_years": 5,
            "tenor_description": "Short Term 1-5Y",
            "principal_amount": 1000,
            "issue_currency": "USD",
            "face_value": 1000,
            "total_issue_size": 500000000,
            "outstanding_amount": 500000000,
            "coupon_type": "Fixed",
            "coupon_rate": 9.25,
            "benchmark_rate": "NA",
            "coupon_frequency": "Annual",
            "first_coupon_date": "2025-03-01",
            "penultimate_date": "2028-03-01",
            "day_count_convention": "30/360",
            "business_day_convention": "Following",
            "governing_law": "New York Law",
            "exchange_listing": "Singapore",
            "credit_rating": "BB+",
            "credit_rating_agency": "S&P",
            "rating_outlook": "Positive",
            "bond_type": "Corporate Bond",
            "security_type": "Unsecured",
            "domestic_foreign": "International",
            "esg_classification": "Green Bond",
            "use_of_proceeds": "Financing and refinancing of eligible renewable energy projects including solar power plants, wind energy projects, and hybrid renewable energy projects across India.",
            "is_callable": 0,
            "is_active": 1,
        },
        # 4. Tata Zero Coupon
        {
            "bond_name": "Tata Zero Coupon 2028",
            "isin": "INE155A08111",
            "issuer_name": "Tata Motors Finance",
            "issuer_type": "NBFC",
            "issue_date": "2023-06-01",
            "maturity_date": "2028-06-01",
            "tenor_years": 5,
            "tenor_description": "Short Term 1-5Y",
            "principal_amount": 10000,
            "issue_currency": "INR",
            "face_value": 10000,
            "total_issue_size": 10000000000,
            "outstanding_amount": 10000000000,
            "coupon_type": "Zero Coupon",
            "coupon_rate": 0,
            "benchmark_rate": "NA",
            "coupon_frequency": "At Maturity",
            "first_coupon_date": "2028-06-01",
            "penultimate_date": "2028-06-01",
            "day_count_convention": "Actual/365",
            "business_day_convention": "Modified Following",
            "governing_law": "Indian Law",
            "exchange_listing": "BSE",
            "credit_rating": "AA",
            "credit_rating_agency": "ICRA",
            "rating_outlook": "Stable",
            "bond_type": "Zero Coupon",
            "security_type": "Secured",
            "domestic_foreign": "Domestic",
            "esg_classification": "None",
            "is_active": 1,
        },
        # 5. L&T Step-Up Bond
        {
            "bond_name": "L&T Step-Up Bond 2030",
            "isin": "INE018A08093",
            "issuer_name": "Larsen & Toubro Limited",
            "issuer_type": "Corporate",
            "issue_date": "2024-04-01",
            "maturity_date": "2030-04-01",
            "tenor_years": 6,
            "tenor_description": "Medium Term 5-10Y",
            "principal_amount": 1000000,
            "issue_currency": "INR",
            "face_value": 1000000,
            "total_issue_size": 20000000000,
            "outstanding_amount": 20000000000,
            "coupon_type": "Step-Up",
            "coupon_rate": 7.0,
            "benchmark_rate": "NA",
            "coupon_frequency": "Quarterly",
            "first_coupon_date": "2024-07-01",
            "penultimate_date": "2030-01-01",
            "day_count_convention": "Actual/365",
            "business_day_convention": "Modified Following",
            "governing_law": "Indian Law",
            "exchange_listing": "NSE",
            "credit_rating": "AAA",
            "credit_rating_agency": "CRISIL",
            "rating_outlook": "Stable",
            "bond_type": "Corporate Bond",
            "security_type": "Unsecured",
            "domestic_foreign": "Domestic",
            "esg_classification": "None",
            "is_active": 1,
            "remarks": "Step-up: 2024-26: 7%, 2026-28: 8%, 2028-30: 9%",
        },
    ]

    bond_names = {}
    for b in bonds_data:
        if not frappe.db.exists("Bond Master", {"isin": b["isin"]}):
            doc = _safe_insert({"doctype": "Bond Master", **b})
            if doc:
                bond_names[b["isin"]] = doc.name
        else:
            existing = frappe.get_all("Bond Master", filters={"isin": b["isin"]}, fields=["name"])
            if existing:
                bond_names[b["isin"]] = existing[0].name

    # Create step schedule for L&T
    lt_name = bond_names.get("INE018A08093", "")
    if lt_name:
        steps = [
            {"period_from": "2024-04-01", "period_to": "2026-03-31", "coupon_rate": 7.0, "rate_type": "Fixed"},
            {"period_from": "2026-04-01", "period_to": "2028-03-31", "coupon_rate": 8.0, "rate_type": "Fixed"},
            {"period_from": "2028-04-01", "period_to": "2030-04-01", "coupon_rate": 9.0, "rate_type": "Fixed"},
        ]
        for step in steps:
            _safe_insert({"doctype": "Bond Step Schedule", "bond_name": lt_name, "isin": "INE018A08093", **step})

    # Create coupon schedules for HDFC bond
    hdfc_name = bond_names.get("INE040A08382", "")
    if hdfc_name:
        for i in range(1, 5):
            coupon_date = f"202{4+i//2}-0{1+((i%2)*6)}-15"
            _safe_insert({
                "doctype": "Bond Coupon Schedule",
                "bond_name": hdfc_name,
                "isin": "INE040A08382",
                "coupon_number": i,
                "coupon_date": f"2024-07-15" if i == 1 else f"2025-01-15" if i == 2 else f"2025-07-15" if i == 3 else "2026-01-15",
                "coupon_rate_applicable": 8.65,
                "coupon_amount_per_unit": 43250,
                "total_coupon_amount": 2162500000,
                "day_count_days": 182,
                "day_count_fraction": 0.4973,
                "status": "Upcoming" if i > 1 else "Paid",
            })

    # Create coupon schedules for GoI bond
    goi_name = bond_names.get("IN0020210123", "")
    if goi_name:
        for i in range(1, 5):
            _safe_insert({
                "doctype": "Bond Coupon Schedule",
                "bond_name": goi_name,
                "isin": "IN0020210123",
                "coupon_number": i + 6,
                "coupon_date": f"2024-07-22" if i == 1 else f"2025-01-22" if i == 2 else f"2025-07-22" if i == 3 else "2026-01-22",
                "coupon_rate_applicable": 6.54,
                "coupon_amount_per_unit": 3.27,
                "total_coupon_amount": 3270000000,
                "day_count_days": 182,
                "status": "Upcoming",
            })


def _create_clients():
    clients = [
        {
            "full_name": "Amit Verma",
            "email": "amit.verma@email.com",
            "phone": "9876501234",
            "client_type": "Individual",
            "pan_number": "ABCPV1234D",
            "kyc_status": "Verified",
            "demat_account_number": "1234567890123456",
            "dp_name": "CDSL",
            "bank_name": "HDFC Bank",
            "bank_account_number": "50100123456789",
            "ifsc_code": "HDFC0001234",
            "relationship_manager": "Rajesh Kumar",
            "risk_profile": "Moderate",
            "total_investment": 5000000,
            "total_current_value": 5350000,
            "total_interest_earned": 350000,
            "total_bonds_held": 2,
            "is_active": 1,
        },
        {
            "full_name": "Sunita Patel",
            "email": "sunita.patel@email.com",
            "phone": "9876502345",
            "client_type": "Individual",
            "pan_number": "BCQPS5678E",
            "kyc_status": "Verified",
            "demat_account_number": "9876543210987654",
            "dp_name": "NSDL",
            "bank_name": "SBI",
            "bank_account_number": "10987654321",
            "ifsc_code": "SBIN0001234",
            "relationship_manager": "Priya Sharma",
            "risk_profile": "Conservative",
            "total_investment": 10000000,
            "total_current_value": 10650000,
            "total_interest_earned": 654000,
            "total_bonds_held": 3,
            "is_active": 1,
        },
        {
            "full_name": "Greentech Investments Pvt Ltd",
            "email": "invest@greentech.com",
            "phone": "9876503456",
            "client_type": "Corporate",
            "pan_number": "AAACG1234F",
            "kyc_status": "Verified",
            "demat_account_number": "5432167890543216",
            "dp_name": "CDSL",
            "bank_name": "Axis Bank",
            "bank_account_number": "9876543210",
            "ifsc_code": "UTIB0001234",
            "relationship_manager": "Rajesh Kumar",
            "risk_profile": "Aggressive",
            "total_investment": 25000000,
            "total_current_value": 26500000,
            "total_interest_earned": 1500000,
            "total_bonds_held": 4,
            "is_active": 1,
        },
    ]
    for c in clients:
        if not frappe.db.exists("Bond Client", {"email": c["email"]}):
            _safe_insert({"doctype": "Bond Client", **c})

    # Create holdings
    hdfc_bonds = frappe.get_all("Bond Master", filters={"isin": "INE040A08382"}, fields=["name", "bond_name"])
    goi_bonds = frappe.get_all("Bond Master", filters={"isin": "IN0020210123"}, fields=["name", "bond_name"])
    adani_bonds = frappe.get_all("Bond Master", filters={"isin": "INE999X08001"}, fields=["name", "bond_name"])

    if hdfc_bonds and frappe.db.exists("Bond Client", {"email": "amit.verma@email.com"}):
        _safe_insert({
            "doctype": "Bond Holding",
            "client_name": "Amit Verma",
            "isin": "INE040A08382",
            "bond_name": hdfc_bonds[0]["name"],
            "issuer_name": "HDFC Bank Limited",
            "purchase_date": "2024-01-20",
            "settlement_date": "2024-01-22",
            "face_value": 1000000,
            "quantity": 5,
            "purchase_price": 100.0,
            "purchase_yield": 8.65,
            "purchase_amount": 5000000,
            "current_price": 101.5,
            "current_value": 5075000,
            "accrued_interest": 43250,
            "total_value_with_interest": 5118250,
            "unrealized_pnl": 75000,
            "unrealized_pnl_percent": 1.5,
            "interest_earned_to_date": 216250,
            "maturity_date": "2034-01-15",
            "next_coupon_date": "2025-01-15",
            "next_coupon_amount": 43250,
            "holding_status": "Active",
        })

    if goi_bonds and frappe.db.exists("Bond Client", {"email": "sunita.patel@email.com"}):
        _safe_insert({
            "doctype": "Bond Holding",
            "client_name": "Sunita Patel",
            "isin": "IN0020210123",
            "bond_name": goi_bonds[0]["name"],
            "issuer_name": "Government of India",
            "purchase_date": "2024-02-10",
            "settlement_date": "2024-02-12",
            "face_value": 100,
            "quantity": 100000,
            "purchase_price": 98.5,
            "purchase_yield": 6.75,
            "purchase_amount": 9850000,
            "current_price": 99.2,
            "current_value": 9920000,
            "accrued_interest": 327000,
            "total_value_with_interest": 10247000,
            "unrealized_pnl": 70000,
            "unrealized_pnl_percent": 0.71,
            "interest_earned_to_date": 654000,
            "maturity_date": "2031-01-22",
            "next_coupon_date": "2025-01-22",
            "next_coupon_amount": 327000,
            "holding_status": "Active",
        })

    if adani_bonds and frappe.db.exists("Bond Client", {"email": "invest@greentech.com"}):
        _safe_insert({
            "doctype": "Bond Holding",
            "client_name": "Greentech Investments Pvt Ltd",
            "isin": "INE999X08001",
            "bond_name": adani_bonds[0]["name"],
            "issuer_name": "Adani Green Energy Limited",
            "purchase_date": "2024-03-05",
            "settlement_date": "2024-03-07",
            "face_value": 1000,
            "quantity": 10000,
            "purchase_price": 100.0,
            "purchase_yield": 9.25,
            "purchase_amount": 10000000,
            "current_price": 102.5,
            "current_value": 10250000,
            "accrued_interest": 231250,
            "total_value_with_interest": 10481250,
            "unrealized_pnl": 250000,
            "unrealized_pnl_percent": 2.5,
            "interest_earned_to_date": 925000,
            "maturity_date": "2029-03-01",
            "next_coupon_date": "2025-03-01",
            "next_coupon_amount": 925000,
            "holding_status": "Active",
        })

    # Create one pending coupon payment
    hdfc_name = hdfc_bonds[0]["name"] if hdfc_bonds else ""
    if hdfc_name:
        _safe_insert({
            "doctype": "Bond Coupon Payment",
            "isin": "INE040A08382",
            "bond_name": hdfc_name,
            "issuer_name": "HDFC Bank Limited",
            "coupon_date": "2025-01-15",
            "record_date": "2025-01-10",
            "payment_date": "2025-01-15",
            "coupon_rate": 8.65,
            "coupon_amount_per_unit": 43250,
            "total_holders": 3,
            "total_units": 5,
            "total_coupon_payable": 216250,
            "total_paid": 0,
            "total_pending": 216250,
            "payment_status": "Scheduled",
            "payment_mode": "NEFT",
        })
