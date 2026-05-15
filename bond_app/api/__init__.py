import frappe
import json
import datetime


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _get_settings():
    try:
        return frappe.get_single("Bond Settings")
    except Exception:
        return frappe._dict({})


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_dashboard_stats():
    try:
        today = datetime.date.today()
        seven_days = today + datetime.timedelta(days=7)

        total_bonds = frappe.db.count("Bond Master")
        active_bonds = frappe.db.count("Bond Master", {"is_active": 1})
        total_clients = frappe.db.count("Bond Client", {"is_active": 1})
        esg_bonds_count = frappe.db.count("Bond Master", {"esg_classification": ["!=", "None"]})
        today_settlements = frappe.db.count("Bond Settlement", {"settlement_date": str(today)})

        aum_result = frappe.db.sql(
            "SELECT SUM(total_current_value) FROM `tabBond Client` WHERE is_active=1"
        )
        total_aum = (aum_result[0][0] or 0) if aum_result else 0

        upcoming_coupons_7days = frappe.db.count(
            "Bond Coupon Schedule",
            {"coupon_date": ["between", [str(today), str(seven_days)]], "status": "Upcoming"}
        )
        overdue_coupons = frappe.db.count(
            "Bond Coupon Schedule",
            {"coupon_date": ["<", str(today)], "status": "Upcoming"}
        )

        monthly_interest_result = frappe.db.sql(
            "SELECT SUM(total_coupon_amount) FROM `tabBond Coupon Schedule` "
            "WHERE MONTH(coupon_date)=MONTH(CURDATE()) AND YEAR(coupon_date)=YEAR(CURDATE())"
        )
        monthly_interest = (monthly_interest_result[0][0] or 0) if monthly_interest_result else 0

        return {
            "total_bonds": total_bonds,
            "active_bonds": active_bonds,
            "total_aum": total_aum,
            "upcoming_coupons_7days": upcoming_coupons_7days,
            "total_clients": total_clients,
            "overdue_coupons": overdue_coupons,
            "esg_bonds_count": esg_bonds_count,
            "today_settlements": today_settlements,
            "monthly_interest": monthly_interest,
        }
    except Exception as e:
        frappe.log_error(str(e), "get_dashboard_stats")
        return {}


@frappe.whitelist(allow_guest=True)
def get_settings():
    try:
        s = _get_settings()
        return {
            "company_name": s.company_name or "Bizaxl Bond Markets",
            "tagline": s.tagline or "",
            "sebi_registration": s.sebi_registration or "",
            "phone": s.phone or "",
            "email": s.email or "",
            "address": s.address or "",
            "upi_id": s.upi_id or "",
            "gstin": s.gstin or "",
            "logo_url": s.logo_url or "",
            "whatsapp_number": s.whatsapp_number or "",
            "claude_api_key": s.claude_api_key or "",
            "ai_model": s.ai_model or "claude-sonnet-4-20250514",
            "max_tokens_per_query": s.max_tokens_per_query or 2000,
            "monthly_statement_day": s.monthly_statement_day or 1,
            "coupon_reminder_days_before": s.coupon_reminder_days_before or 3,
            "working_days": s.working_days or "",
        }
    except Exception as e:
        frappe.log_error(str(e), "get_settings")
        return {}


@frappe.whitelist(allow_guest=True)
def save_settings(**kwargs):
    try:
        s = frappe.get_single("Bond Settings")
        fields = [
            "company_name", "tagline", "sebi_registration", "phone", "email",
            "address", "upi_id", "gstin", "logo_url", "whatsapp_number",
            "claude_api_key", "ai_model", "max_tokens_per_query",
            "monthly_statement_day", "coupon_reminder_days_before", "working_days"
        ]
        for f in fields:
            if f in kwargs:
                setattr(s, f, kwargs[f])
        s.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(str(e), "save_settings")
        return {"status": "error", "message": str(e)}


# ─── BOND MASTER ───────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_bonds(bond_type=None, esg_type=None, issuer=None, currency=None, search=None):
    try:
        filters = {}
        if bond_type:
            filters["bond_type"] = bond_type
        if esg_type:
            filters["esg_classification"] = esg_type
        if issuer:
            filters["issuer_name"] = ["like", f"%{issuer}%"]
        if currency:
            filters["issue_currency"] = currency
        if search:
            filters["bond_name"] = ["like", f"%{search}%"]

        bonds = frappe.get_all(
            "Bond Master",
            filters=filters,
            fields=[
                "name", "bond_name", "isin", "issuer_name", "issuer_type",
                "bond_type", "coupon_type", "coupon_rate", "coupon_frequency",
                "maturity_date", "issue_date", "credit_rating", "issue_currency",
                "principal_amount", "esg_classification", "is_active",
                "exchange_listing", "rating_outlook"
            ],
            order_by="creation desc",
            limit=200
        )
        return bonds
    except Exception as e:
        frappe.log_error(str(e), "get_bonds")
        return []


@frappe.whitelist(allow_guest=True)
def get_bond_detail(bond_name):
    try:
        bond = frappe.get_doc("Bond Master", bond_name)
        return bond.as_dict()
    except Exception as e:
        frappe.log_error(str(e), "get_bond_detail")
        return {}


@frappe.whitelist(allow_guest=True)
def get_coupon_schedule(bond_name):
    try:
        return frappe.get_all(
            "Bond Coupon Schedule",
            filters={"bond_name": bond_name},
            fields=["*"],
            order_by="coupon_number asc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_coupon_schedule")
        return []


@frappe.whitelist(allow_guest=True)
def get_amortization_schedule(bond_name):
    try:
        return frappe.get_all(
            "Bond Amortization Schedule",
            filters={"bond_name": bond_name},
            fields=["*"],
            order_by="payment_number asc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_amortization_schedule")
        return []


# ─── CLIENT ────────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_clients(kyc_status=None, search=None):
    try:
        filters = {}
        if kyc_status:
            filters["kyc_status"] = kyc_status
        if search:
            filters["full_name"] = ["like", f"%{search}%"]
        return frappe.get_all(
            "Bond Client",
            filters=filters,
            fields=[
                "name", "full_name", "email", "phone", "client_type",
                "pan_number", "kyc_status", "risk_profile", "total_investment",
                "total_current_value", "total_bonds_held", "is_active",
                "relationship_manager"
            ],
            order_by="creation desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_clients")
        return []


@frappe.whitelist(allow_guest=True)
def get_client_holdings(client_name):
    try:
        return frappe.get_all(
            "Bond Holding",
            filters={"client_name": client_name},
            fields=["*"],
            order_by="purchase_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_client_holdings")
        return []


@frappe.whitelist(allow_guest=True)
def get_client_transactions(client_name, date_from=None, date_to=None):
    try:
        filters = {"client_name": client_name}
        if date_from:
            filters["transaction_date"] = [">=", date_from]
        if date_to:
            filters["transaction_date"] = ["<=", date_to]
        return frappe.get_all(
            "Bond Transaction",
            filters=filters,
            fields=["*"],
            order_by="transaction_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_client_transactions")
        return []


@frappe.whitelist(allow_guest=True)
def get_client_ledger(client_name, date_from=None, date_to=None):
    try:
        filters = {"client_name": client_name}
        if date_from:
            filters["entry_date"] = [">=", date_from]
        if date_to:
            filters["entry_date"] = ["<=", date_to]
        return frappe.get_all(
            "Bond Ledger",
            filters=filters,
            fields=["*"],
            order_by="entry_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_client_ledger")
        return []


# ─── COUPON ────────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_coupon_payments(date_from=None, date_to=None, status=None):
    try:
        filters = {}
        if date_from:
            filters["payment_date"] = [">=", date_from]
        if date_to:
            filters["payment_date"] = ["<=", date_to]
        if status:
            filters["payment_status"] = status
        return frappe.get_all(
            "Bond Coupon Payment",
            filters=filters,
            fields=["*"],
            order_by="payment_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_coupon_payments")
        return []


@frappe.whitelist(allow_guest=True)
def get_upcoming_coupons(days=7):
    try:
        today = datetime.date.today()
        future = today + datetime.timedelta(days=int(days))
        return frappe.get_all(
            "Bond Coupon Schedule",
            filters={
                "coupon_date": ["between", [str(today), str(future)]],
                "status": "Upcoming"
            },
            fields=["*"],
            order_by="coupon_date asc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_upcoming_coupons")
        return []


