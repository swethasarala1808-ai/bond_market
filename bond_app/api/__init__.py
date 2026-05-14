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


# ─── AI BOND ASSISTANT ─────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def process_bond_document(bond_doc_name):
    try:
        import requests
        settings = _get_settings()
        api_key = settings.claude_api_key or ""

        doc = frappe.get_doc("Bond Document", bond_doc_name)
        doc.processing_status = "Processing"
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        extracted = doc.extracted_text or ""
        if not extracted and doc.file_attachment:
            try:
                file_doc = frappe.get_all("File", filters={"file_url": doc.file_attachment}, fields=["name", "file_url"])
                if file_doc:
                    file_path = frappe.get_site_path() + file_doc[0].file_url
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    try:
                        extracted = content.decode('utf-8', errors='ignore')
                    except Exception:
                        extracted = str(content)
            except Exception as fe:
                extracted = f"File extraction attempted: {str(fe)}"

        if extracted or doc.document_url:
            prompt = f"""Analyze this bond document and extract ALL key information in structured format.

Document: {doc.document_name} ({doc.document_type})
Bond: {doc.bond_name}

Text/Content:
{extracted[:40000] if extracted else "Document URL provided: " + str(doc.document_url)}

Extract and provide:
1. BOND SUMMARY (2-3 paragraphs)
2. KEY TERMS JSON with: issuer, isin, issue_date, maturity_date, coupon_rate, coupon_type, coupon_frequency, principal_amount, currency, credit_rating, day_count_convention, governing_law, call_option, put_option, conversion_terms
3. COUPON SCHEDULE summary
4. RISK FACTORS (top 5)
5. COVENANTS (key ones)
6. USE OF PROCEEDS
7. ESG DETAILS (if applicable)

Format response as valid JSON only with keys: summary, key_terms, coupon_summary, risk_factors, covenants, use_of_proceeds, esg_details"""

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=120
            )
            result = response.json()
            ai_output = result.get("content", [{}])[0].get("text", "")

            try:
                clean = ai_output
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                parsed = json.loads(clean)
                doc.document_summary = parsed.get("summary", "")
                doc.key_terms_json = json.dumps(parsed.get("key_terms", {}), indent=2)
                doc.covenants_extracted = 1
                doc.risk_factors_extracted = 1
                if parsed.get("esg_details"):
                    doc.esg_details_extracted = 1
            except Exception:
                doc.document_summary = ai_output[:2000]
                doc.key_terms_json = "{}"

        doc.extracted_text = extracted[:100000] if extracted else ""
        doc.processing_status = "Ready"
        doc.processed_on = datetime.datetime.now()
        doc.coupon_details_extracted = 1
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Document processed successfully"}
    except Exception as e:
        frappe.log_error(str(e), "process_bond_document")
        try:
            doc.processing_status = "Failed"
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def ask_bond_ai(bond_name, question, session_id=None):
    try:
        import requests
        settings = _get_settings()
        api_key = settings.claude_api_key or ""

        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name, "processing_status": "Ready"},
            fields=["extracted_text", "key_terms_json", "document_summary", "document_name", "document_type"],
            order_by="document_date desc"
        )

        if not docs:
            return {
                "answer": "No processed documents found for this bond. Please upload and process the bond prospectus first.",
                "sources": [],
                "session_id": session_id or ""
            }

        context_parts = []
        for doc in docs[:3]:
            if doc.get("extracted_text"):
                context_parts.append(
                    f"[{doc['document_type']} — {doc['document_name']}]\n{doc['extracted_text'][:15000]}"
                )
            elif doc.get("document_summary"):
                context_parts.append(
                    f"[Summary — {doc['document_name']}]\n{doc['document_summary']}"
                )
        context = "\n\n---\n\n".join(context_parts)

        bond = frappe.get_all(
            "Bond Master",
            filters={"name": bond_name},
            fields=[
                "bond_name", "isin", "issuer_name", "coupon_rate", "coupon_type",
                "coupon_frequency", "maturity_date", "issue_date", "principal_amount",
                "issue_currency", "credit_rating", "esg_classification", "bond_type",
                "day_count_convention", "face_value", "coupon_type"
            ]
        )
        bond_meta = json.dumps(bond[0] if bond else {}, default=str)

        system_prompt = f"""You are an expert Bond Analyst AI assistant for Bizaxl Securities.
You have deep knowledge of fixed income markets, bond structures, coupon calculations,
ESG bond frameworks, SEBI regulations, and bond documentation.

You are answering questions about a SPECIFIC BOND. Use ONLY the provided bond documents
and metadata to answer. Be precise, cite specific sections/pages when possible.
If information is not in the documents, say so clearly.

Bond Metadata: {bond_meta}

Bond Documents Context:
{context}

Answer in clear, professional language. For calculations, show the formula used.
For coupon calculations use the day count convention specified in the bond terms.
Format answers clearly with sections when needed."""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": settings.ai_model or "claude-sonnet-4-20250514",
                "max_tokens": int(settings.max_tokens_per_query or 2000),
                "system": system_prompt,
                "messages": [{"role": "user", "content": question}]
            },
            timeout=60
        )

        data = response.json()
        answer = data.get("content", [{}])[0].get("text", "Unable to process your question.")
        tokens = data.get("usage", {}).get("output_tokens", 0)

        if not session_id:
            session_id = f"SESSION-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        chat = frappe.get_doc({
            "doctype": "Bond AI Chat",
            "bond_name": bond_name,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "model_used": settings.ai_model or "claude-sonnet-4-20250514",
            "tokens_used": tokens,
            "asked_by": frappe.session.user,
            "asked_on": datetime.datetime.now()
        })
        chat.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [d["document_name"] for d in docs]
        }
    except Exception as e:
        frappe.log_error(str(e), "ask_bond_ai")
        return {"answer": f"Error processing question: {str(e)}", "sources": [], "session_id": session_id or ""}


