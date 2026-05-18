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
    """
    Bizaxl Bond AI Engine - answers from uploaded documents first, then DB data.
    No external API needed.
    """

    def __init__(self, bond, coupons, steps, amort, documents):
        self.b = bond or {}
        self.coupons = coupons or []
        self.steps = steps or []
        self.amort = amort or []
        # Build full document text from all processed docs
        doc_parts = []
        for d in (documents or []):
            txt = d.get("extracted_text") or d.get("document_summary") or ""
            if txt.strip():
                doc_parts.append("[DOC: " + str(d.get("document_name","")) + "]\n" + txt)
        self.doc_text = "\n\n".join(doc_parts)[:100000]
        self.doc_names = [str(d.get("document_name","")) for d in (documents or []) if d.get("document_name")]
        self.has_docs = bool(self.doc_text.strip())

    def _s(self, v, default="N/A"):
        """Safely convert any value (including None) to string."""
        if v is None:
            return default
        s = str(v).strip()
        return s if s else default

    def _fmt(self, n):
        if n is None or n == "":
            return "N/A"
        try:
            n = float(n)
        except Exception:
            return str(n)
        if n >= 10000000:
            return "Rs." + str(round(n/10000000, 2)) + " Cr"
        if n >= 100000:
            return "Rs." + str(round(n/100000, 1)) + " L"
        return "Rs.{:,.0f}".format(n)

    def _ppY(self, freq):
        return {"Annual": 1, "Semi-Annual": 2, "Quarterly": 4,
                "Monthly": 12, "At Maturity": 1}.get(str(freq or ""), 2)

    def answer(self, q):
        ql = q.lower().strip()
        b = self.b

        # PRIORITY 1: If document is uploaded, search it first for specific questions
        if self.has_docs:
            doc_answer = self._answer_from_doc(q, ql)
            if doc_answer:
                return doc_answer

        # PRIORITY 2: Answer from DB data
        if any(w in ql for w in ["coupon schedule","all coupon","all payment","list coupon","payment schedule"]):
            return self._coupon_schedule()
        if any(w in ql for w in ["next coupon","next payment","upcoming coupon","when is next","upcoming payment"]):
            return self._next_coupon()
        if any(w in ql for w in ["coupon rate","interest rate","what rate","rate per annum","rate %"]):
            return self._coupon_rate()
        if any(w in ql for w in ["ytm","yield to maturity","yield to call","ytc","calculate yield"]):
            return self._yield_analysis()
        if any(w in ql for w in ["amortiz","principal repay","principal schedule"]):
            return self._amortization()
        if any(w in ql for w in ["step-up","step up","step schedule","step-down","step rate"]):
            return self._step_schedule()
        if any(w in ql for w in ["risk factor","credit risk","default risk","market risk","risk"]):
            return self._risk_factors()
        if any(w in ql for w in ["covenant","restriction","events of default","affirmative covenant"]):
            return self._covenants()
        if any(w in ql for w in ["esg","green bond","use of proceed","sustainability","climate bond","social bond"]):
            return self._esg()
        if any(w in ql for w in ["call option","callable","call date","call price"]):
            return self._call_option()
        if any(w in ql for w in ["put option","puttable","put date"]):
            return self._put_option()
        if any(w in ql for w in ["convert","convertible","conversion ratio","conversion price"]):
            return self._convertible()
        if any(w in ql for w in ["maturity","matures","maturity date","redemption date","when does"]):
            return self._maturity()
        if any(w in ql for w in ["issuer","who issued","company name","issuer name"]):
            return self._issuer()
        if any(w in ql for w in ["isin","identifier","bond code"]):
            return self._identifiers()
        if any(w in ql for w in ["rating","credit rating","crisil","icra","care","moody","fitch"]):
            return self._rating()
        if any(w in ql for w in ["day count","accrued interest","accrual","30/360","actual/actual"]):
            return self._day_count()
        if any(w in ql for w in ["duration","modified duration","macaulay","dv01"]):
            return self._duration()
        if any(w in ql for w in ["face value","par value","nominal value"]):
            return self._face_value()
        if any(w in ql for w in ["issue size","total issue","outstanding amount"]):
            return self._issue_size()
        if any(w in ql for w in ["summary","overview","about this bond","tell me about","describe","details"]):
            return self._summary()
        if any(w in ql for w in ["calculate","compute","how much","accrue","interest for"]):
            return self._calculation(q)

        # PRIORITY 3: General fallback
        return self._general()

    def _answer_from_doc(self, question, ql):
        """
        Search the uploaded document text and return relevant sections.
        This is the PRIMARY answer source when docs are available.
        """
        if not self.doc_text:
            return None

        # Split into sentences/paragraphs
        import re
        # Split by newlines and sentences
        chunks = []
        for para in self.doc_text.split("\n"):
            para = para.strip()
            if len(para) > 20:
                chunks.append(para)

        if not chunks:
            return None

        # Score each chunk against the question
        q_words = set(ql.split())
        # Remove stop words
        stop = {"what","is","the","a","an","of","in","for","and","or","this",
                "bond","does","how","when","tell","me","about","show","are",
                "can","you","please","give","explain","describe","list","all"}
        q_words -= stop

        if not q_words:
            q_words = set(ql.split())  # use all words if all were stop words

        scored = []
        for chunk in chunks:
            cl = chunk.lower()
            # Exact phrase match gets bonus
            phrase_score = 3 if ql[:20] in cl else 0
            word_score = sum(1 for w in q_words if w in cl)
            total = phrase_score + word_score
            if total > 0:
                scored.append((total, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return None

        # Take top relevant chunks
        top_chunks = [c[1] for c in scored[:8] if c[0] >= 1]

        if not top_chunks:
            return None

        # Build answer
        doc_label = ", ".join(self.doc_names) if self.doc_names else "uploaded document"
        answer = "## Answer from Document\n"
        answer += "*Source: " + doc_label + "*\n\n"

        # Format the chunks nicely
        seen = set()
        unique_chunks = []
        for chunk in top_chunks:
            # Deduplicate
            key = chunk[:50].lower()
            if key not in seen:
                seen.add(key)
                unique_chunks.append(chunk)

        answer += "\n\n".join(unique_chunks[:6])

        # Add bond DB context if relevant
        b = self.b
        bond_name = self._s(b.get("bond_name"), "")
        if bond_name:
            answer += "\n\n---\n**Bond:** " + bond_name
            if b.get("isin"):
                answer += " | **ISIN:** " + self._s(b.get("isin"))
        return answer

    def _summary(self):
        b = self.b
        rows = [
            ("ISIN", "`" + self._s(b.get("isin")) + "`"),
            ("Issuer", self._s(b.get("issuer_name")) + " (" + self._s(b.get("issuer_type"), "") + ")"),
            ("Bond Type", self._s(b.get("bond_type"))),
            ("Coupon", "**" + self._s(b.get("coupon_rate"), "0") + "%** " + self._s(b.get("coupon_type"), "") + " " + self._s(b.get("coupon_frequency"), "")),
            ("Issue Date", self._s(b.get("issue_date"))),
            ("Maturity Date", "**" + self._s(b.get("maturity_date")) + "**"),
            ("Tenor", self._s(b.get("tenor_years")) + " years"),
            ("Face Value", self._fmt(b.get("face_value"))),
            ("Total Issue Size", self._fmt(b.get("total_issue_size"))),
            ("Credit Rating", "**" + self._s(b.get("credit_rating")) + "** (" + self._s(b.get("credit_rating_agency")) + ") — " + self._s(b.get("rating_outlook"), "")),
            ("Security", self._s(b.get("security_type"))),
            ("Currency", self._s(b.get("issue_currency"), "INR")),
            ("Exchange", self._s(b.get("exchange_listing"))),
            ("ESG", self._s(b.get("esg_classification"), "None")),
            ("Day Count", self._s(b.get("day_count_convention"))),
        ]
        lines = ["## Bond Summary — " + self._s(b.get("bond_name"), ""), "", "| Field | Value |", "|-------|-------|"]
        for label, val in rows:
            lines.append("| **" + label + "** | " + val + " |")
        if b.get("use_of_proceeds"):
            lines += ["", "**Use of Proceeds:** " + self._s(b.get("use_of_proceeds"), "")]
        if self.coupons:
            lines += ["", "**" + str(len(self.coupons)) + " coupon payments** scheduled. Ask *Show coupon schedule* for full list."]
        if self.doc_names:
            lines += ["", "**Documents:** " + ", ".join(self.doc_names)]
        return "\n".join(lines)

    def _coupon_schedule(self):
        b = self.b
        if not self.coupons:
            fv = float(b.get("face_value") or 0)
            rate = float(b.get("coupon_rate") or 0)
            freq = self._s(b.get("coupon_frequency"), "Semi-Annual")
            amt = (fv * rate / 100) / self._ppY(freq) if fv and rate else 0
            return ("## Coupon Schedule — " + self._s(b.get("bond_name"), "") + "\n\n"
                    "No coupon records stored yet.\n\n"
                    "**Bond Terms:**\n"
                    "- Rate: **" + str(rate) + "% p.a.**\n"
                    "- Frequency: " + freq + "\n"
                    "- Face Value: " + self._fmt(fv) + "\n"
                    "- Day Count: " + self._s(b.get("day_count_convention"), "N/A") + "\n\n"
                    "Estimated coupon/unit = " + self._fmt(fv) + " x " + str(rate) + "% / " + str(self._ppY(freq)) + " = **" + self._fmt(amt) + "**")
        today = str(__import__("datetime").date.today())
        lines = ["## Coupon Schedule — " + self._s(b.get("bond_name"), ""), "",
                 "Rate: **" + str(b.get("coupon_rate") or 0) + "% p.a.** | Freq: " + self._s(b.get("coupon_frequency"), ""),
                 "", "| # | Date | Rate | Amt/Unit | Total | Status |",
                 "|---|------|------|----------|-------|--------|"]
        paid = 0; total_paid = 0; total_pend = 0
        for c in self.coupons:
            s = self._s(c.get("status"), "Upcoming")
            marker = " <-- NEXT" if s == "Upcoming" and paid == len([x for x in self.coupons if (x.get("status") or "") == "Paid"]) else ""
            lines.append("| " + self._s(c.get("coupon_number"), "?") +
                         " | " + self._s(c.get("coupon_date"), "?") +
                         " | " + str(c.get("coupon_rate_applicable") or 0) + "%" +
                         " | " + self._fmt(c.get("coupon_amount_per_unit")) +
                         " | " + self._fmt(c.get("total_coupon_amount")) +
                         " | " + s + marker + " |")
            if s == "Paid":
                paid += 1; total_paid += float(c.get("total_coupon_amount") or 0)
            else:
                total_pend += float(c.get("total_coupon_amount") or 0)
        lines += ["", "**Paid:** " + self._fmt(total_paid) + " | **Pending:** " + self._fmt(total_pend)]
        return "\n".join(lines)

    def _next_coupon(self):
        b = self.b
        today = str(__import__("datetime").date.today())
        upcoming = [c for c in self.coupons if self._s(c.get("coupon_date"), "") > today and (c.get("status") or "") != "Paid"]
        if upcoming:
            c = upcoming[0]
            return ("## Next Coupon Payment\n\n"
                    "| Field | Value |\n|-------|-------|\n"
                    "| **Bond** | " + self._s(b.get("bond_name")) + " |\n"
                    "| **Coupon #** | " + self._s(c.get("coupon_number"), "?") + " |\n"
                    "| **Payment Date** | **" + self._s(c.get("coupon_date"), "N/A") + "** |\n"
                    "| **Rate** | " + str(c.get("coupon_rate_applicable") or 0) + "% p.a. |\n"
                    "| **Amount per Unit** | **" + self._fmt(c.get("coupon_amount_per_unit")) + "** |\n"
                    "| **Total Payable** | " + self._fmt(c.get("total_coupon_amount")) + " |\n"
                    "| **Status** | " + self._s(c.get("status"), "Upcoming") + " |\n\n"
                    "*" + str(len(upcoming)) + " coupon payment(s) remaining.*")
        fv = float(b.get("face_value") or 0)
        rate = float(b.get("coupon_rate") or 0)
        freq = self._s(b.get("coupon_frequency"), "Semi-Annual")
        amt = (fv * rate / 100) / self._ppY(freq) if fv and rate else 0
        return ("## Next Coupon\n\nNo upcoming coupon records stored.\n\n"
                "**Estimated from bond terms:**\n"
                "- Rate: " + str(rate) + "% | Frequency: " + freq + "\n"
                "- Face Value: " + self._fmt(fv) + "\n"
                "- Expected Amount/Unit: **" + self._fmt(amt) + "**")

    def _coupon_rate(self):
        b = self.b
        fv = float(b.get("face_value") or 0)
        rate = float(b.get("coupon_rate") or 0)
        freq = self._s(b.get("coupon_frequency"), "Semi-Annual")
        amt = (fv * rate / 100) / self._ppY(freq) if fv and rate else 0
        lines = ["## Coupon Rate — " + self._s(b.get("bond_name"), ""), "",
                 "| Parameter | Value |", "|-----------|-------|",
                 "| **Coupon Type** | " + self._s(b.get("coupon_type"), "Fixed") + " |",
                 "| **Annual Coupon Rate** | **" + str(rate) + "% per annum** |",
                 "| **Coupon Frequency** | " + freq + " |",
                 "| **Day Count** | " + self._s(b.get("day_count_convention"), "N/A") + " |"]
        if b.get("coupon_type") in ("Floating", "Variable"):
            lines += ["| **Benchmark** | " + self._s(b.get("benchmark_rate"), "N/A") + " |",
                      "| **Spread (bps)** | " + str(b.get("spread_bps") or 0) + " |"]
        if fv and rate:
            lines += ["", "**Coupon per payment = " + self._fmt(fv) + " x " + str(rate) + "% / " + str(self._ppY(freq)) + " = **" + self._fmt(amt) + "**",
                      "**Annual income per unit = **" + self._fmt(amt * self._ppY(freq)) + "**"]
        return "\n".join(lines)

    def _yield_analysis(self):
        b = self.b
        rate = float(b.get("coupon_rate") or 0)
        fv = float(b.get("face_value") or 0)
        tenor = float(b.get("tenor_years") or 0)
        ann_coupon = fv * rate / 100 if fv and rate else 0
        lines = ["## Yield Analysis — " + self._s(b.get("bond_name"), ""), "",
                 "**Coupon:** " + str(rate) + "% | **Face Value:** " + self._fmt(fv) + " | **Maturity:** " + self._s(b.get("maturity_date")), "",
                 "### YTM Formula", "YTM = [Annual Coupon + (Face Value - Price) / Years] / [(Face Value + Price) / 2]", ""]
        if fv and rate and tenor:
            lines += ["### At Different Market Prices",
                      "| Price | Premium/Discount | YTM |", "|-------|-----------------|-----|"]
            for pct in [92, 95, 97, 100, 103, 105, 108]:
                price = fv * pct / 100
                ytm = ((ann_coupon + (fv - price) / tenor) / ((fv + price) / 2)) * 100
                pd = "Par" if pct == 100 else ("Premium +" + str(pct - 100) + "%" if pct > 100 else "Discount -" + str(100 - pct) + "%")
                lines.append("| " + self._fmt(price) + " | " + pd + " | **" + str(round(ytm, 2)) + "%** |")
        return "\n".join(lines)

    def _amortization(self):
        b = self.b
        if not self.amort:
            is_amort = b.get("is_amortizing")
            return ("## Amortization — " + self._s(b.get("bond_name"), "") + "\n\n"
                    + ("No schedule stored. **Bullet bond** — full principal " + self._fmt(b.get("face_value")) + " repaid on " + self._s(b.get("maturity_date"))
                       if not is_amort else "Please add amortization schedule records."))
        lines = ["## Amortization Schedule — " + self._s(b.get("bond_name"), ""), "",
                 "| # | Date | Opening | Coupon | Principal | Total | Closing |",
                 "|---|------|---------|--------|-----------|-------|---------|"]
        for a in self.amort:
            lines.append("| " + self._s(a.get("payment_number"), "?") +
                         " | " + self._s(a.get("payment_date"), "?") +
                         " | " + self._fmt(a.get("opening_principal")) +
                         " | " + self._fmt(a.get("coupon_payment")) +
                         " | " + self._fmt(a.get("principal_payment")) +
                         " | " + self._fmt(a.get("total_payment")) +
                         " | " + self._fmt(a.get("closing_principal")) + " |")
        return "\n".join(lines)

    def _step_schedule(self):
        b = self.b
        if not self.steps:
            return ("## Step Schedule — " + self._s(b.get("bond_name"), "") + "\n\n"
                    "No step schedule. Coupon type: " + self._s(b.get("coupon_type"), "Fixed") +
                    " at " + str(b.get("coupon_rate") or 0) + "% p.a.")
        lines = ["## Step Schedule — " + self._s(b.get("bond_name"), ""), "",
                 "| Period From | Period To | Rate | Type | Benchmark | Spread |",
                 "|-------------|-----------|------|------|-----------|--------|"]
        for s in self.steps:
            lines.append("| " + self._s(s.get("period_from")) + " | " + self._s(s.get("period_to")) +
                         " | **" + str(s.get("coupon_rate") or 0) + "%** | " + self._s(s.get("rate_type"), "-") +
                         " | " + self._s(s.get("benchmark"), "-") + " | " + str(s.get("spread_bps") or 0) + "bps |")
        return "\n".join(lines)

    def _risk_factors(self):
        b = self.b
        rating = self._s(b.get("credit_rating"), "")
        risk = ("Low" if any(x in rating for x in ["AAA", "Sovereign"]) else
                "Moderate-Low" if "AA" in rating else
                "Moderate" if "A" in rating else
                "High" if any(x in rating for x in ["B", "C", "D"]) else "Moderate")
        lines = ["## Risk Factors — " + self._s(b.get("bond_name"), ""), "",
                 "**1. Credit Risk — " + risk + "**",
                 "- Rating: **" + rating + "** (" + self._s(b.get("credit_rating_agency"), "") + ") | Outlook: " + self._s(b.get("rating_outlook"), "N/A"),
                 "- Issuer: " + self._s(b.get("issuer_name"), "N/A") + " (" + self._s(b.get("issuer_type"), "") + ")", "",
                 "**2. Interest Rate Risk**",
                 "- Tenor: " + str(b.get("tenor_years") or "?") + " years | Coupon: " + self._s(b.get("coupon_type"), "Fixed"),
                 "- " + ("Fixed rate — price falls if rates rise" if (b.get("coupon_type") or "") == "Fixed" else "Floating rate — resets with market"), "",
                 "**3. Liquidity Risk** — Exchange: " + self._s(b.get("exchange_listing"), "N/A"),
                 "**4. Reinvestment Risk** — " + self._s(b.get("coupon_frequency"), "N/A") + " coupons must be reinvested",
                 "**5. Call Risk** — " + ("Callable on " + self._s(b.get("call_date"), "?") if b.get("is_callable") else "Not callable")]
        if self.has_docs:
            doc_sec = self._extract_section("risk|default|credit")
            if doc_sec:
                lines += ["", "### From Uploaded Document:", "", doc_sec[:1000]]
        return "\n".join(lines)

    def _covenants(self):
        b = self.b
        lines = ["## Covenants & Restrictions — " + self._s(b.get("bond_name"), ""), "",
                 "**Issuer:** " + self._s(b.get("issuer_name"), "N/A") + " | **Security:** " + self._s(b.get("security_type"), "N/A"), "",
                 "**Negative Covenants:**",
                 "- No additional secured borrowings beyond agreed limit",
                 "- No disposal of core assets without bondholder consent",
                 "- Dividend restrictions if financial ratios breach thresholds", "",
                 "**Affirmative Covenants:**",
                 "- Regular financial reporting to bondholders",
                 "- Notify on rating changes, litigation, restructuring",
                 "- Maintain pledged security / financial health ratios", "",
                 "**Events of Default:**",
                 "- Non-payment of coupon or principal on due date",
                 "- Cross-default on other material debt",
                 "- Insolvency / winding up proceedings"]
        if self.has_docs:
            doc_sec = self._extract_section("covenant|restriction|event of default|accelerat")
            if doc_sec:
                lines += ["", "### From Prospectus:", "", doc_sec[:1200]]
        return "\n".join(lines)

    def _esg(self):
        b = self.b
        esg = self._s(b.get("esg_classification"), "None")
        if esg == "None":
            return "## ESG — " + self._s(b.get("bond_name"), "") + "\n\nThis bond is **not classified as an ESG bond**."
        lines = ["## ESG — " + self._s(b.get("bond_name"), ""), "", "**Classification: " + esg + "**", ""]
        if b.get("use_of_proceeds"):
            lines += ["**Use of Proceeds:** " + self._s(b.get("use_of_proceeds"), "")]
        if self.has_docs:
            doc_sec = self._extract_section("esg|green|sustainability|climate|social|proceed")
            if doc_sec:
                lines += ["", "### From Prospectus:", "", doc_sec[:1000]]
        return "\n".join(lines)

    def _call_option(self):
        b = self.b
        if not b.get("is_callable"):
            return "## Call Option\n\nThis bond **is NOT callable**. Issuer cannot redeem before maturity on " + self._s(b.get("maturity_date"), "N/A") + "."
        return ("## Call Option\n\n**This bond IS CALLABLE**\n\n"
                "| Call Date | Call Price |\n|-----------|------------|\n"
                "| **" + self._s(b.get("call_date"), "N/A") + "** | **" + self._s(b.get("call_price"), "N/A") + "** |\n\n"
                "Issuer may redeem early — evaluate YTC vs YTM.")

    def _put_option(self):
        b = self.b
        if not b.get("is_puttable"):
            return "## Put Option\n\nThis bond **is NOT puttable**."
        return ("## Put Option\n\n**This bond IS PUTTABLE** — investors can sell back\n\n"
                "| Put Date | Put Price |\n|----------|-----------|\n"
                "| **" + self._s(b.get("put_date"), "N/A") + "** | **" + self._s(b.get("put_price"), "N/A") + "** |")

    def _convertible(self):
        b = self.b
        if not b.get("is_convertible"):
            return "## Convertible\n\nThis bond **is NOT convertible** into equity."
        return ("## Convertible Bond\n\n**IS CONVERTIBLE** into equity shares\n\n"
                "- Conversion Ratio: **" + self._s(b.get("conversion_ratio"), "N/A") + "** shares per bond\n"
                "- Conversion Price: **" + self._s(b.get("conversion_price"), "N/A") + "**")

    def _maturity(self):
        b = self.b
        import datetime
        maturity = b.get("maturity_date")
        today = datetime.date.today()
        lines = ["## Maturity Details — " + self._s(b.get("bond_name"), ""), "",
                 "| Field | Value |", "|-------|-------|",
                 "| **Maturity Date** | **" + self._s(maturity) + "** |",
                 "| **Issue Date** | " + self._s(b.get("issue_date")) + " |",
                 "| **Tenor** | " + str(b.get("tenor_years") or "N/A") + " years |"]
        if maturity:
            try:
                mat = datetime.date.fromisoformat(str(maturity))
                days = (mat - today).days
                if days > 0:
                    lines += ["| **Days to Maturity** | " + str(days) + " days (" + str(round(days/365.25, 1)) + " yrs) |",
                              "| **Status** | Active |"]
                    if days <= 30:
                        lines.append("\n**ALERT: Maturing in " + str(days) + " days!**")
                else:
                    lines.append("| **Status** | MATURED " + str(abs(days)) + " days ago |")
            except Exception:
                pass
        lines += ["", "At maturity: Face Value **" + self._fmt(b.get("face_value")) + "** + final coupon repaid."]
        return "\n".join(lines)

    def _issuer(self):
        b = self.b
        return ("## Issuer\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Name** | **" + self._s(b.get("issuer_name")) + "** |\n"
                "| **Type** | " + self._s(b.get("issuer_type")) + " |\n"
                "| **SEBI Reg** | " + self._s(b.get("sebi_registration")) + " |\n"
                "| **Governing Law** | " + self._s(b.get("governing_law")) + " |")

    def _identifiers(self):
        b = self.b
        return ("## Bond Identifiers\n\n"
                "- **ISIN:** `" + self._s(b.get("isin")) + "`\n"
                "- **Bond Name:** " + self._s(b.get("bond_name")) + "\n"
                "- **Exchange:** " + self._s(b.get("exchange_listing")))

    def _rating(self):
        b = self.b
        r = self._s(b.get("credit_rating"), "N/A")
        meaning = ("Highest Safety" if "AAA" in r else "High Safety" if "AA" in r else
                   "Adequate Safety" if r.startswith("A") else "Moderate Safety" if "BBB" in r else
                   "Speculative" if any(x in r for x in ["BB", "B", "C", "D"]) else "")
        lines = ["## Credit Rating — " + self._s(b.get("bond_name"), ""), "",
                 "| Field | Value |", "|-------|-------|",
                 "| **Rating** | **" + r + "** |",
                 "| **Agency** | " + self._s(b.get("credit_rating_agency")) + " |",
                 "| **Outlook** | " + self._s(b.get("rating_outlook")) + " |",
                 "| **Meaning** | " + meaning + " |"]
        if self.has_docs:
            doc_sec = self._extract_section("rating|crisil|icra|care|credit quality")
            if doc_sec:
                lines += ["", "### From Prospectus:", "", doc_sec[:500]]
        return "\n".join(lines)

    def _day_count(self):
        b = self.b
        dc = self._s(b.get("day_count_convention"), "Actual/Actual")
        fv = float(b.get("face_value") or 0)
        rate = float(b.get("coupon_rate") or 0)
        lines = ["## Day Count Convention\n\n**Used:** " + dc, "",
                 "| Convention | Divisor | Used In |", "|------------|---------|---------|",
                 "| Actual/Actual | 365 or 366 | Govt Bonds |",
                 "| Actual/365 | 365 | Indian Corp Bonds |",
                 "| Actual/360 | 360 | Money Market |",
                 "| 30/360 | 360 | US Corp Bonds |"]
        if fv and rate:
            year_days = 360 if "360" in dc else 365
            lines += ["", "### Accrued Interest Examples", "| Days | Formula | Result |", "|------|---------|--------|"]
            for days in [30, 90, 180, 365]:
                accrued = fv * rate / 100 * days / year_days
                lines.append("| " + str(days) + " | " + self._fmt(fv) + " x " + str(rate) + "% x " + str(days) + "/" + str(year_days) + " | **" + self._fmt(accrued) + "** |")
        return "\n".join(lines)

    def _duration(self):
        b = self.b
        tenor = float(b.get("tenor_years") or 0)
        rate = float(b.get("coupon_rate") or 0)
        mac = round(tenor * 0.85 if rate > 0 else tenor, 2)
        mod = round(mac / (1 + rate / 100 / 2), 2)
        return ("## Duration Analysis\n\n"
                "| Measure | Value |\n|---------|-------|\n"
                "| Tenor | " + str(tenor) + " years |\n"
                "| Macaulay Duration | ~" + str(mac) + " years |\n"
                "| Modified Duration | ~" + str(mod) + " |\n\n"
                "A 1% rate rise -> ~" + str(mod) + "% price fall.")

    def _face_value(self):
        b = self.b
        return ("## Face Value / Principal\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Face Value (per unit)** | **" + self._fmt(b.get("face_value")) + "** |\n"
                "| **Principal Amount** | " + self._fmt(b.get("principal_amount")) + " |\n"
                "| **Total Issue Size** | " + self._fmt(b.get("total_issue_size")) + " |\n"
                "| **Currency** | " + self._s(b.get("issue_currency"), "INR") + " |")

    def _issue_size(self):
        b = self.b
        fv = float(b.get("face_value") or 1)
        total = float(b.get("total_issue_size") or 0)
        units = int(total / fv) if fv else 0
        return ("## Issue Size\n\n"
                "| Field | Value |\n|-------|-------|\n"
                "| **Total Issue Size** | **" + self._fmt(total) + "** |\n"
                "| **Face Value/Unit** | " + self._fmt(b.get("face_value")) + " |\n"
                "| **Units** | " + "{:,}".format(units) + " |\n"
                "| **Currency** | " + self._s(b.get("issue_currency"), "INR") + " |")

    def _calculation(self, q):
        import re
        b = self.b
        fv = float(b.get("face_value") or 0)
        rate = float(b.get("coupon_rate") or 0)
        freq = self._s(b.get("coupon_frequency"), "Semi-Annual")
        dc = self._s(b.get("day_count_convention"), "Actual/Actual")
        m = re.search(r"(\d+)\s*days?", q.lower())
        days = int(m.group(1)) if m else 182
        year_days = 360 if "360" in dc else 365
        accrued = fv * rate / 100 * days / year_days if fv and rate else 0
        coupon = (fv * rate / 100) / self._ppY(freq) if fv and rate else 0
        return ("## Calculation\n\n"
                "**Bond:** " + self._s(b.get("bond_name"), "") + "\n"
                "**Face Value:** " + self._fmt(fv) + " | **Rate:** " + str(rate) + "% | **Convention:** " + dc + "\n\n"
                "**Accrued Interest for " + str(days) + " days:**\n"
                "= " + self._fmt(fv) + " x " + str(rate) + "% x " + str(days) + "/" + str(year_days) + "\n"
                "= **" + self._fmt(accrued) + "**\n\n"
                "**Coupon per " + freq + " payment:**\n"
                "= " + self._fmt(fv) + " x " + str(rate) + "% / " + str(self._ppY(freq)) + "\n"
                "= **" + self._fmt(coupon) + "**")

    def _general(self):
        b = self.b
        bond_name = self._s(b.get("bond_name"), "this bond")
        lines = ["## Bizaxl Bond AI — " + bond_name, "",
                 "| Bond | " + bond_name + " |",
                 "|------|" + "-" * (len(bond_name) + 2) + "|",
                 "| ISIN | " + self._s(b.get("isin"), "N/A") + " |",
                 "| Issuer | " + self._s(b.get("issuer_name"), "N/A") + " |",
                 "| Coupon | " + str(b.get("coupon_rate") or 0) + "% " + self._s(b.get("coupon_frequency"), "") + " |",
                 "| Maturity | " + self._s(b.get("maturity_date"), "N/A") + " |",
                 "| Rating | " + self._s(b.get("credit_rating"), "N/A") + " |", ""]
        if self.has_docs:
            lines += ["**Documents loaded:** " + ", ".join(self.doc_names), "I can answer questions from these documents.", ""]
        lines += ["**Ask me:**",
                  "- Coupon schedule / next payment",
                  "- Risk factors / covenants",
                  "- ESG classification / use of proceeds",
                  "- Yield to maturity / accrued interest",
                  "- Call/put options / maturity details",
                  "- Any question about the uploaded prospectus"]
        return "\n".join(lines)

    def _extract_section(self, keyword, max_chars=1500):
        if not self.doc_text:
            return ""
        import re
        lines = self.doc_text.split("\n")
        result = []
        for line in lines:
            if re.search(keyword, line, re.IGNORECASE) and len(line.strip()) > 10:
                result.append(line.strip())
        return "\n".join(result)[:max_chars].strip()

    def _search_docs(self, question):
        return self._answer_from_doc(question, question.lower())


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


# ─── GET BOND DOCUMENTS (was missing — caused 417 error) ──────────────────────
@frappe.whitelist(allow_guest=True)
def get_bond_documents(bond_name):
    """Get all uploaded documents for a bond."""
    try:
        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name},
            fields=["name", "document_name", "document_type", "document_date",
                    "processing_status", "file_attachment"],
            order_by="modified desc"
        )
        return docs or []
    except Exception as e:
        frappe.log_error(str(e), "get_bond_documents")
        return []