@frappe.whitelist(allow_guest=True)
def get_coupon_receipts(client_name=None, isin=None):
    try:
        filters = {}
        if client_name:
            filters["client_name"] = client_name
        if isin:
            filters["isin"] = isin
        return frappe.get_all(
            "Bond Coupon Receipt",
            filters=filters,
            fields=["*"],
            order_by="credit_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_coupon_receipts")
        return []


# ─── SETTLEMENT ────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_settlements(date=None, status=None):
    try:
        filters = {}
        if date:
            filters["settlement_date"] = date
        if status:
            filters["settlement_status"] = status
        return frappe.get_all(
            "Bond Settlement",
            filters=filters,
            fields=["*"],
            order_by="settlement_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_settlements")
        return []


# ─── BILLING ───────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_contract_notes(client_name=None, date_from=None, date_to=None):
    try:
        filters = {}
        if client_name:
            filters["client_name"] = client_name
        if date_from:
            filters["contract_date"] = [">=", date_from]
        if date_to:
            filters["contract_date"] = ["<=", date_to]
        return frappe.get_all(
            "Bond Contract Note",
            filters=filters,
            fields=["*"],
            order_by="contract_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_contract_notes")
        return []


@frappe.whitelist(allow_guest=True)
def get_invoices(client_name=None, payment_status=None):
    try:
        filters = {}
        if client_name:
            filters["client_name"] = client_name
        if payment_status:
            filters["payment_status"] = payment_status
        return frappe.get_all(
            "Bond Invoice",
            filters=filters,
            fields=["*"],
            order_by="invoice_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_invoices")
        return []


# ─── WHATSAPP ──────────────────────────────────────────────────────────────────

def _build_wa_url(phone, message):
    import urllib.parse
    phone = str(phone).replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = "91" + phone
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"


@frappe.whitelist(allow_guest=True)
def send_coupon_reminder(client_name, isin, coupon_date, amount):
    try:
        settings = _get_settings()
        client = frappe.get_all("Bond Client", filters={"full_name": client_name}, fields=["phone"])
        phone = client[0].phone if client else ""
        bond = frappe.get_all("Bond Master", filters={"isin": isin}, fields=["bond_name"])
        bond_name = bond[0].bond_name if bond else isin
        msg = (
            f"📅 *Upcoming Coupon Payment*\n"
            f"Dear *{client_name}*,\n"
            f"Bond: *{bond_name}* ({isin})\n"
            f"Coupon Date: *{coupon_date}*\n"
            f"Amount: *₹{amount}* per unit\n"
            f"*{settings.company_name or 'Bizaxl Bond Markets'}* | {settings.phone or ''}"
        )
        wa_url = _build_wa_url(phone, msg)
        frappe.log_error(wa_url, "WA")
        return {"status": "success", "wa_url": wa_url}
    except Exception as e:
        frappe.log_error(str(e), "send_coupon_reminder")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def send_coupon_credited(coupon_receipt_name):
    try:
        settings = _get_settings()
        r = frappe.get_doc("Bond Coupon Receipt", coupon_receipt_name)
        msg = (
            f"✅ *Coupon Credited!*\n"
            f"Dear *{r.client_name}*,\n"
            f"₹{r.net_amount} credited for *{r.bond_name}*\n"
            f"Gross: ₹{r.gross_amount} | TDS: ₹{r.tds_deducted}\n"
            f"Date: {r.credit_date} | Ref: {r.bank_reference}\n"
            f"*{settings.company_name or 'Bizaxl Bond Markets'}*"
        )
        wa_url = _build_wa_url(r.client_phone, msg)
        frappe.log_error(wa_url, "WA")
        r.whatsapp_sent = 1
        r.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "wa_url": wa_url}
    except Exception as e:
        frappe.log_error(str(e), "send_coupon_credited")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def send_monthly_statement(client_name):
    try:
        settings = _get_settings()
        client = frappe.get_all("Bond Client", filters={"full_name": client_name},
                                fields=["phone", "total_current_value", "total_investment", "total_bonds_held"])
        if not client:
            return {"status": "error", "message": "Client not found"}
        c = client[0]
        now = datetime.date.today()
        msg = (
            f"📊 *Monthly Bond Statement — {now.strftime('%B %Y')}*\n"
            f"Dear *{client_name}*,\n"
            f"Portfolio Value: *₹{c.total_current_value or 0}*\n"
            f"Total Invested: *₹{c.total_investment or 0}*\n"
            f"Bonds Held: *{c.total_bonds_held or 0}*\n"
            f"*{settings.company_name or 'Bizaxl Bond Markets'}* | SEBI: {settings.sebi_registration or ''}"
        )
        wa_url = _build_wa_url(c.phone, msg)
        frappe.log_error(wa_url, "WA")
        return {"status": "success", "wa_url": wa_url}
    except Exception as e:
        frappe.log_error(str(e), "send_monthly_statement")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def send_bond_maturity_alert(client_name, bond_name, maturity_date):
    try:
        settings = _get_settings()
        client = frappe.get_all("Bond Client", filters={"full_name": client_name}, fields=["phone"])
        phone = client[0].phone if client else ""
        msg = (
            f"⏰ *Bond Maturity Alert*\n"
            f"Dear *{client_name}*,\n"
            f"*{bond_name}* matures on *{maturity_date}*\n"
            f"Please contact your Relationship Manager.\n"
            f"*{settings.company_name or 'Bizaxl Bond Markets'}*"
        )
        wa_url = _build_wa_url(phone, msg)
        frappe.log_error(wa_url, "WA")
        return {"status": "success", "wa_url": wa_url}
    except Exception as e:
        frappe.log_error(str(e), "send_bond_maturity_alert")
        return {"status": "error", "message": str(e)}



# ─── BUILT-IN BOND AI ENGINE (NO EXTERNAL API KEY NEEDED) ─────────────────────
# All analysis is done locally using bond data from the database.
# Uploaded documents are searched for additional context.

import re as _re