@frappe.whitelist(allow_guest=True)
def get_ai_chat_history(bond_name, session_id=None):
    try:
        filters = {"bond_name": bond_name}
        if session_id:
            filters["session_id"] = session_id
        return frappe.get_all(
            "Bond AI Chat",
            filters=filters,
            fields=["question", "answer", "session_id", "asked_on", "model_used", "tokens_used", "feedback"],
            order_by="asked_on asc",
            limit=50
        )
    except Exception as e:
        frappe.log_error(str(e), "get_ai_chat_history")
        return []


@frappe.whitelist(allow_guest=True)
def get_bond_documents(bond_name):
    try:
        return frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name},
            fields=["name", "document_name", "document_type", "document_date", "processing_status", "total_pages", "document_summary"],
            order_by="document_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_bond_documents")
        return []


@frappe.whitelist(allow_guest=True)
def get_esg_bonds():
    try:
        return frappe.get_all(
            "Bond Master",
            filters={"esg_classification": ["!=", "None"]},
            fields=["name", "bond_name", "isin", "issuer_name", "esg_classification", "use_of_proceeds", "issue_currency", "principal_amount", "credit_rating"],
            order_by="creation desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_esg_bonds")
        return []


@frappe.whitelist(allow_guest=True)
def get_esg_reports():
    try:
        return frappe.get_all(
            "Bond ESG Report",
            fields=["*"],
            order_by="report_date desc"
        )
    except Exception as e:
        frappe.log_error(str(e), "get_esg_reports")
        return []


