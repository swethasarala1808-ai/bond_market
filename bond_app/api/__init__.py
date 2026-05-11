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