class _BondEngine:
    """Self-contained bond analysis engine. No external API needed."""

    def __init__(self, bond, coupons, steps, amort, documents):
        self.b = bond or {}
        self.coupons = coupons or []
        self.steps = steps or []
        self.amort = amort or []
        self.doc_text = " ".join([
            (d.get("extracted_text") or d.get("document_summary") or "")
            for d in (documents or [])
        ])[:80000]
        self.doc_names = [d.get("document_name","") for d in (documents or [])]

    def answer(self, q):
        ql = q.lower().strip()
        if any(w in ql for w in ["coupon schedule","payment schedule","all coupon","all payment","list coupon"]):
            return self._coupon_schedule()
        if any(w in ql for w in ["next coupon","next payment","upcoming coupon","when is next","upcoming payment"]):
            return self._next_coupon()
        if any(w in ql for w in ["coupon rate","interest rate","what rate","coupon %","rate per"]):
            return self._coupon_rate()
        if any(w in ql for w in ["ytm","yield to maturity","yield to call","ytc","calculate yield"]):
            return self._yield_analysis()
        if any(w in ql for w in ["amortiz","principal repay","principal schedule","amort"]):
            return self._amortization()
        if any(w in ql for w in ["step-up","step up","step schedule","step-down","step rate"]):
            return self._step_schedule()
        if any(w in ql for w in ["risk factor","credit risk","default risk","market risk","risk"]):
            return self._risk_factors()
        if any(w in ql for w in ["covenant","restriction","negative covenant","events of default","affirmative"]):
            return self._covenants()
        if any(w in ql for w in ["esg","green bond","use of proceed","sustainability","climate bond","social bond"]):
            return self._esg()
        if any(w in ql for w in ["call option","callable","call date","call price","call feature"]):
            return self._call_option()
        if any(w in ql for w in ["put option","puttable","put date","put feature"]):
            return self._put_option()
        if any(w in ql for w in ["convert","convertible","conversion ratio","conversion price"]):
            return self._convertible()
        if any(w in ql for w in ["maturity","matures","maturity date","redemption date","when does"]):
            return self._maturity()
        if any(w in ql for w in ["issuer","who issued","company name","issuer name"]):
            return self._issuer()
        if any(w in ql for w in ["isin","identifier","cusip","bond code"]):
            return self._identifiers()
        if any(w in ql for w in ["rating","credit rating","crisil","icra","care","moody","fitch","s&p"]):
            return self._rating()
        if any(w in ql for w in ["day count","accrued interest","accrual","30/360","actual/actual"]):
            return self._day_count()
        if any(w in ql for w in ["duration","modified duration","macaulay duration","dv01"]):
            return self._duration()
        if any(w in ql for w in ["face value","par value","principal amount","nominal value"]):
            return self._face_value()
        if any(w in ql for w in ["issue size","total issue","outstanding amount","amount issued"]):
            return self._issue_size()
        if any(w in ql for w in ["currency","inr","usd","eur","denomination"]):
            return self._currency()
        if any(w in ql for w in ["exchange","listed","nse","bse","listing"]):
            return self._listing()
        if any(w in ql for w in ["law","governing","jurisdiction","legal"]):
            return self._legal()
        if any(w in ql for w in ["security","secured","unsecured","collateral"]):
            return self._security()
        if any(w in ql for w in ["summary","overview","about this bond","tell me about","details","describe"]):
            return self._summary()
        if any(w in ql for w in ["calculate","compute","how much","accrue","interest for"]):
            return self._calculation(q)
        # Search uploaded documents
        doc_ans = self._search_docs(q)
        if doc_ans:
            return doc_ans
        return self._general()

    def _summary(self):
        b = self.b
        lines = [
            "## Bond Summary — " + b.get("bond_name",""),
            "",
            "| Field | Value |",
            "|-------|-------|",
            "| **ISIN** | `" + b.get("isin","N/A") + "` |",
            "| **Issuer** | " + b.get("issuer_name","N/A") + " (" + b.get("issuer_type","") + ") |",
            "| **Bond Type** | " + b.get("bond_type","N/A") + " |",
            "| **Coupon** | **" + str(b.get("coupon_rate",0)) + "%** " + b.get("coupon_type","") + " " + b.get("coupon_frequency","") + " |",
            "| **Issue Date** | " + str(b.get("issue_date","N/A")) + " |",
            "| **Maturity Date** | " + str(b.get("maturity_date","N/A")) + " |",
            "| **Tenor** | " + str(b.get("tenor_years","N/A")) + " years |",
            "| **Face Value** | " + self._fmt(b.get("face_value")) + " |",
            "| **Total Issue Size** | " + self._fmt(b.get("total_issue_size")) + " |",
            "| **Credit Rating** | " + b.get("credit_rating","N/A") + " (" + b.get("credit_rating_agency","N/A") + ") — " + b.get("rating_outlook","") + " |",
            "| **Security** | " + b.get("security_type","N/A") + " |",
            "| **Currency** | " + b.get("issue_currency","INR") + " |",
            "| **Exchange** | " + b.get("exchange_listing","N/A") + " |",
            "| **ESG** | " + b.get("esg_classification","None") + " |",
            "| **Day Count** | " + b.get("day_count_convention","N/A") + " |",
        ]
        if b.get("is_callable"):
            lines.append("| **Call Date** | " + str(b.get("call_date","N/A")) + " at " + str(b.get("call_price","N/A")) + " |")
        if b.get("is_convertible"):
            lines.append("| **Convertible** | Yes — ratio " + str(b.get("conversion_ratio","")) + " |")
        if b.get("use_of_proceeds"):
            lines += ["", "**Use of Proceeds:** " + b.get("use_of_proceeds","")]
        if self.coupons:
            lines += ["", "**" + str(len(self.coupons)) + " coupon payments** in schedule. Ask *'Show coupon schedule'* for full list."]
        if self.doc_names:
            lines += ["", "**Uploaded Documents:** " + ", ".join(self.doc_names)]
        return "\n".join(lines)

    def _coupon_schedule(self):
        b = self.b
        if not self.coupons:
            fv = b.get("face_value",0) or 0
            rate = b.get("coupon_rate",0) or 0
            freq = b.get("coupon_frequency","Semi-Annual")
            amt = (float(fv) * float(rate) / 100) / self._ppY(freq) if fv and rate else 0
            return (
                "## Coupon Schedule — " + b.get("bond_name","") + "\n\n"
                "No individual coupon records stored yet.\n\n"
                "**Bond Terms:**\n"
                "- Coupon Rate: **" + str(rate) + "% p.a.**\n"
                "- Frequency: " + freq + "\n"
                "- Face Value: " + self._fmt(fv) + "\n"
                "- Day Count: " + b.get("day_count_convention","Actual/Actual") + "\n\n"
                "**Estimated coupon per unit:**\n"
                "= " + self._fmt(fv) + " × " + str(rate) + "% ÷ " + str(self._ppY(freq)) + " = **" + self._fmt(amt) + "**"
            )
        today = str(datetime.date.today())
        lines = [
            "## Coupon Schedule — " + b.get("bond_name",""),
            "",
            "Rate: **" + str(b.get("coupon_rate",0)) + "% p.a.** | Frequency: " + b.get("coupon_frequency","") + " | Day Count: " + b.get("day_count_convention",""),
            "",
            "| # | Date | Rate | Amt/Unit | Total | Status |",
            "|---|------|------|----------|-------|--------|",
        ]
        paid_count = 0
        total_paid = 0
        total_pending = 0
        for c in self.coupons:
            s = c.get("status","Upcoming")
            marker = " ◀ NEXT" if s == "Upcoming" and paid_count == len([x for x in self.coupons if x.get("status")=="Paid"]) else ""
            lines.append(
                "| " + str(c.get("coupon_number","?")) +
                " | " + str(c.get("coupon_date","?")) +
                " | " + str(c.get("coupon_rate_applicable",0)) + "%" +
                " | " + self._fmt(c.get("coupon_amount_per_unit",0)) +
                " | " + self._fmt(c.get("total_coupon_amount",0)) +
                " | " + s + marker + " |"
            )
            if s == "Paid":
                paid_count += 1
                total_paid += c.get("total_coupon_amount",0) or 0
            else:
                total_pending += c.get("total_coupon_amount",0) or 0
        lines += [
            "",
            "**Total Paid:** " + self._fmt(total_paid) + " | **Total Pending:** " + self._fmt(total_pending),
        ]
        return "\n".join(lines)

    def _next_coupon(self):
        b = self.b
        today = str(datetime.date.today())
        upcoming = [c for c in self.coupons if str(c.get("coupon_date","")) > today and c.get("status") != "Paid"]
        if upcoming:
            c = upcoming[0]
            return (
                "## Next Coupon Payment — " + b.get("bond_name","") + "\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Coupon #** | " + str(c.get("coupon_number","?")) + " |\n"
                "| **Payment Date** | **" + str(c.get("coupon_date","N/A")) + "** |\n"
                "| **Rate** | " + str(c.get("coupon_rate_applicable",0)) + "% p.a. |\n"
                "| **Amount per Unit** | **" + self._fmt(c.get("coupon_amount_per_unit",0)) + "** |\n"
                "| **Total Payable** | " + self._fmt(c.get("total_coupon_amount",0)) + " |\n"
                "| **Record Date** | " + str(c.get("record_date","N/A")) + " |\n"
                "| **Status** | " + c.get("status","Upcoming") + " |\n\n"
                "*" + str(len(upcoming)) + " coupon payment(s) remaining till maturity.*"
            )
        fv = b.get("face_value",0) or 0
        rate = b.get("coupon_rate",0) or 0
        freq = b.get("coupon_frequency","Semi-Annual")
        amt = (float(fv)*float(rate)/100)/self._ppY(freq) if fv and rate else 0
        return (
            "## Next Coupon — " + b.get("bond_name","") + "\n\n"
            "No upcoming coupon records in schedule.\n\n"
            "**Estimated from bond terms:**\n"
            "- Coupon Rate: " + str(rate) + "% p.a.\n"
            "- Frequency: " + freq + "\n"
            "- Face Value: " + self._fmt(fv) + "\n"
            "- Expected Amount/Unit: **" + self._fmt(amt) + "**"
        )

    def _coupon_rate(self):
        b = self.b
        fv = b.get("face_value",0) or 0
        rate = b.get("coupon_rate",0) or 0
        freq = b.get("coupon_frequency","Semi-Annual")
        amt = (float(fv)*float(rate)/100)/self._ppY(freq) if fv and rate else 0
        lines = [
            "## Coupon Rate — " + b.get("bond_name",""),
            "",
            "| Parameter | Value |",
            "|-----------|-------|",
            "| **Coupon Type** | " + b.get("coupon_type","Fixed") + " |",
            "| **Annual Coupon Rate** | **" + str(rate) + "% per annum** |",
            "| **Coupon Frequency** | " + freq + " |",
            "| **Day Count Convention** | " + b.get("day_count_convention","Actual/Actual") + " |",
        ]
        if b.get("coupon_type") in ("Floating","Variable"):
            lines += [
                "| **Benchmark Rate** | " + str(b.get("benchmark_rate","N/A")) + " |",
                "| **Spread (bps)** | " + str(b.get("spread_bps",0)) + " |",
            ]
        if fv and rate:
            lines += [
                "",
                "### Coupon Calculation",
                "Coupon per unit = Face Value × Annual Rate ÷ Periods per Year",
                "= " + self._fmt(fv) + " × " + str(rate) + "% ÷ " + str(self._ppY(freq)),
                "= **" + self._fmt(amt) + " per coupon payment**",
                "",
                "Annual interest income per unit = **" + self._fmt(amt * self._ppY(freq)) + "**",
            ]
        if self.steps:
            lines += ["", "### Step-Up Rate Schedule", "| Period | Rate | Type |", "|--------|------|------|"]
            for s in self.steps:
                lines.append("| " + str(s.get("period_from","")) + " → " + str(s.get("period_to","")) + " | **" + str(s.get("coupon_rate",0)) + "%** | " + s.get("rate_type","") + " |")
        return "\n".join(lines)

    def _yield_analysis(self):
        b = self.b
        rate = b.get("coupon_rate",0) or 0
        fv = b.get("face_value",0) or 0
        tenor = b.get("tenor_years",0) or 0
        freq = b.get("coupon_frequency","Semi-Annual")
        ann_coupon = (float(fv)*float(rate)/100) if fv and rate else 0
        lines = [
            "## Yield Analysis — " + b.get("bond_name",""),
            "",
            "**Face Value:** " + self._fmt(fv) + " | **Coupon Rate:** " + str(rate) + "% p.a. | **Maturity:** " + str(b.get("maturity_date","N/A")),
            "",
            "### Yield to Maturity (YTM) Formula",
            "```",
            "YTM ≈ [Annual Coupon + (Face Value - Price) / Years] / [(Face Value + Price) / 2]",
            "```",
            "",
        ]
        if fv and rate and tenor:
            lines += [
                "### At Different Market Prices",
                "| Market Price | Premium/Discount | Approx YTM |",
                "|-------------|-----------------|------------|",
            ]
            for pct in [92, 95, 97, 100, 103, 105, 108]:
                price = float(fv) * pct / 100
                ytm = ((ann_coupon + (float(fv)-price)/float(tenor)) / ((float(fv)+price)/2)) * 100
                pd = "At Par" if pct==100 else ("Premium +" + str(pct-100) + "%" if pct>100 else "Discount -" + str(100-pct) + "%")
                lines.append("| " + self._fmt(price) + " | " + pd + " | **" + str(round(ytm,2)) + "%** |")
            lines += [
                "",
                "**When trading at par:** YTM = Coupon Rate = " + str(rate) + "%",
                "**When at discount:** YTM > Coupon Rate",
                "**When at premium:** YTM < Coupon Rate",
            ]
        lines += ["", "*Provide the current market price for exact YTM calculation.*"]
        return "\n".join(lines)

    def _amortization(self):
        b = self.b
        if not self.amort:
            is_amort = b.get("is_amortizing",0)
            return (
                "## Amortization — " + b.get("bond_name","") + "\n\n"
                + ("No amortization schedule records stored.\n\n"
                   "**Is Amortizing:** " + ("Yes" if is_amort else "No — This is a **BULLET BOND**") + "\n\n"
                   + ("Entire principal of **" + self._fmt(b.get("face_value",0)) + "** is repaid in one lump sum on maturity date **" + str(b.get("maturity_date","N/A")) + "**."
                      if not is_amort else
                      "Please add amortization schedule records in the Bond Amortization Schedule doctype."))
            )
        lines = [
            "## Amortization Schedule — " + b.get("bond_name",""),
            "",
            "| # | Date | Opening Principal | Coupon | Principal Repaid | Total Payment | Closing Principal |",
            "|---|------|-------------------|--------|-----------------|---------------|-------------------|",
        ]
        for a in self.amort:
            lines.append(
                "| " + str(a.get("payment_number","?")) +
                " | " + str(a.get("payment_date","?")) +
                " | " + self._fmt(a.get("opening_principal",0)) +
                " | " + self._fmt(a.get("coupon_payment",0)) +
                " | " + self._fmt(a.get("principal_payment",0)) +
                " | " + self._fmt(a.get("total_payment",0)) +
                " | " + self._fmt(a.get("closing_principal",0)) + " |"
            )
        return "\n".join(lines)

    def _step_schedule(self):
        b = self.b
        if not self.steps:
            return (
                "## Step Schedule — " + b.get("bond_name","") + "\n\n"
                "**Coupon Type:** " + b.get("coupon_type","N/A") + "\n\n"
                + ("No step schedule records found. This bond has a fixed coupon of **" + str(b.get("coupon_rate",0)) + "% p.a.**"
                   if b.get("coupon_type") != "Step-Up" else
                   "Please add step schedule records in Bond Step Schedule doctype.")
            )
        lines = [
            "## Step-Up/Down Coupon Schedule — " + b.get("bond_name",""),
            "",
            "| Period From | Period To | Coupon Rate | Type | Benchmark | Spread (bps) |",
            "|-------------|-----------|-------------|------|-----------|-------------|",
        ]
        for s in self.steps:
            lines.append(
                "| " + str(s.get("period_from","")) +
                " | " + str(s.get("period_to","")) +
                " | **" + str(s.get("coupon_rate",0)) + "%** |" +
                " " + s.get("rate_type","") +
                " | " + s.get("benchmark","-") +
                " | " + str(s.get("spread_bps",0)) + " |"
            )
        return "\n".join(lines)

    def _risk_factors(self):
        b = self.b
        rating = b.get("credit_rating","")
        risk_lvl = ("Low" if any(x in (rating or "") for x in ["AAA","Sovereign","Gilt"]) else
                    "Moderate-Low" if "AA" in (rating or "") else
                    "Moderate" if "A" in (rating or "") else
                    "High" if any(x in (rating or "") for x in ["B","BB","C","D"]) else "Moderate")
        doc_sec = self._extract_section("risk|default|credit risk", 1500)
        lines = [
            "## Risk Factors — " + b.get("bond_name",""),
            "",
            "### 1. Credit Risk — **" + risk_lvl + "**",
            "- Rating: **" + (rating or "N/A") + "** (" + b.get("credit_rating_agency","") + ") | Outlook: " + b.get("rating_outlook","N/A"),
            "- Issuer: " + b.get("issuer_name","N/A") + " (" + b.get("issuer_type","") + ")",
            "",
            "### 2. Interest Rate (Duration) Risk",
            "- Tenor: **" + str(b.get("tenor_years","?")) + " years** — " + ("High duration risk" if (b.get("tenor_years") or 0) > 10 else "Moderate duration risk" if (b.get("tenor_years") or 0) > 5 else "Lower duration risk"),
            "- Coupon Type: " + b.get("coupon_type","Fixed"),
            "- " + ("Fixed rate — price falls if market rates rise" if b.get("coupon_type")=="Fixed" else "Floating rate — resets with market; lower duration risk"),
            "",
            "### 3. Liquidity Risk",
            "- Exchange: " + b.get("exchange_listing","N/A") + " | Security: " + b.get("security_type","N/A"),
            "",
            "### 4. Reinvestment Risk",
            "- " + b.get("coupon_frequency","") + " coupons — must be reinvested at current market rates",
            "",
            "### 5. Call Risk",
            "- " + ("**Callable** on " + str(b.get("call_date","?")) + " at " + str(b.get("call_price","?")) + " — issuer may redeem early" if b.get("is_callable") else "Not callable — no early redemption risk"),
        ]
        if b.get("esg_classification") and b.get("esg_classification") != "None":
            lines += ["", "### 6. ESG/Greenwashing Risk", "- ESG classification must be verified by third-party verifier", "- Annual use-of-proceeds reporting required"]
        if doc_sec:
            lines += ["", "### From Prospectus:", "", doc_sec]
        return "\n".join(lines)

    def _covenants(self):
        b = self.b
        doc_sec = self._extract_section("covenant|restriction|event of default", 1500)
        lines = [
            "## Covenants & Restrictions — " + b.get("bond_name",""),
            "",
            "**Issuer:** " + b.get("issuer_name","N/A") + " | **Security:** " + b.get("security_type","N/A"),
            "",
            "### Negative Covenants (Restrictions on Issuer)",
            "- No additional secured borrowings above agreed limit without bondholder consent",
            "- No disposal of core assets without disclosure",
            "- Dividend restrictions if key financial ratios breach thresholds",
            "- No material change in business without notification",
            "",
            "### Affirmative Covenants (Obligations of Issuer)",
            "- Quarterly/annual financial reporting to bondholders",
            "- Notify on material events (rating change, litigation, restructuring)",
            "- Maintain credit rating (rating trigger covenants)",
            "- Preserve " + ("pledged security/collateral" if b.get("security_type")=="Secured" else "financial health ratios"),
            "",
            "### Events of Default",
            "- Non-payment of coupon or principal on due date (grace period: typically 30 days)",
            "- Cross-default on other material debt obligations",
            "- Insolvency / winding up proceedings",
            "- Material Adverse Change (MAC clause)",
            "- Rating downgrade below trigger level",
        ]
        if b.get("is_callable"):
            lines += ["", "### Call Provisions", "- Issuer may redeem on **" + str(b.get("call_date","?")) + "** at **" + str(b.get("call_price","?")) + "**"]
        if b.get("is_puttable"):
            lines += ["", "### Put Provisions", "- Investor may sell back on **" + str(b.get("put_date","?")) + "** at **" + str(b.get("put_price","?")) + "**"]
        if doc_sec:
            lines += ["", "### From Prospectus:", "", doc_sec]
        return "\n".join(lines)

    def _esg(self):
        b = self.b
        esg = b.get("esg_classification","None")
        if esg == "None":
            return "## ESG — " + b.get("bond_name","") + "\n\nThis bond is **not classified as an ESG bond**. It is a standard " + b.get("bond_type","corporate") + " bond."
        doc_sec = self._extract_section("esg|green|sustainability|climate|social bond|proceeds", 1500)
        lines = [
            "## ESG Classification — " + b.get("bond_name",""),
            "",
            "### Classification: **" + esg + "**",
            "",
            "| Parameter | Details |",
            "|-----------|---------|",
            "| ESG Type | **" + esg + "** |",
            "| Issuer | " + b.get("issuer_name","N/A") + " |",
            "| Issue Size | " + self._fmt(b.get("total_issue_size")) + " |",
            "| Currency | " + b.get("issue_currency","INR") + " |",
        ]
        if b.get("use_of_proceeds"):
            lines += ["", "### Use of Proceeds", "", b.get("use_of_proceeds","")]
        esg_desc = {
            "Green Bond": "Finances projects with clear environmental benefits — renewable energy, energy efficiency, clean transport, sustainable water, pollution prevention.",
            "Blue Bond": "Finances ocean and water sustainability — marine protected areas, sustainable fisheries, wastewater treatment.",
            "Social Bond": "Finances projects with positive social outcomes — affordable housing, healthcare, education, employment for underserved populations.",
            "Sustainability Bond": "Combines both Green and Social project categories.",
            "Climate Bond": "Finances climate change mitigation and adaptation projects — aligned with the Paris Agreement 1.5°C pathway.",
        }
        if esg in esg_desc:
            lines += ["", "**About " + esg + "s:** " + esg_desc[esg]]
        lines += [
            "", "### ESG Reporting Requirements",
            "- Annual Use of Proceeds Report",
            "- Impact Reporting (CO₂ avoided, MW renewable energy, beneficiaries etc.)",
            "- Third-party verification recommended (SEBI Green Bond guidelines)"
        ]
        if doc_sec:
            lines += ["", "### From Prospectus:", "", doc_sec]
        return "\n".join(lines)

    def _call_option(self):
        b = self.b
        if not b.get("is_callable"):
            return "## Call Option — " + b.get("bond_name","") + "\n\nThis bond **is NOT callable**. The issuer cannot redeem it before maturity on " + str(b.get("maturity_date","N/A")) + ". Investors are protected from early redemption."
        return (
            "## Call Option — " + b.get("bond_name","") + "\n\n"
            "⚠️ This bond **IS CALLABLE**\n\n"
            "| Parameter | Details |\n|-----------|--------|\n"
            "| Call Date | **" + str(b.get("call_date","N/A")) + "** |\n"
            "| Call Price | **" + str(b.get("call_price","N/A")) + "** |\n"
            "| Maturity Date | " + str(b.get("maturity_date","N/A")) + " |\n\n"
            "**Impact on investors:**\n"
            "- Issuer (" + b.get("issuer_name","") + ") can redeem this bond on the call date\n"
            "- Bondholders receive the call price — may be at par or slight premium\n"
            "- Typically exercised when market rates fall (issuer can refinance cheaper)\n"
            "- Yield to Call (YTC) may differ significantly from Yield to Maturity (YTM)\n"
            "- Always evaluate both YTM and YTC when purchasing callable bonds"
        )

    def _put_option(self):
        b = self.b
        if not b.get("is_puttable"):
            return "## Put Option — " + b.get("bond_name","") + "\n\nThis bond **is NOT puttable**. Investors cannot sell it back to the issuer before maturity."
        return (
            "## Put Option — " + b.get("bond_name","") + "\n\n"
            "✅ This bond **IS PUTTABLE** — investors can sell back to issuer\n\n"
            "| Put Date | Put Price |\n|----------|----------|\n"
            "| **" + str(b.get("put_date","N/A")) + "** | **" + str(b.get("put_price","N/A")) + "** |\n\n"
            "**This protects investors** — if rates rise, you can put back and reinvest at higher rates."
        )

    def _convertible(self):
        b = self.b
        if not b.get("is_convertible"):
            return "## Convertible Feature — " + b.get("bond_name","") + "\n\nThis bond **is NOT convertible**. It is a straight debt instrument with no equity conversion feature."
        return (
            "## Convertible Bond — " + b.get("bond_name","") + "\n\n"
            "✅ This bond **IS CONVERTIBLE** into equity shares\n\n"
            "| Parameter | Details |\n|-----------|--------|\n"
            "| Conversion Ratio | **" + str(b.get("conversion_ratio","N/A")) + "** shares per bond |\n"
            "| Conversion Price | **" + str(b.get("conversion_price","N/A")) + "** |\n\n"
            "**Conversion Value = Conversion Ratio × Current Share Price**\n"
            "When share price > conversion price, conversion is in-the-money."
        )

    def _maturity(self):
        b = self.b
        maturity = b.get("maturity_date")
        today = datetime.date.today()
        lines = [
            "## Maturity Details — " + b.get("bond_name",""),
            "",
            "| Field | Value |",
            "|-------|-------|",
            "| **Maturity Date** | **" + str(maturity or "N/A") + "** |",
            "| **Issue Date** | " + str(b.get("issue_date","N/A")) + " |",
            "| **Tenor** | " + str(b.get("tenor_years","N/A")) + " years |",
        ]
        if maturity:
            try:
                mat = datetime.date.fromisoformat(str(maturity))
                days = (mat - today).days
                if days > 0:
                    lines += [
                        "| **Days to Maturity** | " + str(days) + " days (" + str(round(days/365.25,2)) + " years) |",
                        "| **Status** | 🟢 Active |",
                    ]
                    if days <= 30:
                        lines.append("\n⚠️ **MATURING IN " + str(days) + " DAYS — Alert your RM immediately!**")
                    elif days <= 90:
                        lines.append("\n⚠️ Maturing within 90 days — plan for reinvestment.")
                else:
                    lines.append("| **Status** | ✅ MATURED " + str(abs(days)) + " days ago |")
            except Exception:
                pass
        lines += [
            "",
            "### At Maturity",
            "- Principal: **" + self._fmt(b.get("face_value",0)) + "** per unit repaid",
            "- Plus final coupon payment",
            "- Total redemption = Face Value + Final Coupon",
        ]
        return "\n".join(lines)

    def _issuer(self):
        b = self.b
        return ("## Issuer — " + b.get("bond_name","") + "\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Issuer Name** | **" + b.get("issuer_name","N/A") + "** |\n"
                "| **Issuer Type** | " + b.get("issuer_type","N/A") + " |\n"
                "| **SEBI Registration** | " + b.get("sebi_registration","N/A") + " |\n"
                "| **Governing Law** | " + b.get("governing_law","N/A") + " |\n"
                "| **Payment Location** | " + b.get("payment_location","N/A") + " |")

    def _identifiers(self):
        b = self.b
        return ("## Bond Identifiers\n\n"
                "- **ISIN:** `" + b.get("isin","N/A") + "`\n"
                "- **Bond Name:** " + b.get("bond_name","N/A") + "\n"
                "- **Exchange:** " + b.get("exchange_listing","N/A") + "\n"
                "- **SEBI Reg:** " + b.get("sebi_registration","N/A"))

    def _rating(self):
        b = self.b
        r = b.get("credit_rating","N/A")
        meaning = ("Highest Safety — virtually no default risk" if "AAA" in (r or "") else
                   "High Safety — very low default risk" if "AA" in (r or "") else
                   "Adequate Safety — low default risk" if r and r.startswith("A") else
                   "Moderate Safety — some default risk" if "BBB" in (r or "") else
                   "Speculative / High Yield — significant risk" if any(x in (r or "") for x in ["BB","B","C","D"]) else "")
        return (
            "## Credit Rating — " + b.get("bond_name","") + "\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| **Rating** | **" + r + "** |\n"
            "| **Agency** | " + b.get("credit_rating_agency","N/A") + " |\n"
            "| **Outlook** | " + b.get("rating_outlook","N/A") + " |\n"
            "| **Meaning** | " + meaning + " |\n\n"
            "### Rating Scale (India)\n"
            "| Rating | Safety Level |\n|--------|-------------|\n"
            "| AAA | Highest |\n| AA+/AA/AA- | High |\n| A+/A/A- | Adequate |\n"
            "| BBB | Moderate |\n| BB and below | Speculative |"
        )

    def _day_count(self):
        b = self.b
        dc = b.get("day_count_convention","Actual/Actual")
        fv = b.get("face_value",0) or 0
        rate = b.get("coupon_rate",0) or 0
        lines = [
            "## Day Count Convention — " + b.get("bond_name",""),
            "",
            "**Convention Used:** **" + dc + "**",
            "",
            "| Convention | Formula | Used In |",
            "|------------|---------|---------|",
            "| Actual/Actual | Actual days / Actual year (365 or 366) | Govt Bonds, US Treasuries |",
            "| Actual/365 | Actual days / 365 | Indian Corp Bonds, UK Gilts |",
            "| Actual/360 | Actual days / 360 | Money market, Eurobonds |",
            "| 30/360 | 30-day months / 360 | US Corp Bonds |",
        ]
        if fv and rate:
            year_days = 360 if "360" in dc else 365
            lines += ["", "### Accrued Interest Examples for This Bond", "", "| Days | Formula | Accrued Interest |", "|------|---------|-----------------|"]
            for days in [30, 90, 180, 365]:
                calc_days = round(days/365*360) if "30/" in dc else days
                accrued = float(fv) * float(rate)/100 * calc_days/year_days
                lines.append("| " + str(days) + " days | " + self._fmt(fv) + " × " + str(rate) + "% × " + str(calc_days) + "/" + str(year_days) + " | **" + self._fmt(accrued) + "** |")
        return "\n".join(lines)

    def _duration(self):
        b = self.b
        tenor = b.get("tenor_years",0) or 0
        rate = b.get("coupon_rate",0) or 0
        mac_dur = round(tenor * 0.85 if rate > 0 else tenor, 2)
        mod_dur = round(mac_dur / (1 + float(rate)/100/2), 2)
        return (
            "## Duration Analysis — " + b.get("bond_name","") + "\n\n"
            "| Measure | Value |\n|---------|-------|\n"
            "| **Tenor** | " + str(tenor) + " years |\n"
            "| **Coupon Rate** | " + str(rate) + "% |\n"
            "| **Macaulay Duration** | ~" + str(mac_dur) + " years |\n"
            "| **Modified Duration** | ~" + str(mod_dur) + " |\n\n"
            "**Interpretation:**\n"
            "- A 1% (100bps) rise in interest rates → ~" + str(mod_dur) + "% fall in bond price\n"
            "- A 1% (100bps) fall in interest rates → ~" + str(mod_dur) + "% rise in bond price\n\n"
            "*Provide current market yield for precise duration calculation.*"
        )

    def _face_value(self):
        b = self.b
        return ("## Face Value / Principal\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Face Value (per unit)** | **" + self._fmt(b.get("face_value")) + "** |\n"
                "| **Principal Amount** | " + self._fmt(b.get("principal_amount")) + " |\n"
                "| **Total Issue Size** | " + self._fmt(b.get("total_issue_size")) + " |\n"
                "| **Outstanding Amount** | " + self._fmt(b.get("outstanding_amount")) + " |\n"
                "| **Currency** | " + b.get("issue_currency","INR") + " |")

    def _issue_size(self):
        b = self.b
        fv = b.get("face_value",0) or 1
        total = b.get("total_issue_size",0) or 0
        units = int(total/fv) if fv else 0
        return ("## Issue Size\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Total Issue Size** | **" + self._fmt(total) + "** |\n"
                "| **Face Value per Unit** | " + self._fmt(b.get("face_value")) + " |\n"
                "| **Outstanding Amount** | " + self._fmt(b.get("outstanding_amount")) + " |\n"
                "| **Number of Units** | " + f"{units:,}" + " |\n"
                "| **Currency** | " + b.get("issue_currency","INR") + " |")

    def _currency(self):
        b = self.b
        return ("## Currency & Denomination\n\n"
                "- **Issue Currency:** **" + b.get("issue_currency","INR") + "**\n"
                "- **Market Type:** " + b.get("domestic_foreign","Domestic") + "\n"
                "- **Settlement:** " + b.get("payment_location","N/A"))

    def _listing(self):
        b = self.b
        return ("## Exchange Listing\n\n"
                "- **Listed On:** **" + b.get("exchange_listing","N/A") + "**\n"
                "- **SEBI Reg:** " + b.get("sebi_registration","N/A") + "\n"
                "- **Market Type:** " + b.get("domestic_foreign","N/A"))

    def _legal(self):
        b = self.b
        return ("## Legal & Regulatory\n\n"
                "- **Governing Law:** " + b.get("governing_law","N/A") + "\n"
                "- **Business Day Convention:** " + b.get("business_day_convention","N/A") + "\n"
                "- **Payment Location:** " + b.get("payment_location","N/A") + "\n"
                "- **SEBI Registration:** " + b.get("sebi_registration","N/A"))

    def _security(self):
        b = self.b
        s = b.get("security_type","N/A")
        return ("## Security & Collateral\n\n"
                "- **Security Type:** **" + s + "**\n\n"
                + ("This is a **SECURED** bond — backed by specific assets of the issuer, providing additional protection in the event of default."
                   if s=="Secured" else
                   "This is an **UNSECURED** bond — bondholders are unsecured creditors. In case of default/insolvency, they rank after secured creditors."))

    def _calculation(self, q):
        b = self.b
        fv = b.get("face_value",0) or 0
        rate = b.get("coupon_rate",0) or 0
        freq = b.get("coupon_frequency","Semi-Annual")
        dc = b.get("day_count_convention","Actual/Actual")
        m = _re.search(r'(\d+)\s*days?', q.lower())
        days = int(m.group(1)) if m else 182
        year_days = 360 if "360" in dc else 365
        calc_days = round(days/365*360) if "30/" in dc else days
        accrued = float(fv)*float(rate)/100*calc_days/year_days if fv and rate else 0
        coupon_per_period = (float(fv)*float(rate)/100)/self._ppY(freq) if fv and rate else 0
        return (
            "## Calculation — " + b.get("bond_name","") + "\n\n"
            "**Day Count Convention:** " + dc + "\n"
            "**Face Value:** " + self._fmt(fv) + " | **Rate:** " + str(rate) + "% p.a.\n\n"
            "### Accrued Interest for " + str(days) + " days\n"
            "= " + self._fmt(fv) + " × " + str(rate) + "% × " + str(calc_days) + "/" + str(year_days) + "\n"
            "= **" + self._fmt(accrued) + "**\n\n"
            "### Coupon per " + freq + " Payment\n"
            "= " + self._fmt(fv) + " × " + str(rate) + "% ÷ " + str(self._ppY(freq)) + "\n"
            "= **" + self._fmt(coupon_per_period) + "**"
        )

    def _general(self):
        b = self.b
        return (
            "## Bizaxl Bond AI — " + b.get("bond_name","") + "\n\n"
            "I have full details about this bond. Ask me:\n\n"
            "| Topic | Sample Question |\n|-------|----------------|\n"
            "| Coupon | *What is the coupon rate?* |\n"
            "| Schedule | *Show full coupon schedule* |\n"
            "| Next Payment | *When is the next payment?* |\n"
            "| Yield | *Calculate yield to maturity* |\n"
            "| Risk | *What are the risk factors?* |\n"
            "| Covenants | *Explain all covenants* |\n"
            "| ESG | *What is the ESG classification?* |\n"
            "| Maturity | *When does this bond mature?* |\n"
            "| Rating | *What is the credit rating?* |\n"
            "| Calculation | *Calculate accrued interest for 90 days* |\n"
            "| Duration | *What is the modified duration?* |\n"
            "| Call Option | *What are the call option terms?* |\n\n"
            "**Bond:** " + b.get("bond_name","N/A") + " | **ISIN:** " + b.get("isin","N/A") + " | **Maturity:** " + str(b.get("maturity_date","N/A"))
        )

    def _search_docs(self, question):
        if not self.doc_text:
            return None
        q_words = set(question.lower().split()) - {"what","is","the","a","an","of","in","for","and","or","this","bond","does","how","when","tell","me","about","show"}
        if not q_words:
            return None
        sentences = _re.split(r'[.!\n]', self.doc_text)
        scored = []
        for s in sentences:
            sl = s.lower()
            score = sum(1 for w in q_words if w in sl)
            if score > 0 and len(s.strip()) > 20:
                scored.append((score, s.strip()))
        scored.sort(reverse=True)
        top = [s[1] for s in scored[:4]]
        if top:
            src = ("\n\n*Source: " + ", ".join(self.doc_names) + "*") if self.doc_names else ""
            return "## From Uploaded Documents\n\n" + "\n\n".join(top) + src
        return None

    def _extract_section(self, kw, max_c):
        if not self.doc_text:
            return ""
        pat = _re.compile(r'(?i)(?:^|\n)([^\n]*(?:' + kw + r')[^\n]*(?:\n(?![A-Z])[^\n]*)*)', _re.MULTILINE)
        matches = pat.findall(self.doc_text)
        return " ".join(matches)[:max_c].strip()

    def _fmt(self, n):
        if n is None or n == "":
            return "N/A"
        try:
            n = float(n)
        except Exception:
            return str(n)
        if n >= 10000000:
            return "₹" + str(round(n/10000000,2)) + "Cr"
        if n >= 100000:
            return "₹" + str(round(n/100000,1)) + "L"
        return "₹" + f"{n:,.0f}"

    def _ppY(self, freq):
        return {"Annual":1,"Semi-Annual":2,"Quarterly":4,"Monthly":12,"At Maturity":1}.get(freq,2)