@frappe.whitelist(allow_guest=True)
def ask_bond_ai_v2(bond_name, question, session_id=None):
    """Improved ask_bond_ai with better error handling and api key check."""
    try:
        import requests
        settings = _get_settings()
        api_key = settings.claude_api_key or ""

        # Clear API key check
        if not api_key or len(api_key.strip()) < 20:
            return {
                "answer": "⚠️ Claude API Key not configured. Please go to **Settings** → enter your Claude API Key (starts with `sk-ant-...`) and click Save. Then come back here to ask questions.",
                "sources": [],
                "session_id": session_id or ""
            }

        # Get documents - try both bond_name and name filters
        docs = frappe.get_all(
            "Bond Document",
            filters={"processing_status": "Ready"},
            fields=["extracted_text", "key_terms_json", "document_summary", "document_name", "document_type", "bond_name"],
            order_by="modified desc",
            limit=10
        )
        # Filter by bond_name flexibly
        bond_docs = [d for d in docs if d.get("bond_name") == bond_name or d.get("bond_name") in bond_name or bond_name in (d.get("bond_name") or "")]
        if not bond_docs and docs:
            bond_docs = docs[:3]  # fallback to latest docs

        if not bond_docs:
            return {
                "answer": "📄 No processed documents found. Please upload the bond prospectus/document using the panel on the right, then click **Process with AI**. Once processed, I can answer any question about this bond.",
                "sources": [],
                "session_id": session_id or ""
            }

        # Build context
        context_parts = []
        for doc in bond_docs[:3]:
            text = doc.get("extracted_text") or doc.get("document_summary") or ""
            if text:
                context_parts.append(f"[{doc.get('document_type','Document')} — {doc.get('document_name','Unknown')}]\n{text[:18000]}")
        context = "\n\n---\n\n".join(context_parts)

        # Get bond metadata
        bond_list = frappe.get_all(
            "Bond Master",
            filters=[["name", "like", f"%{bond_name}%"]],
            fields=["bond_name", "isin", "issuer_name", "coupon_rate", "coupon_type",
                    "coupon_frequency", "maturity_date", "issue_date", "principal_amount",
                    "issue_currency", "credit_rating", "esg_classification", "bond_type",
                    "day_count_convention", "face_value", "governing_law"],
            limit=1
        )
        if not bond_list:
            bond_list = frappe.get_all("Bond Master", fields=["bond_name", "isin", "issuer_name"], limit=1)
        bond_meta = json.dumps(bond_list[0] if bond_list else {}, default=str)

        system_prompt = f"""You are an expert Bond Analyst AI for Bizaxl Securities with deep knowledge of:
- Fixed income markets, bond pricing, yield calculations
- Coupon structures (fixed, floating, step-up, zero coupon)
- Day count conventions (Actual/Actual, 30/360, Actual/365)
- ESG bond frameworks (Green, Social, Sustainability, Climate)
- SEBI regulations and Indian bond markets
- Bond documentation (prospectus, information memorandum, term sheets)

You are analyzing a SPECIFIC BOND. Answer ONLY from the provided documents.
Be precise, professional, and show calculations when asked.

Bond Details: {bond_meta}

Document Context:
{context}

Rules:
- Show formulas for all calculations
- Cite document sections when possible
- If data not in documents, say so clearly
- For coupon calculations, use the bond's day count convention"""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key.strip(),
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": settings.ai_model or "claude-sonnet-4-20250514",
                "max_tokens": int(settings.max_tokens_per_query or 2000),
                "system": system_prompt,
                "messages": [{"role": "user", "content": question}]
            },
            timeout=90
        )

        data = resp.json()

        # Handle API errors explicitly
        if resp.status_code != 200:
            err_type = data.get("error", {}).get("type", "unknown")
            err_msg = data.get("error", {}).get("message", "Unknown error")
            if err_type == "authentication_error":
                return {"answer": f"❌ Invalid Claude API Key. Please check your API key in Settings. It should start with `sk-ant-api03-...`\n\nError: {err_msg}", "sources": [], "session_id": session_id or ""}
            return {"answer": f"❌ Claude API Error ({resp.status_code}): {err_msg}", "sources": [], "session_id": session_id or ""}

        content_blocks = data.get("content", [])
        answer = ""
        for block in content_blocks:
            if block.get("type") == "text":
                answer += block.get("text", "")

        if not answer:
            answer = "I received an empty response. Please try again."

        tokens = data.get("usage", {}).get("output_tokens", 0)

        if not session_id:
            session_id = f"SESSION-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            chat = frappe.get_doc({
                "doctype": "Bond AI Chat",
                "bond_name": bond_name,
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "model_used": settings.ai_model or "claude-sonnet-4-20250514",
                "tokens_used": tokens,
                "asked_by": frappe.session.user,
                "asked_on": datetime.datetime.now()
            })
            chat.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": [d.get("document_name", "") for d in bond_docs]
        }

    except Exception as e:
        frappe.log_error(str(e), "ask_bond_ai_v2")
        return {
            "answer": f"❌ Error: {str(e)}\n\nPlease check:\n1. Claude API Key is set in Settings\n2. Internet connection is available\n3. The bond document has been processed",
            "sources": [],
            "session_id": session_id or ""
        }