@frappe.whitelist(allow_guest=True)
def get_ai_chat_history(bond_name, session_id=None):
    """Get AI chat history for a bond."""
    try:
        filters = {"bond_name": bond_name}
        if session_id:
            filters["session_id"] = session_id
        chats = frappe.get_all(
            "Bond AI Chat",
            filters=filters,
            fields=["question", "answer", "asked_on", "session_id"],
            order_by="asked_on asc",
            limit=50
        )
        return chats or []
    except Exception as e:
        return []


# ─── MISSING FUNCTIONS (caused 417 errors) ────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def get_esg_bonds(esg_type=None):
    """Get all ESG classified bonds."""
    try:
        filters = [["esg_classification", "!=", "None"],
                   ["esg_classification", "!=", ""],
                   ["esg_classification", "is", "set"]]
        if esg_type:
            filters = [["esg_classification", "=", esg_type]]
        bonds = frappe.get_all(
            "Bond Master",
            filters=filters,
            fields=["name", "bond_name", "isin", "issuer_name", "issuer_type",
                    "bond_type", "esg_classification", "issue_currency",
                    "principal_amount", "total_issue_size", "credit_rating",
                    "credit_rating_agency", "maturity_date", "use_of_proceeds",
                    "coupon_rate", "coupon_frequency"],
            order_by="creation desc"
        )
        return bonds or []
    except Exception as e:
        frappe.log_error(str(e), "get_esg_bonds")
        return []