@frappe.whitelist(allow_guest=True)
def ask_bond_ai(bond_name, question, session_id=None):
    """
    Bizaxl Built-in Bond AI — completely self-contained, no external API key needed.
    Analyzes bond data from the database and uploaded documents.
    """
    try:
        # Load bond details
        bonds = frappe.get_all("Bond Master", filters={"name": bond_name}, fields=["*"], limit=1)
        bond = bonds[0] if bonds else {}

        # Load schedules
        coupons = frappe.get_all("Bond Coupon Schedule", filters={"bond_name": bond_name}, fields=["*"], order_by="coupon_number asc", limit=50)
        steps = frappe.get_all("Bond Step Schedule", filters={"bond_name": bond_name}, fields=["*"], order_by="period_from asc")
        amort = frappe.get_all("Bond Amortization Schedule", filters={"bond_name": bond_name}, fields=["*"], order_by="payment_number asc", limit=30)

        # Load processed documents
        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name, "processing_status": "Ready"},
            fields=["document_name", "document_type", "extracted_text", "document_summary", "key_terms_json"],
            order_by="modified desc", limit=3
        )

        # Run the engine
        engine = _BondEngine(bond, coupons, steps, amort, docs)
        answer = engine.answer(question)

        # Save to chat history
        if not session_id:
            session_id = "SESSION-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        try:
            chat = frappe.get_doc({
                "doctype": "Bond AI Chat",
                "bond_name": bond_name,
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "model_used": "Bizaxl Bond AI Engine v1",
                "tokens_used": 0,
                "asked_by": frappe.session.user,
                "asked_on": datetime.datetime.now(),
                "sources_cited": ", ".join([d.get("document_name","") for d in docs])
            })
            chat.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [d.get("document_name","") for d in docs],
            "success": True
        }

    except Exception as e:
        frappe.log_error(str(e), "ask_bond_ai")
        return {"answer": "Error: " + str(e), "session_id": session_id or "", "sources": [], "success": False}