@frappe.whitelist(allow_guest=True)
def extract_bond_from_document(file_url=None, file_content=None, document_name=None):
    """
    Upload a bond document (prospectus/term sheet) and AI auto-extracts
    all bond fields to pre-fill the Add Bond form.
    Returns a dict with all bond fields ready to populate the form.
    """
    try:
        import requests
        settings = _get_settings()
        api_key = settings.claude_api_key or ""

        if not api_key or len(api_key.strip()) < 20:
            return {
                "status": "error",
                "message": "Claude API Key not configured. Please set it in Settings first."
            }

        # Read file content
        extracted_text = ""
        if file_url:
            try:
                file_docs = frappe.get_all("File", filters={"file_url": file_url}, fields=["name", "file_url"])
                if file_docs:
                    file_path = frappe.get_site_path() + file_url
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    try:
                        extracted_text = content.decode('utf-8', errors='ignore')
                    except Exception:
                        extracted_text = str(content)
            except Exception as fe:
                extracted_text = f"Could not read file: {str(fe)}"

        if not extracted_text:
            return {"status": "error", "message": "Could not read the uploaded file. Please try a text-based PDF or .txt file."}

        # Build extraction prompt
        prompt = f"""You are a bond document parser. Extract ALL bond details from this document.

Document: {document_name or 'Bond Document'}

Content:
{extracted_text[:45000]}

Extract and return ONLY a valid JSON object with these exact keys (use null if not found):
{{
  "bond_name": "Full bond name",
  "isin": "12-character ISIN code",
  "cusip": "CUSIP if available",
  "issuer_name": "Name of the bond issuer",
  "issuer_type": "Corporate|Central Government|State Government|Municipal|Financial Institution|NBFC|PSU",
  "issue_date": "YYYY-MM-DD",
  "maturity_date": "YYYY-MM-DD",
  "tenor_years": 10,
  "principal_amount": 1000000,
  "face_value": 1000,
  "issue_currency": "INR|USD|EUR|GBP",
  "total_issue_size": 5000000000,
  "coupon_type": "Fixed|Floating|Zero Coupon|Step-Up|Step-Down|Variable|Index Linked",
  "coupon_rate": 8.5,
  "benchmark_rate": "SOFR|LIBOR|EURIBOR|MIBOR|NA",
  "spread_bps": 0,
  "coupon_frequency": "Annual|Semi-Annual|Quarterly|Monthly|At Maturity|Zero",
  "first_coupon_date": "YYYY-MM-DD",
  "day_count_convention": "Actual/Actual|Actual/360|Actual/365|30/360|30/365",
  "business_day_convention": "Following|Modified Following|Preceding",
  "governing_law": "Indian Law|UK English Law|New York Law|German Law|French Law|Other",
  "exchange_listing": "NSE|BSE|NSE+BSE|Luxembourg|Dublin|Singapore|OTC|Unlisted",
  "credit_rating": "AAA|AA+|AA|AA-|A+|A|BBB+|BBB|BB+|BB|B|sovereign",
  "credit_rating_agency": "CRISIL|ICRA|CARE|India Ratings|S&P|Moody's|Fitch",
  "rating_outlook": "Stable|Positive|Negative|Watch",
  "bond_type": "Corporate Bond|Government Bond|Zero Coupon|Convertible|Exchangeable|Amortizing|Inflation Indexed|Junk/High Yield|Callable|Puttable|Perpetual",
  "security_type": "Secured|Unsecured",
  "domestic_foreign": "Domestic|Foreign|Eurobond|Global|International",
  "esg_classification": "None|Green Bond|Blue Bond|Social Bond|Sustainability Bond|Gender Equality Bond|Climate Bond|Pandemic Bond|Transition Bond",
  "use_of_proceeds": "Description of use of proceeds",
  "is_callable": 0,
  "call_date": "YYYY-MM-DD or null",
  "call_price": null,
  "is_puttable": 0,
  "put_date": null,
  "put_price": null,
  "is_convertible": 0,
  "is_amortizing": 0,
  "sebi_registration": "SEBI reg number if any",
  "payment_location": "Mumbai|London|New York",
  "remarks": "Any important notes about this bond"
}}

Return ONLY the JSON, no other text."""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key.strip(),
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=120
        )

        if resp.status_code != 200:
            err = resp.json().get("error", {}).get("message", "API error")
            return {"status": "error", "message": f"Claude API error: {err}"}

        data = resp.json()
        ai_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                ai_text += block.get("text", "")

        # Parse JSON from response
        try:
            clean = ai_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            bond_fields = json.loads(clean)
        except Exception as pe:
            return {"status": "error", "message": f"Could not parse AI response: {str(pe)}", "raw": ai_text[:500]}

        return {
            "status": "success",
            "bond_fields": bond_fields,
            "message": f"Successfully extracted bond details from {document_name or 'document'}"
        }

    except Exception as e:
        frappe.log_error(str(e), "extract_bond_from_document")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def save_ai_chat(bond_name, session_id, question, answer):
    """Save AI chat history to Bond AI Chat doctype."""
    try:
        chat = frappe.get_doc({
            "doctype": "Bond AI Chat",
            "bond_name": bond_name,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "model_used": "claude-sonnet-4-20250514",
            "asked_by": frappe.session.user,
            "asked_on": datetime.datetime.now()
        })
        chat.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(str(e), "save_ai_chat")
        return {"status": "error"}