@frappe.whitelist(allow_guest=True)
def get_esg_reports(bond_name=None):
    """Get ESG reports for a bond."""
    try:
        filters = {"document_type": ["in", ["ESG Report", "Sustainability Report"]]}
        if bond_name:
            filters["bond_name"] = bond_name
        docs = frappe.get_all(
            "Bond Document",
            filters=filters,
            fields=["name", "bond_name", "document_name", "document_type",
                    "document_date", "processing_status", "file_attachment"],
            order_by="document_date desc"
        )
        return docs or []
    except Exception as e:
        return []


@frappe.whitelist(allow_guest=True)
def get_bond_documents(bond_name):
    """Get all uploaded documents for a bond."""
    try:
        if not bond_name:
            return []
        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": str(bond_name)},
            fields=["name", "document_name", "document_type", "document_date",
                    "processing_status", "file_attachment", "document_summary"],
            order_by="modified desc"
        )
        return docs or []
    except Exception as e:
        frappe.log_error(str(e), "get_bond_documents")
        return []


@frappe.whitelist(allow_guest=True)
def get_ai_chat_history(bond_name, session_id=None):
    """Get AI chat history for a bond."""
    try:
        filters = {"bond_name": str(bond_name)}
        if session_id:
            filters["session_id"] = session_id
        chats = frappe.get_all(
            "Bond AI Chat",
            filters=filters,
            fields=["question", "answer", "asked_on", "session_id", "sources_cited"],
            order_by="asked_on asc",
            limit=50
        )
        return chats or []
    except Exception as e:
        return []