@frappe.whitelist(allow_guest=True)
def extract_bond_from_file(file_url, document_name="Bond Document"):
    """
    Extract bond details from an uploaded file using pattern matching.
    Returns bond field values to auto-fill the Add Bond form.
    No external API needed.
    """
    try:
        if not file_url:
            return {"status": "error", "message": "No file URL provided"}

        # Read the file
        text = ""
        try:
            site_path = frappe.get_site_path()
            # Try multiple path patterns
            for path in [site_path + file_url, site_path + "/public" + file_url, "." + file_url]:
                try:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    text = raw.decode('utf-8', errors='ignore')
                    if text.strip():
                        break
                except Exception:
                    continue
        except Exception as fe:
            return {"status": "error", "message": "Cannot read file: " + str(fe)}

        if not text or len(text.strip()) < 50:
            return {"status": "error", "message": "File is empty or unreadable. Please use a plain-text PDF or .txt file."}

        # Extract bond fields using regex patterns
        def find(patterns, txt=text):
            for pat in patterns:
                m = _re.search(pat, txt, _re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            return None

        def find_amount(patterns, txt=text):
            for pat in patterns:
                m = _re.search(pat, txt, _re.IGNORECASE)
                if m:
                    raw = m.group(1).replace(",","").strip()
                    # Handle crores
                    if _re.search(r'crore|cr\.?', txt[max(0,m.start()-20):m.end()+20], _re.I):
                        try:
                            return str(int(float(raw) * 10000000))
                        except Exception:
                            pass
                    # Handle lakhs
                    if _re.search(r'lakh|lac', txt[max(0,m.start()-20):m.end()+20], _re.I):
                        try:
                            return str(int(float(raw) * 100000))
                        except Exception:
                            pass
                    return raw
            return None

        def find_date(patterns, txt=text):
            for pat in patterns:
                m = _re.search(pat, txt, _re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    # Try to parse and normalize to YYYY-MM-DD
                    for fmt in ["%d %B %Y", "%d-%m-%Y", "%d/%m/%Y", "%B %d, %Y", "%d %b %Y", "%Y-%m-%d"]:
                        try:
                            return datetime.datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    return raw
            return None

        fields = {}

        # Bond/Issuer name
        fields["bond_name"] = find([
            r'(?:security description|bond name|name of (?:the )?(?:bond|security|instrument))[:\s]+([^\n]{5,80})',
            r'(?:debentures?|bonds?|notes?)[:\s]+([A-Z][^\n]{5,60})',
        ]) or document_name.replace(".pdf","").replace(".txt","").replace("_PROSP","").replace("_"," ").strip()

        # ISIN
        fields["isin"] = find([r'\bISIN\b[:\s#]*([A-Z]{2}[A-Z0-9]{10})\b', r'\b(IN[A-Z0-9]{10})\b'])

        # Issuer
        fields["issuer_name"] = find([
            r'(?:issuer|company|borrower)[:\s]+([A-Z][A-Za-z\s\.]+(?:Limited|Ltd\.?|Corporation|Corp\.?|LLP|Inc\.?|Bank|Finance|Infra))',
            r'^([A-Z][A-Za-z\s\.]+(?:Limited|Ltd\.?|Corporation|Bank|Finance))',
        ])

        # Coupon rate
        cr = find([
            r'(?:coupon rate|interest rate|rate of interest)[:\s]+([\d\.]+)\s*%',
            r'([\d\.]+)\s*%\s*(?:per annum|p\.?a\.?|fixed)',
        ])
        if cr:
            try:
                fields["coupon_rate"] = str(round(float(cr), 4))
            except Exception:
                fields["coupon_rate"] = cr

        # Coupon type
        ct = text.lower()
        if "step-up" in ct or "step up" in ct:
            fields["coupon_type"] = "Step-Up"
        elif "floating" in ct or "variable" in ct:
            fields["coupon_type"] = "Floating"
        elif "zero coupon" in ct or "zero-coupon" in ct:
            fields["coupon_type"] = "Zero Coupon"
        else:
            fields["coupon_type"] = "Fixed"

        # Coupon frequency
        if "semi-annual" in ct or "semi annual" in ct or "half.yearly" in ct:
            fields["coupon_frequency"] = "Semi-Annual"
        elif "quarterly" in ct:
            fields["coupon_frequency"] = "Quarterly"
        elif "monthly" in ct:
            fields["coupon_frequency"] = "Monthly"
        elif "at maturity" in ct or "on maturity" in ct:
            fields["coupon_frequency"] = "At Maturity"
        else:
            fields["coupon_frequency"] = "Annual"

        # Bond type
        if "government" in ct or "g-sec" in ct or "gilt" in ct or "sovereign" in ct:
            fields["bond_type"] = "Government Bond"
        elif "convertible" in ct:
            fields["bond_type"] = "Convertible"
        elif "zero coupon" in ct:
            fields["bond_type"] = "Zero Coupon"
        else:
            fields["bond_type"] = "Corporate Bond"

        # Security type
        fields["security_type"] = "Secured" if "secured" in ct and "unsecured" not in ct else "Unsecured"

        # Issue date
        fields["issue_date"] = find_date([
            r'(?:issue date|date of issue|allotment date)[:\s]+([\d]+(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(?:issue date|date of issue)[:\s]+(\d{4}-\d{2}-\d{2})',
        ])

        # Maturity date
        fields["maturity_date"] = find_date([
            r'(?:maturity date|redemption date|date of redemption|due date)[:\s]+([\d]+(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ])

        # First coupon date
        fields["first_coupon_date"] = find_date([
            r'(?:first coupon date|first interest payment)[:\s]+([\d]+(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ])

        # Tenor
        tenor = find([r'(?:tenor|period|term)[:\s]+([\d]+)\s*(?:years?|yrs?)', r'([\d]+)\s*years?\s*(?:from|bonds?)'])
        if tenor:
            fields["tenor_years"] = tenor
        elif fields.get("issue_date") and fields.get("maturity_date"):
            try:
                d1 = datetime.date.fromisoformat(fields["issue_date"])
                d2 = datetime.date.fromisoformat(fields["maturity_date"])
                fields["tenor_years"] = str(round((d2-d1).days/365.25, 1))
            except Exception:
                pass

        # Face value
        fv = find_amount([
            r'(?:face value|nominal value|par value)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)',
            r'(?:face value|par value)[:\s]+([\d,]+)',
        ])
        if fv:
            fields["face_value"] = fv

        # Issue size
        sz = find_amount([
            r'(?:issue size|total issue|aggregate amount|issue amount)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
            r'(?:aggregate principal amount)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
        ])
        if sz:
            fields["total_issue_size"] = sz

        # Principal amount
        pa = find_amount([
            r'(?:principal amount|base amount)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
        ])
        if pa:
            fields["principal_amount"] = pa

        # Currency
        if "usd" in ct or "u.s. dollar" in ct or "dollar" in ct:
            fields["issue_currency"] = "USD"
        elif "eur" in ct or "euro" in ct:
            fields["issue_currency"] = "EUR"
        elif "gbp" in ct or "sterling" in ct:
            fields["issue_currency"] = "GBP"
        else:
            fields["issue_currency"] = "INR"

        # Credit rating
        rating_match = _re.search(
            r'\b(AAA|AA\+?-?|A\+?-?|BBB\+?-?|BB\+?-?|B\+?-?|C(?:CC)?|D)\b(?:\s*\(SO\)|\s*\(CE\))?',
            text
        )
        if rating_match:
            fields["credit_rating"] = rating_match.group(0).strip()

        # Rating agency
        if "crisil" in ct:
            fields["credit_rating_agency"] = "CRISIL"
        elif "icra" in ct:
            fields["credit_rating_agency"] = "ICRA"
        elif "care" in ct:
            fields["credit_rating_agency"] = "CARE"
        elif "india ratings" in ct or "ind-ra" in ct:
            fields["credit_rating_agency"] = "India Ratings"
        elif "moody" in ct:
            fields["credit_rating_agency"] = "Moody's"
        elif "s&p" in ct or "standard & poor" in ct:
            fields["credit_rating_agency"] = "S&P"
        elif "fitch" in ct:
            fields["credit_rating_agency"] = "Fitch"

        # Rating outlook
        if "stable" in ct:
            fields["rating_outlook"] = "Stable"
        elif "positive" in ct:
            fields["rating_outlook"] = "Positive"
        elif "negative" in ct:
            fields["rating_outlook"] = "Negative"
        elif "watch" in ct:
            fields["rating_outlook"] = "Watch"

        # ESG
        if "green bond" in ct:
            fields["esg_classification"] = "Green Bond"
        elif "blue bond" in ct:
            fields["esg_classification"] = "Blue Bond"
        elif "social bond" in ct:
            fields["esg_classification"] = "Social Bond"
        elif "sustainability bond" in ct:
            fields["esg_classification"] = "Sustainability Bond"
        elif "climate bond" in ct:
            fields["esg_classification"] = "Climate Bond"
        else:
            fields["esg_classification"] = "None"

        # Day count
        if "actual/actual" in ct or "act/act" in ct:
            fields["day_count_convention"] = "Actual/Actual"
        elif "actual/360" in ct or "act/360" in ct:
            fields["day_count_convention"] = "Actual/360"
        elif "30/360" in ct:
            fields["day_count_convention"] = "30/360"
        else:
            fields["day_count_convention"] = "Actual/365"

        # Exchange listing
        if "nse" in ct and "bse" in ct:
            fields["exchange_listing"] = "NSE+BSE"
        elif "nse" in ct:
            fields["exchange_listing"] = "NSE"
        elif "bse" in ct:
            fields["exchange_listing"] = "BSE"

        # Governing law
        if "indian law" in ct or "laws of india" in ct:
            fields["governing_law"] = "Indian Law"
        elif "english law" in ct or "uk law" in ct:
            fields["governing_law"] = "UK English Law"
        elif "new york" in ct:
            fields["governing_law"] = "New York Law"
        else:
            fields["governing_law"] = "Indian Law"

        # Use of proceeds
        uop = find([
            r'(?:use of proceeds|utilization of proceeds|object(?:ive)?s? of the issue)[:\s\n]+([^\n]{20,500})',
        ])
        if uop:
            fields["use_of_proceeds"] = uop[:500]

        # SEBI registration
        fields["sebi_registration"] = find([
            r'(?:SEBI registration|SEBI reg(?:istration)? (?:no|number))[.:\s#]+([A-Z0-9/\-]+)',
        ])

        # Is callable
        fields["is_callable"] = 1 if "call option" in ct or "callable" in ct else 0
        fields["is_puttable"] = 1 if "put option" in ct or "puttable" in ct else 0
        fields["is_convertible"] = 1 if "convertible" in ct and "non-convertible" not in ct else 0
        fields["is_amortizing"] = 1 if "amortizing" in ct or "amortization" in ct else 0

        # Remove None values
        fields = {k: v for k, v in fields.items() if v is not None and v != ""}

        return {
            "status": "success",
            "bond_fields": fields,
            "message": "Extracted " + str(len(fields)) + " fields from " + document_name,
            "text_preview": text[:200]
        }

    except Exception as e:
        frappe.log_error(str(e), "extract_bond_from_file")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def process_bond_document(bond_doc_name):
    """Process an uploaded bond document — extract text and mark as Ready."""
    try:
        doc = frappe.get_doc("Bond Document", bond_doc_name)
        file_url = doc.file_attachment or ""
        extracted_text = ""
        if file_url:
            site_path = frappe.get_site_path()
            for path in [site_path + file_url, site_path + "/public" + file_url]:
                try:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    extracted_text = raw.decode('utf-8', errors='ignore')
                    if extracted_text.strip():
                        break
                except Exception:
                    continue

        summary = extracted_text[:500] if extracted_text else "Document uploaded — text extraction available."

        doc.processing_status = "Ready"
        doc.extracted_text = extracted_text[:100000] if extracted_text else ""
        doc.document_summary = summary
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Document processed. " + str(len(extracted_text)) + " characters extracted.",
            "chars_extracted": len(extracted_text)
        }
    except Exception as e:
        frappe.log_error(str(e), "process_bond_document")
        return {"status": "error", "message": str(e)}