# ─── BUILT-IN BOND AI (NO USER API KEY NEEDED) ───────────────────────────────
# This endpoint acts as a proxy — the app calls Anthropic on behalf of the user.
# Users never need to configure any API key.

def _call_claude(system_prompt, user_message, max_tokens=2000):
    """Internal helper to call Claude API. App provides its own access."""
    import requests as _req
    import os

    # Try multiple sources for the API key (app-level, not user-level)
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY") or
        os.environ.get("CLAUDE_API_KEY") or
        frappe.conf.get("anthropic_api_key") or
        ""
    )

    # If no env key, try the Settings (user may have put it there)
    if not api_key:
        try:
            s = frappe.get_single("Bond Settings")
            api_key = s.claude_api_key or ""
        except Exception:
            pass

    if not api_key:
        return {
            "success": False,
            "answer": "🔧 The Bond AI needs to be configured by the administrator.\n\nPlease ask your system admin to set the `ANTHROPIC_API_KEY` environment variable on the server, or enter it once in Bond Settings.",
            "error": "no_key"
        }

    try:
        resp = _req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key.strip(),
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=90
        )
        data = resp.json()

        if resp.status_code == 200:
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            return {"success": True, "answer": text, "tokens": data.get("usage", {}).get("output_tokens", 0)}
        else:
            err = data.get("error", {}).get("message", f"HTTP {resp.status_code}")
            return {"success": False, "answer": f"AI Error: {err}", "error": err}
    except Exception as e:
        return {"success": False, "answer": f"Connection error: {str(e)}", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def bond_ai_chat(bond_name, question, session_id=None):
    """
    Built-in Bond AI — no user API key needed.
    Loads bond data + documents from DB, calls Claude, returns answer.
    """
    try:
        # ── Load bond data from DB ──────────────────────────────────────────
        bond_info = ""
        coupon_info = ""
        doc_context = ""
        sources = []

        # Bond master details
        bonds = frappe.get_all(
            "Bond Master",
            filters=[["name", "=", bond_name]],
            fields=["*"],
            limit=1
        )
        if bonds:
            b = bonds[0]
            bond_info = f"""BOND DETAILS:
Name: {b.get('bond_name', '')}
ISIN: {b.get('isin', 'N/A')}
Issuer: {b.get('issuer_name', 'N/A')} ({b.get('issuer_type', '')})
Bond Type: {b.get('bond_type', 'N/A')}
Coupon Type: {b.get('coupon_type', 'N/A')}
Coupon Rate: {b.get('coupon_rate', 0)}% p.a.
Benchmark Rate: {b.get('benchmark_rate', 'NA')}
Spread (bps): {b.get('spread_bps', 0)}
Coupon Frequency: {b.get('coupon_frequency', 'N/A')}
First Coupon Date: {b.get('first_coupon_date', 'N/A')}
Penultimate Date: {b.get('penultimate_date', 'N/A')}
Issue Date: {b.get('issue_date', 'N/A')}
Maturity Date: {b.get('maturity_date', 'N/A')}
Tenor: {b.get('tenor_years', 'N/A')} years
Face Value: {b.get('face_value', 'N/A')}
Principal Amount: {b.get('principal_amount', 'N/A')}
Total Issue Size: {b.get('total_issue_size', 'N/A')}
Outstanding Amount: {b.get('outstanding_amount', 'N/A')}
Currency: {b.get('issue_currency', 'INR')}
Credit Rating: {b.get('credit_rating', 'N/A')} ({b.get('credit_rating_agency', 'N/A')}) — {b.get('rating_outlook', 'N/A')}
Day Count Convention: {b.get('day_count_convention', 'N/A')}
Business Day Convention: {b.get('business_day_convention', 'N/A')}
Exchange Listing: {b.get('exchange_listing', 'N/A')}
Governing Law: {b.get('governing_law', 'N/A')}
Security Type: {b.get('security_type', 'N/A')}
Domestic/Foreign: {b.get('domestic_foreign', 'N/A')}
ESG Classification: {b.get('esg_classification', 'None')}
Use of Proceeds: {b.get('use_of_proceeds', 'N/A')}
Is Callable: {'Yes — Call Date: ' + str(b.get('call_date','')) + ' Price: ' + str(b.get('call_price','')) if b.get('is_callable') else 'No'}
Is Puttable: {'Yes — Put Date: ' + str(b.get('put_date','')) + ' Price: ' + str(b.get('put_price','')) if b.get('is_puttable') else 'No'}
Is Convertible: {'Yes — Ratio: ' + str(b.get('conversion_ratio','')) + ' Price: ' + str(b.get('conversion_price','')) if b.get('is_convertible') else 'No'}
Is Amortizing: {'Yes' if b.get('is_amortizing') else 'No'}
Payment Location: {b.get('payment_location', 'N/A')}
SEBI Registration: {b.get('sebi_registration', 'N/A')}
Remarks: {b.get('remarks', '')}"""

        # Coupon schedule
        coupons = frappe.get_all(
            "Bond Coupon Schedule",
            filters={"bond_name": bond_name},
            fields=["*"],
            order_by="coupon_number asc",
            limit=40
        )
        if coupons:
            coupon_info = "\nCOUPON SCHEDULE:\n"
            for c in coupons:
                coupon_info += (
                    f"{c.get('coupon_number','?')}. "
                    f"Date: {c.get('coupon_date','?')} | "
                    f"Rate: {c.get('coupon_rate_applicable',0)}% | "
                    f"Amount/Unit: {c.get('coupon_amount_per_unit',0)} | "
                    f"Total: {c.get('total_coupon_amount',0)} | "
                    f"Days: {c.get('day_count_days','')} | "
                    f"Status: {c.get('status','Upcoming')}\n"
                )

        # Amortization schedule
        amort = frappe.get_all(
            "Bond Amortization Schedule",
            filters={"bond_name": bond_name},
            fields=["*"],
            order_by="payment_number asc",
            limit=30
        )
        if amort:
            coupon_info += "\nAMORTIZATION SCHEDULE:\n"
            for a in amort:
                coupon_info += (
                    f"{a.get('payment_number','?')}. "
                    f"Date: {a.get('payment_date','?')} | "
                    f"Opening: {a.get('opening_principal',0)} | "
                    f"Coupon: {a.get('coupon_payment',0)} | "
                    f"Principal: {a.get('principal_payment',0)} | "
                    f"Closing: {a.get('closing_principal',0)}\n"
                )

        # Step schedule (for step-up/step-down bonds)
        steps = frappe.get_all(
            "Bond Step Schedule",
            filters={"bond_name": bond_name},
            fields=["*"],
            order_by="period_from asc"
        )
        if steps:
            coupon_info += "\nSTEP SCHEDULE:\n"
            for s in steps:
                coupon_info += (
                    f"Period: {s.get('period_from','')} to {s.get('period_to','')} | "
                    f"Rate: {s.get('coupon_rate',0)}% | "
                    f"Type: {s.get('rate_type','')} | "
                    f"Benchmark: {s.get('benchmark','')} | "
                    f"Spread: {s.get('spread_bps',0)}bps\n"
                )

        # Uploaded documents (processed)
        docs = frappe.get_all(
            "Bond Document",
            filters={"bond_name": bond_name, "processing_status": "Ready"},
            fields=["document_name", "document_type", "document_summary", "key_terms_json", "extracted_text"],
            order_by="modified desc",
            limit=3
        )
        for doc in docs:
            sources.append(doc.get("document_name", ""))
            text = doc.get("extracted_text") or doc.get("document_summary") or ""
            if text:
                doc_context += f"\n[{doc.get('document_type','Document')}: {doc.get('document_name','')}]\n{text[:12000]}\n"
            if doc.get("key_terms_json"):
                try:
                    kt = json.loads(doc["key_terms_json"])
                    doc_context += f"Key Terms: {json.dumps(kt, indent=2)[:2000]}\n"
                except Exception:
                    pass

        # ── Build system prompt ─────────────────────────────────────────────
        system_prompt = f"""You are the Bizaxl Bond AI — a built-in expert bond analyst for the Bizaxl Securities bond management platform.

You have deep expertise in:
- Fixed income markets and bond pricing
- Coupon calculations (fixed, floating, step-up, zero coupon, amortizing)
- Day count conventions (Actual/Actual, 30/360, Actual/365, Actual/360)
- Yield to maturity, yield to call, duration, convexity
- ESG bond frameworks (Green, Blue, Social, Sustainability, Climate)
- SEBI regulations and Indian bond markets
- Bond documentation (prospectus, IM, term sheets, covenants)

You are answering questions about this SPECIFIC BOND. Use ONLY the data below.
Show all formulas and step-by-step calculations when asked.
Be professional, precise, and helpful.

{bond_info}
{coupon_info}
{doc_context if doc_context else ''}"""

        # ── Call Claude ─────────────────────────────────────────────────────
        result = _call_claude(system_prompt, question, max_tokens=2000)

        # ── Save to chat history ────────────────────────────────────────────
        if not session_id:
            session_id = f"SESSION-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        if result.get("success"):
            try:
                chat = frappe.get_doc({
                    "doctype": "Bond AI Chat",
                    "bond_name": bond_name,
                    "session_id": session_id,
                    "question": question,
                    "answer": result["answer"],
                    "model_used": "claude-sonnet-4-20250514",
                    "tokens_used": result.get("tokens", 0),
                    "asked_by": frappe.session.user,
                    "asked_on": datetime.datetime.now(),
                    "sources_cited": ", ".join(sources)
                })
                chat.insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                pass

        return {
            "answer": result.get("answer", "Unable to process"),
            "session_id": session_id,
            "sources": sources,
            "success": result.get("success", False)
        }

    except Exception as e:
        frappe.log_error(str(e), "bond_ai_chat")
        return {
            "answer": f"Error: {str(e)}",
            "session_id": session_id or "",
            "sources": [],
            "success": False
        }


@frappe.whitelist(allow_guest=True)
def bond_ai_extract(file_url, document_name="Bond Document"):
    """
    Built-in document extraction — reads uploaded file and extracts all bond fields.
    No user API key needed.
    """
    try:
        extracted_text = ""
        if file_url:
            try:
                file_path = frappe.get_site_path() + file_url
                with open(file_path, 'rb') as f:
                    content = f.read()
                extracted_text = content.decode('utf-8', errors='ignore')
            except Exception as fe:
                return {"status": "error", "message": f"Cannot read file: {str(fe)}"}

        if not extracted_text:
            return {"status": "error", "message": "File is empty or unreadable. Please use a text-based PDF or .txt file."}

        prompt = f"""Extract ALL bond details from this document. Return ONLY valid JSON.

Document: {document_name}
Content:
{extracted_text[:45000]}

Return this exact JSON structure (null for missing fields):
{{
  "bond_name": "Full official bond name",
  "isin": "12-char ISIN code",
  "issuer_name": "Issuer name",
  "issuer_type": "Corporate|Central Government|State Government|Municipal|Financial Institution|NBFC|PSU",
  "issue_date": "YYYY-MM-DD",
  "maturity_date": "YYYY-MM-DD",
  "tenor_years": 10,
  "principal_amount": 1000000,
  "face_value": 1000,
  "issue_currency": "INR",
  "total_issue_size": 5000000000,
  "coupon_type": "Fixed|Floating|Zero Coupon|Step-Up|Step-Down|Variable",
  "coupon_rate": 8.5,
  "coupon_frequency": "Annual|Semi-Annual|Quarterly|Monthly|At Maturity",
  "first_coupon_date": "YYYY-MM-DD",
  "credit_rating": "AAA",
  "credit_rating_agency": "CRISIL|ICRA|CARE|India Ratings|S&P|Moody's|Fitch",
  "rating_outlook": "Stable|Positive|Negative|Watch",
  "bond_type": "Corporate Bond|Government Bond|Zero Coupon|Convertible|Amortizing|Callable|Puttable",
  "security_type": "Secured|Unsecured",
  "esg_classification": "None|Green Bond|Blue Bond|Social Bond|Sustainability Bond|Climate Bond",
  "day_count_convention": "Actual/Actual|Actual/360|Actual/365|30/360",
  "governing_law": "Indian Law|UK English Law|New York Law",
  "exchange_listing": "NSE|BSE|NSE+BSE|OTC|Unlisted",
  "use_of_proceeds": "Description of use",
  "is_callable": 0,
  "call_date": null,
  "call_price": null,
  "is_puttable": 0,
  "is_convertible": 0,
  "is_amortizing": 0,
  "sebi_registration": null,
  "remarks": "Key notes"
}}"""

        result = _call_claude(
            "You are a bond document parser. Extract bond data and return only valid JSON.",
            prompt,
            max_tokens=3000
        )

        if not result.get("success"):
            return {"status": "error", "message": result.get("answer", "AI extraction failed")}

        ai_text = result["answer"].strip()
        if "```json" in ai_text:
            ai_text = ai_text.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_text:
            ai_text = ai_text.split("```")[1].split("```")[0].strip()

        try:
            bond_fields = json.loads(ai_text)
            return {"status": "success", "bond_fields": bond_fields, "message": f"Extracted from {document_name}"}
        except Exception as pe:
            return {"status": "error", "message": f"Could not parse response: {str(pe)}", "raw": ai_text[:300]}

    except Exception as e:
        frappe.log_error(str(e), "bond_ai_extract")
        return {"status": "error", "message": str(e)}