@frappe.whitelist(allow_guest=True)
def ask_bond_ai(bond_name, question, session_id=None):
    """
    Bizaxl Built-in Bond AI. No external API key needed.
    Answers from uploaded document text first, then from DB data.
    """
    try:
        if not bond_name or not question:
            return {"answer": "Please select a bond and enter a question.", "session_id": "", "sources": [], "success": False}

        bond_name = str(bond_name)
        question = str(question)

        # Load bond details from DB
        bonds = frappe.get_all("Bond Master", filters={"name": bond_name}, fields=["*"], limit=1)
        bond = bonds[0] if bonds else {}

        # Load schedules
        coupons = frappe.get_all("Bond Coupon Schedule",
            filters={"bond_name": bond_name}, fields=["*"],
            order_by="coupon_number asc", limit=50)
        steps = frappe.get_all("Bond Step Schedule",
            filters={"bond_name": bond_name}, fields=["*"],
            order_by="period_from asc")
        amort = frappe.get_all("Bond Amortization Schedule",
            filters={"bond_name": bond_name}, fields=["*"],
            order_by="payment_number asc", limit=30)

        # Load PROCESSED documents (with extracted text)
        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name, "processing_status": "Ready"},
            fields=["document_name", "document_type", "extracted_text",
                    "document_summary", "key_terms_json"],
            order_by="modified desc",
            limit=5
        )

        # Run built-in AI engine
        engine = _BondEngine(bond, coupons, steps, amort, docs)
        answer = engine.answer(question)

        # Save chat history
        if not session_id:
            session_id = "SESSION-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        try:
            chat = frappe.get_doc({
                "doctype": "Bond AI Chat",
                "bond_name": bond_name,
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "model_used": "Bizaxl Bond AI v2",
                "tokens_used": 0,
                "asked_by": frappe.session.user or "Guest",
                "asked_on": datetime.datetime.now(),
                "sources_cited": ", ".join([str(d.get("document_name", "")) for d in docs])
            })
            chat.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [str(d.get("document_name", "")) for d in docs],
            "success": True
        }

    except Exception as e:
        frappe.log_error(str(e), "ask_bond_ai")
        return {
            "answer": "I encountered an error. Please try again. (" + str(e)[:100] + ")",
            "session_id": session_id or "",
            "sources": [],
            "success": False
        }


@frappe.whitelist(allow_guest=True)
def process_bond_document(bond_doc_name):
    """Process uploaded bond document — extract text and mark as Ready."""
    try:
        doc = frappe.get_doc("Bond Document", str(bond_doc_name))
        file_url = str(doc.file_attachment or "")
        extracted_text = ""

        if file_url:
            site_path = frappe.get_site_path()
            paths_to_try = [
                site_path + file_url,
                site_path + "/public" + file_url,
                site_path.replace("/sites/", "/") + file_url,
            ]
            for path in paths_to_try:
                try:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    # Try UTF-8 first, then latin-1
                    try:
                        extracted_text = raw.decode('utf-8', errors='replace')
                    except Exception:
                        extracted_text = raw.decode('latin-1', errors='replace')
                    if extracted_text.strip():
                        break
                except Exception:
                    continue

        # Clean up the text
        extracted_text = extracted_text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
        # Remove binary garbage (keep printable + common chars)
        import re
        extracted_text = re.sub(r'[^\x20-\x7E\n\t\u00A0-\uFFFF]', ' ', extracted_text)
        extracted_text = re.sub(r' {3,}', '  ', extracted_text)
        extracted_text = extracted_text.strip()

        chars = len(extracted_text)
        summary = extracted_text[:800] if extracted_text else "Document uploaded."

        doc.processing_status = "Ready"
        doc.extracted_text = extracted_text[:100000] if extracted_text else ""
        doc.document_summary = summary
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Document processed. " + str(chars) + " characters extracted.",
            "chars_extracted": chars
        }
    except Exception as e:
        frappe.log_error(str(e), "process_bond_document")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def extract_bond_from_file(file_url, document_name="Bond Document"):
    """Extract bond field values from uploaded prospectus using pattern matching."""
    import re as _re
    try:
        if not file_url:
            return {"status": "error", "message": "No file URL"}

        text = ""
        site_path = frappe.get_site_path()
        for path in [site_path + str(file_url), site_path + "/public" + str(file_url)]:
            try:
                with open(path, 'rb') as f:
                    raw = f.read()
                text = raw.decode('utf-8', errors='replace')
                if text.strip():
                    break
            except Exception:
                continue

        if not text or len(text.strip()) < 30:
            return {"status": "error", "message": "File empty or unreadable. Use a text-based PDF or .txt file."}

        ct = text.lower()
        fields = {}

        def find(pats):
            for p in pats:
                m = _re.search(p, text, _re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            return None

        def find_date(pats):
            import datetime as dt
            for p in pats:
                m = _re.search(p, text, _re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    for fmt in ["%d %B %Y", "%d-%m-%Y", "%d/%m/%Y",
                                "%B %d, %Y", "%d %b %Y", "%Y-%m-%d",
                                "%dst %B %Y", "%dnd %B %Y", "%drd %B %Y", "%dth %B %Y"]:
                        try:
                            cleaned = _re.sub(r'(st|nd|rd|th)', '', raw)
                            return dt.datetime.strptime(cleaned.strip(), fmt).strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    return raw
            return None

        def find_num(pats):
            for p in pats:
                m = _re.search(p, text, _re.IGNORECASE)
                if m:
                    n = m.group(1).replace(',', '').strip()
                    ctx = text[max(0, m.start()-30):m.end()+30].lower()
                    try:
                        val = float(n)
                        if 'crore' in ctx or ' cr' in ctx:
                            val *= 10000000
                        elif 'lakh' in ctx or 'lac' in ctx:
                            val *= 100000
                        return str(int(val))
                    except Exception:
                        return n
            return None

        # Bond name
        fields["bond_name"] = find([
            r'(?:security description|bond name|name of (?:the )?(?:bond|security|instrument))\s*[:\-]\s*([^\n]{5,80})',
            r'(?:series|tranche|issue)\s+(?:of\s+)?(?:non-?convertible\s+)?(?:debentures?|bonds?|notes?)\s*[:\-]?\s*([^\n]{5,60})',
        ]) or str(document_name).replace(".pdf","").replace(".txt","").replace("_PROSP","").replace("_"," ").strip()

        # ISIN
        fields["isin"] = find([r'\bISIN\b[\s:#]*([A-Z]{2}[A-Z0-9]{10})\b', r'\b(IN[A-Z0-9]{10})\b'])

        # Issuer
        fields["issuer_name"] = find([
            r'(?:issuer|company|borrower|obligor)\s*[:\-]\s*([A-Z][A-Za-z\s\.\,]+(?:Limited|Ltd\.?|Corporation|Corp\.?|LLP|Inc\.?|Bank|Finance|Infra|Energy|Power))',
            r'^([A-Z][A-Za-z\s\.]+(?:Limited|Ltd\.?|Corporation|Bank|Finance|Energy))',
        ])

        # Coupon rate
        cr = find([
            r'(?:coupon rate|rate of interest|interest rate)\s*[:\-]\s*([\d\.]+)\s*%',
            r'([\d\.]+)\s*%\s*(?:per annum|p\.?a\.?|fixed|coupon)',
        ])
        if cr:
            try:
                fields["coupon_rate"] = str(round(float(cr), 4))
            except Exception:
                fields["coupon_rate"] = cr

        # Coupon type
        if 'step-up' in ct or 'step up' in ct:
            fields["coupon_type"] = "Step-Up"
        elif 'floating' in ct or 'variable rate' in ct:
            fields["coupon_type"] = "Floating"
        elif 'zero coupon' in ct or 'zero-coupon' in ct:
            fields["coupon_type"] = "Zero Coupon"
        else:
            fields["coupon_type"] = "Fixed"

        # Coupon frequency
        if 'semi-annual' in ct or 'semi annual' in ct or 'half.yearly' in ct or 'half year' in ct:
            fields["coupon_frequency"] = "Semi-Annual"
        elif 'quarterly' in ct:
            fields["coupon_frequency"] = "Quarterly"
        elif 'monthly' in ct:
            fields["coupon_frequency"] = "Monthly"
        elif 'at maturity' in ct or 'on maturity' in ct or 'zero coupon' in ct:
            fields["coupon_frequency"] = "At Maturity"
        else:
            fields["coupon_frequency"] = "Annual"

        # Bond type
        if 'government' in ct or 'g-sec' in ct or 'gilt' in ct or 'sovereign' in ct:
            fields["bond_type"] = "Government Bond"
        elif 'zero coupon' in ct:
            fields["bond_type"] = "Zero Coupon"
        elif 'convertible' in ct and 'non-convertible' not in ct and 'non convertible' not in ct:
            fields["bond_type"] = "Convertible"
        elif 'amortiz' in ct:
            fields["bond_type"] = "Amortizing"
        else:
            fields["bond_type"] = "Corporate Bond"

        # Security
        if 'unsecured' in ct:
            fields["security_type"] = "Unsecured"
        elif 'secured' in ct:
            fields["security_type"] = "Secured"

        # Dates
        fields["issue_date"] = find_date([
            r'(?:issue date|date of issue|allotment date|deemed date of allotment)\s*[:\-]\s*([\d]+ ?(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ])
        fields["maturity_date"] = find_date([
            r'(?:maturity date|redemption date|date of redemption|due date)\s*[:\-]\s*([\d]+ ?(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ])
        fields["first_coupon_date"] = find_date([
            r'(?:first coupon date|first interest payment date)\s*[:\-]\s*([\d]+ ?(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ])

        # Tenor
        tenor = find([r'(?:tenor|period|term)\s*[:\-]\s*([\d]+(?:\.\d+)?)\s*(?:years?|yrs?)'])
        if tenor:
            fields["tenor_years"] = tenor

        # Face value
        fv = find_num([
            r'(?:face value|nominal value|par value)\s*[:\-]\s*(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
        ])
        if fv:
            fields["face_value"] = fv

        # Issue size
        sz = find_num([
            r'(?:issue size|total issue|aggregate amount|issue amount|total amount)\s*[:\-]\s*(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
            r'(?:aggregate principal amount|base issue)\s*[:\-]\s*(?:Rs\.?|INR|₹)?\s*([\d,\.]+)',
        ])
        if sz:
            fields["total_issue_size"] = sz
            if not fields.get("principal_amount"):
                fields["principal_amount"] = sz

        # Currency
        if 'usd' in ct or 'u.s. dollar' in ct:
            fields["issue_currency"] = "USD"
        elif 'eur' in ct or 'euro' in ct:
            fields["issue_currency"] = "EUR"
        elif 'gbp' in ct or 'sterling' in ct:
            fields["issue_currency"] = "GBP"
        else:
            fields["issue_currency"] = "INR"

        # Credit rating
        rm = _re.search(r'\b(AAA|AA\+|AA-|AA|A\+|A-|BBB\+|BBB-|BBB|BB\+|BB-|BB|B\+|B-|CCC|CC|C|D|Sovereign)(?:\s*\([A-Z]+\))?\b', text)
        if rm:
            fields["credit_rating"] = rm.group(1).strip()

        # Rating agency
        for agency, keywords in [("CRISIL", ["crisil"]), ("ICRA", ["icra"]),
                                  ("CARE", ["care ratings", "care "]), ("India Ratings", ["india ratings", "ind-ra"]),
                                  ("Moody's", ["moody"]), ("S&P", ["s&p", "standard & poor"]), ("Fitch", ["fitch"])]:
            if any(k in ct for k in keywords):
                fields["credit_rating_agency"] = agency
                break

        # Outlook
        for outlook in ["Stable", "Positive", "Negative", "Watch"]:
            if outlook.lower() in ct:
                fields["rating_outlook"] = outlook
                break

        # ESG
        for esg, kws in [("Green Bond", ["green bond"]), ("Blue Bond", ["blue bond"]),
                         ("Social Bond", ["social bond"]), ("Sustainability Bond", ["sustainability bond"]),
                         ("Climate Bond", ["climate bond"])]:
            if any(k in ct for k in kws):
                fields["esg_classification"] = esg
                break
        else:
            fields["esg_classification"] = "None"

        # Day count
        if 'actual/actual' in ct or 'act/act' in ct:
            fields["day_count_convention"] = "Actual/Actual"
        elif 'actual/360' in ct or 'act/360' in ct:
            fields["day_count_convention"] = "Actual/360"
        elif '30/360' in ct:
            fields["day_count_convention"] = "30/360"
        else:
            fields["day_count_convention"] = "Actual/365"

        # Exchange
        if 'nse' in ct and 'bse' in ct:
            fields["exchange_listing"] = "NSE+BSE"
        elif 'nse' in ct:
            fields["exchange_listing"] = "NSE"
        elif 'bse' in ct:
            fields["exchange_listing"] = "BSE"

        # Governing law
        if 'laws of india' in ct or 'indian law' in ct:
            fields["governing_law"] = "Indian Law"
        elif 'english law' in ct:
            fields["governing_law"] = "UK English Law"
        else:
            fields["governing_law"] = "Indian Law"

        # Use of proceeds
        uop = find([
            r'(?:use of (?:the )?proceeds|utilization of proceeds|objects? of the issue)\s*[:\-\n]\s*([^\n]{20,500})',
        ])
        if uop:
            fields["use_of_proceeds"] = uop[:500]

        # SEBI reg
        sebi = find([r'SEBI\s+(?:reg(?:istration)?\.?\s+(?:no|number)\.?)\s*[:\-#]?\s*([A-Z0-9/\-]{6,30})'])
        if sebi:
            fields["sebi_registration"] = sebi

        # Features
        fields["is_callable"] = 1 if ('call option' in ct or 'callable' in ct) else 0
        fields["is_puttable"] = 1 if 'put option' in ct or 'puttable' in ct else 0
        fields["is_convertible"] = 1 if ('convertible' in ct and 'non-convertible' not in ct and 'non convertible' not in ct) else 0
        fields["is_amortizing"] = 1 if 'amortiz' in ct else 0

        # Remove None/empty
        fields = {k: v for k, v in fields.items() if v is not None and v != ""}
        return {
            "status": "success",
            "bond_fields": fields,
            "message": "Extracted " + str(len(fields)) + " fields from prospectus."
        }

    except Exception as e:
        frappe.log_error(str(e), "extract_bond_from_file")
        return {"status": "error", "message": str(e)}


# ─── SAVE BOND (reliable backend save) ───────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def save_bond(bond_data):
    """Save a new bond to Bond Master. Returns the saved doc name."""
    try:
        if isinstance(bond_data, str):
            import json
            bond_data = json.loads(bond_data)

        bond_name = bond_data.get("bond_name", "").strip()
        if not bond_name:
            return {"status": "error", "message": "Bond name is required"}

        # Check if already exists
        existing = frappe.db.exists("Bond Master", {"bond_name": bond_name})
        if existing:
            return {"status": "error", "message": "Bond '" + bond_name + "' already exists"}

        # Build the doc - safely handle all fields
        doc = frappe.get_doc({
            "doctype": "Bond Master",
            "bond_name": bond_name,
        })

        # Map all fields safely
        field_map = {
            "isin": "isin",
            "issuer_name": "issuer_name",
            "issuer_type": "issuer_type",
            "bond_type": "bond_type",
            "issue_date": "issue_date",
            "maturity_date": "maturity_date",
            "first_coupon_date": "first_coupon_date",
            "tenor_years": "tenor_years",
            "principal_amount": "principal_amount",
            "face_value": "face_value",
            "total_issue_size": "total_issue_size",
            "issue_currency": "issue_currency",
            "coupon_type": "coupon_type",
            "coupon_rate": "coupon_rate",
            "coupon_frequency": "coupon_frequency",
            "credit_rating": "credit_rating",
            "credit_rating_agency": "credit_rating_agency",
            "rating_outlook": "rating_outlook",
            "esg_classification": "esg_classification",
            "day_count_convention": "day_count_convention",
            "governing_law": "governing_law",
            "exchange_listing": "exchange_listing",
            "security_type": "security_type",
            "use_of_proceeds": "use_of_proceeds",
            "sebi_registration": "sebi_registration",
            "is_callable": "is_callable",
            "call_date": "call_date",
            "call_price": "call_price",
            "is_puttable": "is_puttable",
            "put_date": "put_date",
            "put_price": "put_price",
            "is_convertible": "is_convertible",
            "is_amortizing": "is_amortizing",
            "remarks": "remarks",
        }

        numeric_fields = {"tenor_years", "principal_amount", "face_value",
                          "total_issue_size", "coupon_rate", "call_price",
                          "put_price", "outstanding_amount"}

        for key, field in field_map.items():
            val = bond_data.get(key)
            if val is not None and val != "" and val != "null":
                if field in numeric_fields:
                    try:
                        setattr(doc, field, float(val))
                    except (ValueError, TypeError):
                        pass
                else:
                    setattr(doc, field, val)

        # Set defaults
        if not doc.is_active:
            doc.is_active = 1
        if not doc.esg_classification:
            doc.esg_classification = "None"
        if not doc.issue_currency:
            doc.issue_currency = "INR"

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "name": doc.name,
            "bond_name": doc.bond_name,
            "message": "Bond saved successfully"
        }

    except Exception as e:
        frappe.log_error(str(e), "save_bond")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def save_client(client_data):
    """Save a new client to Bond Client."""
    try:
        if isinstance(client_data, str):
            import json
            client_data = json.loads(client_data)

        full_name = client_data.get("full_name", "").strip()
        if not full_name:
            return {"status": "error", "message": "Full name is required"}

        doc = frappe.get_doc({"doctype": "Bond Client", "full_name": full_name})

        for field in ["email", "phone", "client_type", "kyc_status",
                      "demat_account_number", "dp_name", "risk_profile",
                      "relationship_manager", "pan_number"]:
            val = client_data.get(field)
            if val is not None and val != "":
                setattr(doc, field, val)

        doc.is_active = 1
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "name": doc.name, "message": "Client saved"}
    except Exception as e:
        frappe.log_error(str(e), "save_client")
        return {"status": "error", "message": str(e)}
