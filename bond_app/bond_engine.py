"""
Bizaxl Bond AI Engine
=====================
A fully self-contained bond analysis engine.
No external API, no API keys, no internet needed.
Analyzes bond data from the database and documents using Python.
"""

import re
import json
import datetime


class BondAIEngine:
    """
    Bizaxl's own bond intelligence engine.
    Analyzes bond data, performs calculations, and answers questions.
    """

    def __init__(self, bond_data, coupon_schedule=None, step_schedule=None,
                 amort_schedule=None, documents=None):
        self.bond = bond_data or {}
        self.coupons = coupon_schedule or []
        self.steps = step_schedule or []
        self.amort = amort_schedule or []
        self.documents = documents or []
        self.doc_text = " ".join([
            (d.get("extracted_text") or d.get("document_summary") or "")
            for d in self.documents
        ])[:80000]

    # ── QUESTION ROUTER ────────────────────────────────────────────────────────
    def answer(self, question):
        q = question.lower().strip()

        # Route to specific handlers
        if any(w in q for w in ["coupon schedule", "payment schedule", "all coupon", "coupon dates", "all payment"]):
            return self._answer_coupon_schedule()
        if any(w in q for w in ["next coupon", "next payment", "upcoming coupon", "when is next"]):
            return self._answer_next_coupon()
        if any(w in q for w in ["coupon rate", "interest rate", "what is the rate", "coupon %"]):
            return self._answer_coupon_rate()
        if any(w in q for w in ["ytm", "yield to maturity", "yield to call", "ytc"]):
            return self._answer_yield()
        if any(w in q for w in ["amortiz", "principal repay", "principal schedule"]):
            return self._answer_amortization()
        if any(w in q for w in ["step", "step-up", "step up", "step schedule"]):
            return self._answer_step_schedule()
        if any(w in q for w in ["risk", "risk factor", "credit risk", "default risk"]):
            return self._answer_risk_factors()
        if any(w in q for w in ["covenant", "restriction", "negative covenant", "affirmative"]):
            return self._answer_covenants()
        if any(w in q for w in ["esg", "green bond", "use of proceed", "sustainability", "climate", "social bond"]):
            return self._answer_esg()
        if any(w in q for w in ["call option", "callable", "call date", "call price", "call feature"]):
            return self._answer_call_option()
        if any(w in q for w in ["put option", "puttable", "put date", "put feature"]):
            return self._answer_put_option()
        if any(w in q for w in ["convert", "convertible", "conversion ratio", "conversion price"]):
            return self._answer_convertible()
        if any(w in q for w in ["maturity", "when does", "matures on", "maturity date", "redemption"]):
            return self._answer_maturity()
        if any(w in q for w in ["issuer", "who issued", "company", "issuer name"]):
            return self._answer_issuer()
        if any(w in q for w in ["isin", "cusip", "common code", "identifier"]):
            return self._answer_identifiers()
        if any(w in q for w in ["rating", "credit rating", "crisil", "icra", "care", "moody", "s&p", "fitch"]):
            return self._answer_rating()
        if any(w in q for w in ["day count", "actual/actual", "30/360", "accrued interest", "accrual"]):
            return self._answer_day_count()
        if any(w in q for w in ["calculate", "compute", "how much", "what is the amount"]):
            return self._answer_calculation(question)
        if any(w in q for w in ["duration", "modified duration", "macaulay"]):
            return self._answer_duration()
        if any(w in q for w in ["face value", "principal", "par value", "nominal"]):
            return self._answer_face_value()
        if any(w in q for w in ["issue size", "total issue", "outstanding", "amount issued"]):
            return self._answer_issue_size()
        if any(w in q for w in ["currency", "denomination", "inr", "usd", "eur"]):
            return self._answer_currency()
        if any(w in q for w in ["listing", "exchange", "nse", "bse", "listed"]):
            return self._answer_listing()
        if any(w in q for w in ["law", "governing", "jurisdiction", "legal"]):
            return self._answer_legal()
        if any(w in q for w in ["security", "secured", "unsecured", "collateral"]):
            return self._answer_security()
        if any(w in q for w in ["summary", "overview", "about this bond", "tell me about", "details", "what is this bond"]):
            return self._answer_summary()
        if any(w in q for w in ["document", "prospectus", "information memorandum", "uploaded"]):
            return self._answer_document_info()

        # Search in uploaded documents
        doc_answer = self._search_documents(question)
        if doc_answer:
            return doc_answer

        # General bond info fallback
        return self._answer_general(question)

    # ── SUMMARY ────────────────────────────────────────────────────────────────
    def _answer_summary(self):
        b = self.bond
        name = b.get("bond_name", "This bond")
        lines = [
            f"## {name} — Bond Summary",
            "",
            f"**Issuer:** {b.get('issuer_name', 'N/A')} ({b.get('issuer_type', '')})",
            f"**ISIN:** {b.get('isin', 'N/A')}",
            f"**Bond Type:** {b.get('bond_type', 'N/A')}",
            f"**Currency:** {b.get('issue_currency', 'INR')}",
            "",
            "### Coupon Structure",
            f"- **Coupon Type:** {b.get('coupon_type', 'N/A')}",
            f"- **Coupon Rate:** {b.get('coupon_rate', 0)}% per annum",
            f"- **Coupon Frequency:** {b.get('coupon_frequency', 'N/A')}",
            f"- **Day Count:** {b.get('day_count_convention', 'N/A')}",
            "",
            "### Key Dates",
            f"- **Issue Date:** {b.get('issue_date', 'N/A')}",
            f"- **Maturity Date:** {b.get('maturity_date', 'N/A')}",
            f"- **First Coupon Date:** {b.get('first_coupon_date', 'N/A')}",
            f"- **Tenor:** {b.get('tenor_years', 'N/A')} years",
            "",
            "### Amount",
            f"- **Face Value:** {self._fmt(b.get('face_value'))}",
            f"- **Total Issue Size:** {self._fmt(b.get('total_issue_size'))}",
            f"- **Outstanding:** {self._fmt(b.get('outstanding_amount'))}",
            "",
            "### Credit & Legal",
            f"- **Rating:** {b.get('credit_rating', 'N/A')} ({b.get('credit_rating_agency', 'N/A')}) — {b.get('rating_outlook', 'N/A')}",
            f"- **Security:** {b.get('security_type', 'N/A')}",
            f"- **Governing Law:** {b.get('governing_law', 'N/A')}",
            f"- **Exchange:** {b.get('exchange_listing', 'N/A')}",
        ]
        if b.get("esg_classification") and b.get("esg_classification") != "None":
            lines += ["", f"### ESG Classification", f"- **Type:** {b.get('esg_classification')}",
                      f"- **Use of Proceeds:** {b.get('use_of_proceeds', 'N/A')}"]
        if b.get("is_callable"):
            lines += ["", "### Call Option", f"- Call Date: {b.get('call_date','N/A')} | Price: {b.get('call_price','N/A')}"]
        if b.get("is_convertible"):
            lines += ["", "### Convertible", f"- Conversion Ratio: {b.get('conversion_ratio','N/A')} | Price: {b.get('conversion_price','N/A')}"]
        if self.coupons:
            lines += ["", f"**{len(self.coupons)} coupon payments** scheduled. Ask 'Show coupon schedule' for details."]
        return "\n".join(lines)

    # ── COUPON SCHEDULE ────────────────────────────────────────────────────────
    def _answer_coupon_schedule(self):
        b = self.bond
        if not self.coupons:
            rate = b.get("coupon_rate", 0)
            freq = b.get("coupon_frequency", "Semi-Annual")
            fv = b.get("face_value", 0)
            lines = [
                f"## Coupon Schedule — {b.get('bond_name','')}",
                "",
                f"**Rate:** {rate}% p.a. | **Frequency:** {freq}",
                f"**Face Value:** {self._fmt(fv)} | **Day Count:** {b.get('day_count_convention','Actual/Actual')}",
                "",
                "No individual coupon records are stored yet.",
                f"Expected coupon per unit = Face Value × Rate / Periods",
                f"= {self._fmt(fv)} × {rate}% / {self._periods_per_year(freq)}",
                f"= {self._fmt(self._coupon_amount(fv, rate, freq))} per coupon",
            ]
            return "\n".join(lines)

        today = datetime.date.today()
        lines = [
            f"## Coupon Schedule — {b.get('bond_name','')}",
            "",
            f"**Rate:** {b.get('coupon_rate',0)}% p.a. | **Frequency:** {b.get('coupon_frequency','')}",
            "",
            f"{'#':<4} {'Date':<14} {'Rate%':<8} {'Amt/Unit':>12} {'Total':>16} {'Status':<12}",
            "-" * 70,
        ]
        total_paid = 0
        total_pending = 0
        for c in self.coupons:
            num = str(c.get("coupon_number", "?"))
            date = str(c.get("coupon_date", "?"))
            rate = str(c.get("coupon_rate_applicable", 0)) + "%"
            amt = self._fmt(c.get("coupon_amount_per_unit", 0))
            total = self._fmt(c.get("total_coupon_amount", 0))
            status = c.get("status", "Upcoming")
            marker = " ← NEXT" if c.get("coupon_date") and str(c.get("coupon_date")) > str(today) and total_paid == (len([x for x in self.coupons if x.get("status") == "Paid"])) else ""
            lines.append(f"{num:<4} {date:<14} {rate:<8} {amt:>12} {total:>16} {status:<12}{marker}")
            if status == "Paid":
                total_paid += c.get("total_coupon_amount", 0)
            else:
                total_pending += c.get("total_coupon_amount", 0)

        lines += [
            "-" * 70,
            f"**Total Paid:** {self._fmt(total_paid)} | **Total Pending:** {self._fmt(total_pending)}",
        ]
        return "\n".join(lines)

    # ── NEXT COUPON ────────────────────────────────────────────────────────────
    def _answer_next_coupon(self):
        b = self.bond
        today = str(datetime.date.today())
        upcoming = [c for c in self.coupons if str(c.get("coupon_date", "")) > today and c.get("status") != "Paid"]
        if upcoming:
            c = upcoming[0]
            return (
                f"## Next Coupon Payment — {b.get('bond_name','')}\n\n"
                f"- **Coupon #{c.get('coupon_number','?')}**\n"
                f"- **Date:** {c.get('coupon_date','N/A')}\n"
                f"- **Rate:** {c.get('coupon_rate_applicable',0)}% p.a.\n"
                f"- **Amount per Unit:** {self._fmt(c.get('coupon_amount_per_unit',0))}\n"
                f"- **Total Payable:** {self._fmt(c.get('total_coupon_amount',0))}\n"
                f"- **Record Date:** {c.get('record_date','N/A')}\n"
                f"- **Status:** {c.get('status','Upcoming')}\n\n"
                f"*{len(upcoming)} upcoming coupon payments remaining.*"
            )
        # Calculate from bond data
        rate = b.get("coupon_rate", 0)
        fv = b.get("face_value", 0)
        freq = b.get("coupon_frequency", "Semi-Annual")
        amt = self._coupon_amount(fv, rate, freq)
        return (
            f"## Next Coupon — {b.get('bond_name','')}\n\n"
            f"No upcoming coupon records found in schedule.\n\n"
            f"**Estimated based on bond terms:**\n"
            f"- Coupon Rate: {rate}% p.a.\n"
            f"- Frequency: {freq}\n"
            f"- Face Value: {self._fmt(fv)}\n"
            f"- Expected Amount/Unit: {self._fmt(amt)}\n\n"
            f"Check with your settlement team for exact payment date."
        )

    # ── COUPON RATE ────────────────────────────────────────────────────────────
    def _answer_coupon_rate(self):
        b = self.bond
        lines = [
            f"## Coupon Rate — {b.get('bond_name','')}",
            "",
            f"- **Coupon Type:** {b.get('coupon_type', 'Fixed')}",
            f"- **Coupon Rate:** **{b.get('coupon_rate', 0)}% per annum**",
            f"- **Coupon Frequency:** {b.get('coupon_frequency', 'N/A')}",
            f"- **Day Count Convention:** {b.get('day_count_convention', 'Actual/Actual')}",
            f"- **Business Day Convention:** {b.get('business_day_convention', 'N/A')}",
        ]
        if b.get("coupon_type") in ("Floating", "Variable"):
            lines += [
                f"- **Benchmark Rate:** {b.get('benchmark_rate','N/A')}",
                f"- **Spread (bps):** {b.get('spread_bps', 0)}",
                f"- **Current All-in Rate:** {b.get('benchmark_rate','?')} + {b.get('spread_bps',0)}bps",
            ]
        fv = b.get("face_value", 0)
        rate = b.get("coupon_rate", 0)
        freq = b.get("coupon_frequency", "Semi-Annual")
        if fv and rate:
            amt = self._coupon_amount(fv, rate, freq)
            lines += [
                "",
                "### Coupon Calculation",
                f"Coupon per unit = Face Value × Annual Rate / Periods per Year",
                f"= {self._fmt(fv)} × {rate}% ÷ {self._periods_per_year(freq)}",
                f"= **{self._fmt(amt)} per coupon payment**",
            ]
        if self.steps:
            lines += ["", "### Step Schedule", "| Period | Rate | Type |", "|--------|------|------|"]
            for s in self.steps:
                lines.append(f"| {s.get('period_from','')} → {s.get('period_to','')} | {s.get('coupon_rate',0)}% | {s.get('rate_type','')} |")
        return "\n".join(lines)

    # ── YIELD ──────────────────────────────────────────────────────────────────
    def _answer_yield(self):
        b = self.bond
        rate = b.get("coupon_rate", 0)
        fv = b.get("face_value", 0)
        issue_date = b.get("issue_date")
        maturity = b.get("maturity_date")
        tenor = b.get("tenor_years", 0)
        freq = b.get("coupon_frequency", "Semi-Annual")
        coupon = self._coupon_amount(fv, rate, freq)
        periods = int((tenor or 0) * self._periods_per_year(freq))
        lines = [
            f"## Yield Analysis — {b.get('bond_name','')}",
            "",
            f"**Face Value:** {self._fmt(fv)} | **Coupon Rate:** {rate}% | **Maturity:** {maturity}",
            "",
            "### Yield to Maturity (YTM) Formula",
            "YTM approximation formula:",
            "```",
            "YTM ≈ [C + (FV - P) / n] / [(FV + P) / 2]",
            "```",
            "Where:",
            f"- C = Annual Coupon = {self._fmt(coupon * self._periods_per_year(freq))}",
            f"- FV = Face Value = {self._fmt(fv)}",
            f"- P = Current Price (assumed at par = {self._fmt(fv)})",
            f"- n = Years to Maturity = {tenor}",
            "",
        ]
        if fv and rate and tenor:
            ann_coupon = coupon * self._periods_per_year(freq)
            ytm_approx = (ann_coupon + (fv - fv) / (tenor or 1)) / ((fv + fv) / 2) * 100
            lines += [
                f"**At Par Price ({self._fmt(fv)}):**",
                f"YTM ≈ {ann_coupon:.2f} / {fv:.2f} × 100 = **{rate:.2f}%** (equals coupon rate when trading at par)",
                "",
                "### At Different Prices",
                "| Price | YTM (approx) |",
                "|-------|--------------|",
            ]
            for price_pct in [95, 97, 100, 103, 105]:
                price = fv * price_pct / 100
                ytm = ((ann_coupon + (fv - price) / (tenor or 1)) / ((fv + price) / 2)) * 100
                lines.append(f"| {price_pct}% = {self._fmt(price)} | {ytm:.2f}% |")
        lines += [
            "",
            f"*For exact YTM, enter the current market price.*",
        ]
        return "\n".join(lines)

    # ── AMORTIZATION ────────────────────────────────────────────────────────────
    def _answer_amortization(self):
        b = self.bond
        if not self.amort:
            return (
                f"## Amortization Schedule — {b.get('bond_name','')}\n\n"
                f"No amortization schedule is stored for this bond.\n\n"
                f"**Bond Type:** {b.get('bond_type','N/A')}\n"
                f"**Is Amortizing:** {'Yes' if b.get('is_amortizing') else 'No — Bullet bond (full principal at maturity)'}\n\n"
                + ("This is a **bullet bond** — the entire principal of "
                   + self._fmt(b.get("principal_amount", 0)) +
                   " is repaid on maturity date " + str(b.get("maturity_date","N/A")) + "."
                   if not b.get("is_amortizing") else
                   "Please add amortization schedule records in the Bond Amortization Schedule doctype.")
            )
        lines = [
            f"## Amortization Schedule — {b.get('bond_name','')}",
            "",
            f"{'#':<4} {'Date':<14} {'Opening':>14} {'Coupon':>12} {'Principal':>12} {'Total':>12} {'Closing':>14}",
            "-" * 85,
        ]
        for a in self.amort:
            lines.append(
                f"{str(a.get('payment_number','?')):<4} "
                f"{str(a.get('payment_date','?')):<14} "
                f"{self._fmt(a.get('opening_principal',0)):>14} "
                f"{self._fmt(a.get('coupon_payment',0)):>12} "
                f"{self._fmt(a.get('principal_payment',0)):>12} "
                f"{self._fmt(a.get('total_payment',0)):>12} "
                f"{self._fmt(a.get('closing_principal',0)):>14}"
            )
        return "\n".join(lines)

    # ── STEP SCHEDULE ────────────────────────────────────────────────────────
    def _answer_step_schedule(self):
        b = self.bond
        if not self.steps:
            return (
                f"## Step Schedule — {b.get('bond_name','')}\n\n"
                f"**Coupon Type:** {b.get('coupon_type','N/A')}\n\n"
                + ("No step schedule records found. This bond appears to have a fixed coupon of "
                   + str(b.get('coupon_rate', 0)) + "% p.a."
                   if b.get("coupon_type") != "Step-Up" else
                   "Please add step schedule records in Bond Step Schedule doctype.")
            )
        lines = [
            f"## Step-Up/Step-Down Coupon Schedule — {b.get('bond_name','')}",
            "",
            "| Period From | Period To | Rate | Type | Benchmark | Spread |",
            "|-------------|-----------|------|------|-----------|--------|",
        ]
        for s in self.steps:
            lines.append(
                f"| {s.get('period_from','')} | {s.get('period_to','')} | "
                f"**{s.get('coupon_rate',0)}%** | {s.get('rate_type','')} | "
                f"{s.get('benchmark','-')} | {s.get('spread_bps',0)}bps |"
            )
        return "\n".join(lines)

    # ── RISK FACTORS ──────────────────────────────────────────────────────────
    def _answer_risk_factors(self):
        b = self.bond
        doc_risks = self._extract_section("risk", 2000)
        lines = [
            f"## Risk Factors — {b.get('bond_name','')}",
            "",
            "### Bond-Level Risk Assessment",
            "",
        ]
        rating = b.get("credit_rating", "")
        if rating:
            risk_level = "Low" if "AAA" in rating or "Sovereign" in rating else \
                         "Moderate" if any(x in rating for x in ["AA", "A+"]) else \
                         "High" if any(x in rating for x in ["B", "BB", "C"]) else "Moderate"
            lines += [
                f"**1. Credit Risk** — {risk_level}",
                f"   - Rating: {rating} ({b.get('credit_rating_agency','')}) | Outlook: {b.get('rating_outlook','')}",
                f"   - Issuer: {b.get('issuer_name','')} ({b.get('issuer_type','')})",
            ]
        lines += [
            "",
            f"**2. Interest Rate Risk**",
            f"   - Coupon Type: {b.get('coupon_type','Fixed')}",
            f"   - Tenor: {b.get('tenor_years','?')} years — {'High duration risk' if (b.get('tenor_years') or 0) > 10 else 'Moderate duration risk' if (b.get('tenor_years') or 0) > 5 else 'Lower duration risk'}",
            f"   - Fixed coupons become less attractive if market rates rise" if b.get("coupon_type") == "Fixed" else f"   - Floating rate: benchmarked to {b.get('benchmark_rate','')} + {b.get('spread_bps',0)}bps",
            "",
            f"**3. Liquidity Risk**",
            f"   - Listed on: {b.get('exchange_listing','N/A')}",
            f"   - Security: {b.get('security_type','N/A')}",
            "",
            f"**4. Reinvestment Risk**",
            f"   - Coupon Frequency: {b.get('coupon_frequency','N/A')} — coupon payments need to be reinvested",
            "",
            f"**5. Call Risk**" if b.get("is_callable") else f"**5. Call Risk** — Not applicable (bond is not callable)",
        ]
        if b.get("is_callable"):
            lines.append(f"   - Callable on {b.get('call_date','?')} at {b.get('call_price','?')}")
        if doc_risks:
            lines += ["", "### From Prospectus:", "", doc_risks[:1500]]
        return "\n".join(lines)

    # ── COVENANTS ─────────────────────────────────────────────────────────────
    def _answer_covenants(self):
        b = self.bond
        doc_cov = self._extract_section("covenant", 2000)
        lines = [
            f"## Covenants & Restrictions — {b.get('bond_name','')}",
            "",
            "### Standard Bond Covenants (Typical for this bond type)",
            "",
            f"**Bond Type:** {b.get('bond_type','N/A')} | **Issuer:** {b.get('issuer_name','N/A')}",
            "",
            "**Negative Covenants (Restrictions on Issuer):**",
            "- Restriction on additional secured borrowings above agreed limits",
            "- Restriction on sale/disposal of core assets without bondholder consent",
            "- Dividend restrictions if financial ratios deteriorate",
            "- Restriction on mergers/acquisitions without disclosure",
            "",
            "**Affirmative Covenants (Obligations of Issuer):**",
            "- Maintain financial reporting (quarterly/annual)",
            "- Notify bondholders of material events",
            "- Maintain credit rating (rating trigger covenants)",
            f"- Maintain {'security/collateral' if b.get('security_type')=='Secured' else 'financial health ratios'}",
            "",
            "**Events of Default:**",
            "- Non-payment of coupon or principal on due date",
            "- Cross-default on other material debt",
            "- Insolvency/bankruptcy proceedings",
            "- Material adverse change",
        ]
        if b.get("is_callable"):
            lines += ["", "**Call Provisions:**",
                      f"- Issuer may redeem at {b.get('call_price','?')} on {b.get('call_date','?')}"]
        if b.get("is_puttable"):
            lines += ["", "**Put Provisions:**",
                      f"- Investor may sell back at {b.get('put_price','?')} on {b.get('put_date','?')}"]
        if doc_cov:
            lines += ["", "### From Prospectus:", "", doc_cov[:2000]]
        return "\n".join(lines)

    # ── ESG ────────────────────────────────────────────────────────────────────
    def _answer_esg(self):
        b = self.bond
        esg = b.get("esg_classification", "None")
        proceeds = b.get("use_of_proceeds", "")
        doc_esg = self._extract_section("esg|green|sustainability|climate|social", 2000)
        if esg == "None":
            return (
                f"## ESG Classification — {b.get('bond_name','')}\n\n"
                f"This bond is **not classified** as an ESG bond.\n\n"
                f"It is a standard {b.get('bond_type','corporate')} bond "
                f"issued by {b.get('issuer_name','N/A')}."
            )
        lines = [
            f"## ESG Classification — {b.get('bond_name','')}",
            "",
            f"### Classification: **{esg}**",
            "",
            f"| Parameter | Details |",
            f"|-----------|---------|",
            f"| ESG Type | **{esg}** |",
            f"| Issuer | {b.get('issuer_name','N/A')} |",
            f"| Issue Size | {self._fmt(b.get('total_issue_size'))} |",
            f"| Currency | {b.get('issue_currency','INR')} |",
            "",
        ]
        if proceeds:
            lines += ["### Use of Proceeds", "", proceeds, ""]
        esg_desc = {
            "Green Bond": "Finances projects with environmental benefits — renewable energy, clean transport, green buildings, sustainable water management",
            "Blue Bond": "Finances ocean and water-related sustainability projects — marine conservation, sustainable fisheries, water treatment",
            "Social Bond": "Finances projects with positive social outcomes — affordable housing, healthcare, education, employment",
            "Sustainability Bond": "Combines green and social objectives — comprehensive ESG impact",
            "Climate Bond": "Finances climate change mitigation and adaptation — net-zero transition projects",
            "Transition Bond": "Helps carbon-intensive sectors transition to cleaner operations",
            "Gender Equality Bond": "Advances women's economic empowerment and gender equity",
            "Pandemic Bond": "Finances healthcare infrastructure and pandemic preparedness",
        }
        if esg in esg_desc:
            lines += [f"### About {esg}s", "", esg_desc[esg], ""]
        lines += [
            "### ESG Reporting Requirements",
            "- Annual use of proceeds report",
            "- Impact reporting (CO2 reduction, beneficiaries, MW renewable etc.)",
            "- Third-party verification recommended",
        ]
        if doc_esg:
            lines += ["", "### From Prospectus:", "", doc_esg[:1500]]
        return "\n".join(lines)

    # ── CALL OPTION ────────────────────────────────────────────────────────────
    def _answer_call_option(self):
        b = self.bond
        if not b.get("is_callable"):
            return f"## Call Option — {b.get('bond_name','')}\n\nThis bond **does not have a call option**. It is a non-callable bond — the issuer cannot redeem it before maturity on {b.get('maturity_date','N/A')}."
        return (
            f"## Call Option — {b.get('bond_name','')}\n\n"
            f"This bond **IS CALLABLE**.\n\n"
            f"| Parameter | Details |\n|-----------|--------|\n"
            f"| Call Date | **{b.get('call_date','N/A')}** |\n"
            f"| Call Price | **{b.get('call_price','N/A')}** |\n"
            f"| Maturity Date | {b.get('maturity_date','N/A')} |\n\n"
            f"**What this means:**\n"
            f"- The issuer ({b.get('issuer_name','')}) can redeem this bond on {b.get('call_date','?')}\n"
            f"- If called, bondholders receive the call price of {b.get('call_price','?')}\n"
            f"- This protects the issuer if interest rates fall significantly\n"
            f"- Yield to Call (YTC) may differ from Yield to Maturity (YTM)"
        )

    # ── PUT OPTION ─────────────────────────────────────────────────────────────
    def _answer_put_option(self):
        b = self.bond
        if not b.get("is_puttable"):
            return f"## Put Option — {b.get('bond_name','')}\n\nThis bond **does not have a put option**."
        return (
            f"## Put Option — {b.get('bond_name','')}\n\n"
            f"This bond **IS PUTTABLE** — investors can sell back to the issuer.\n\n"
            f"| Parameter | Details |\n|-----------|--------|\n"
            f"| Put Date | **{b.get('put_date','N/A')}** |\n"
            f"| Put Price | **{b.get('put_price','N/A')}** |\n"
        )

    # ── CONVERTIBLE ────────────────────────────────────────────────────────────
    def _answer_convertible(self):
        b = self.bond
        if not b.get("is_convertible"):
            return f"## Convertible Feature — {b.get('bond_name','')}\n\nThis bond **is not convertible**. It is a straight bond with no equity conversion feature."
        return (
            f"## Convertible Bond — {b.get('bond_name','')}\n\n"
            f"This bond **IS CONVERTIBLE** into equity.\n\n"
            f"| Parameter | Details |\n|-----------|--------|\n"
            f"| Conversion Ratio | **{b.get('conversion_ratio','N/A')}** shares per bond |\n"
            f"| Conversion Price | **{b.get('conversion_price','N/A')}** |\n"
            f"| Convert Into | {b.get('conversion_shares','N/A')} |\n\n"
            f"**Conversion Value = Shares × Current Stock Price**"
        )

    # ── MATURITY ───────────────────────────────────────────────────────────────
    def _answer_maturity(self):
        b = self.bond
        maturity = b.get("maturity_date")
        today = datetime.date.today()
        lines = [
            f"## Maturity Details — {b.get('bond_name','')}",
            "",
            f"- **Maturity Date:** **{maturity or 'N/A'}**",
            f"- **Issue Date:** {b.get('issue_date','N/A')}",
            f"- **Tenor:** {b.get('tenor_years','N/A')} years",
        ]
        if maturity:
            try:
                mat_date = datetime.date.fromisoformat(str(maturity))
                days_left = (mat_date - today).days
                years_left = days_left / 365.25
                if days_left > 0:
                    lines += [
                        f"- **Days to Maturity:** {days_left:,} days ({years_left:.2f} years)",
                        f"- **Status:** Active",
                    ]
                    if days_left <= 30:
                        lines.append("⚠️ **MATURING WITHIN 30 DAYS — Alert your RM immediately!**")
                    elif days_left <= 90:
                        lines.append("⚠️ Maturing within 90 days — plan for reinvestment.")
                else:
                    lines.append(f"- **Status:** ✅ MATURED ({abs(days_left)} days ago)")
            except Exception:
                pass
        lines += [
            "",
            "### At Maturity",
            f"- Principal of {self._fmt(b.get('face_value',0))} per unit will be repaid",
            f"- Final coupon will also be paid",
            f"- Total redemption = Face Value + Final Coupon",
        ]
        return "\n".join(lines)

    # ── OTHER HANDLERS ─────────────────────────────────────────────────────────
    def _answer_issuer(self):
        b = self.bond
        return (
            f"## Issuer Details — {b.get('bond_name','')}\n\n"
            f"- **Issuer Name:** {b.get('issuer_name','N/A')}\n"
            f"- **Issuer Type:** {b.get('issuer_type','N/A')}\n"
            f"- **SEBI Registration:** {b.get('sebi_registration','N/A')}\n"
            f"- **Governing Law:** {b.get('governing_law','N/A')}\n"
            f"- **Payment Location:** {b.get('payment_location','N/A')}"
        )

    def _answer_identifiers(self):
        b = self.bond
        return (
            f"## Bond Identifiers — {b.get('bond_name','')}\n\n"
            f"- **ISIN:** `{b.get('isin','N/A')}`\n"
            f"- **CUSIP:** `{b.get('cusip','N/A')}`\n"
            f"- **Common Code:** `{b.get('common_code','N/A')}`\n"
            f"- **Exchange:** {b.get('exchange_listing','N/A')}"
        )

    def _answer_rating(self):
        b = self.bond
        return (
            f"## Credit Rating — {b.get('bond_name','')}\n\n"
            f"- **Rating:** **{b.get('credit_rating','N/A')}**\n"
            f"- **Agency:** {b.get('credit_rating_agency','N/A')}\n"
            f"- **Outlook:** {b.get('rating_outlook','N/A')}\n\n"
            f"### Rating Scale (CRISIL/ICRA/CARE)\n"
            f"| Rating | Meaning |\n|--------|----------|\n"
            f"| AAA | Highest safety |\n"
            f"| AA | High safety |\n"
            f"| A | Adequate safety |\n"
            f"| BBB | Moderate safety |\n"
            f"| BB and below | Speculative/High yield |"
        )

    def _answer_day_count(self):
        b = self.bond
        dc = b.get("day_count_convention", "Actual/Actual")
        fv = b.get("face_value", 0)
        rate = b.get("coupon_rate", 0)
        lines = [
            f"## Day Count Convention — {b.get('bond_name','')}",
            "",
            f"**Convention:** {dc}",
            "",
            "### How Each Convention Works",
            "",
            "| Convention | Formula | Example (₹10L, 8%, 182 days) |",
            "|------------|---------|-------------------------------|",
            "| Actual/Actual | Actual days / Actual year days | ₹10L × 8% × 182/365 = ₹39,890 |",
            "| Actual/360 | Actual days / 360 | ₹10L × 8% × 182/360 = ₹40,444 |",
            "| Actual/365 | Actual days / 365 | ₹10L × 8% × 182/365 = ₹39,890 |",
            "| 30/360 | 30-day months / 360 | ₹10L × 8% × 180/360 = ₹40,000 |",
        ]
        if fv and rate:
            days_examples = [(30, 30), (90, 91), (180, 182), (365, 365)]
            lines += ["", f"### Accrued Interest Calculation for This Bond ({dc})", ""]
            for approx_days, actual_days in days_examples:
                year_days = 360 if "360" in dc else 365
                calc_days = approx_days if "30/" in dc else actual_days
                accrued = fv * (rate / 100) * calc_days / year_days
                lines.append(f"- For {actual_days} days: {self._fmt(fv)} × {rate}% × {calc_days}/{year_days} = **{self._fmt(accrued)}**")
        return "\n".join(lines)

    def _answer_duration(self):
        b = self.bond
        tenor = b.get("tenor_years", 0)
        rate = b.get("coupon_rate", 0)
        freq = b.get("coupon_frequency", "Semi-Annual")
        return (
            f"## Duration Analysis — {b.get('bond_name','')}\n\n"
            f"- **Tenor:** {tenor} years\n"
            f"- **Coupon Rate:** {rate}%\n"
            f"- **Coupon Frequency:** {freq}\n\n"
            f"### Modified Duration (approximate)\n"
            f"For a {rate}% coupon bond with {tenor} years:\n"
            f"- Macaulay Duration ≈ {round((tenor * 0.85) if rate > 0 else tenor, 2)} years (lower than tenor due to interim coupons)\n"
            f"- Modified Duration ≈ Macaulay Duration / (1 + YTM/periods)\n"
            f"- A 1% rise in interest rates → approx {round((tenor * 0.85) if rate > 0 else tenor, 2):.1f}% drop in price\n\n"
            f"*For precise duration, provide current market yield.*"
        )

    def _answer_face_value(self):
        b = self.bond
        return (
            f"## Face Value / Principal — {b.get('bond_name','')}\n\n"
            f"- **Face Value (per unit):** {self._fmt(b.get('face_value'))}\n"
            f"- **Principal Amount:** {self._fmt(b.get('principal_amount'))}\n"
            f"- **Total Issue Size:** {self._fmt(b.get('total_issue_size'))}\n"
            f"- **Outstanding Amount:** {self._fmt(b.get('outstanding_amount'))}\n"
            f"- **Currency:** {b.get('issue_currency','INR')}"
        )

    def _answer_issue_size(self):
        b = self.bond
        return (
            f"## Issue Size — {b.get('bond_name','')}\n\n"
            f"- **Total Issue Size:** **{self._fmt(b.get('total_issue_size'))}**\n"
            f"- **Face Value per Unit:** {self._fmt(b.get('face_value'))}\n"
            f"- **Outstanding Amount:** {self._fmt(b.get('outstanding_amount'))}\n"
            f"- **Number of Units:** {int((b.get('total_issue_size') or 0) / (b.get('face_value') or 1)):,} units\n"
            f"- **Currency:** {b.get('issue_currency','INR')}"
        )

    def _answer_currency(self):
        b = self.bond
        return (
            f"## Currency & Denomination — {b.get('bond_name','')}\n\n"
            f"- **Issue Currency:** **{b.get('issue_currency','INR')}**\n"
            f"- **Market Type:** {b.get('domestic_foreign','Domestic')}\n"
            f"- **Face Value:** {self._fmt(b.get('face_value'))} {b.get('issue_currency','INR')}\n"
            f"- **Settlement:** {b.get('payment_location','N/A')}"
        )

    def _answer_listing(self):
        b = self.bond
        return (
            f"## Exchange Listing — {b.get('bond_name','')}\n\n"
            f"- **Listed On:** **{b.get('exchange_listing','N/A')}**\n"
            f"- **Market Type:** {b.get('domestic_foreign','N/A')}\n"
            f"- **SEBI Reg:** {b.get('sebi_registration','N/A')}"
        )

    def _answer_legal(self):
        b = self.bond
        return (
            f"## Legal & Regulatory — {b.get('bond_name','')}\n\n"
            f"- **Governing Law:** {b.get('governing_law','N/A')}\n"
            f"- **Business Day Convention:** {b.get('business_day_convention','N/A')}\n"
            f"- **Payment Location:** {b.get('payment_location','N/A')}\n"
            f"- **SEBI Registration:** {b.get('sebi_registration','N/A')}"
        )

    def _answer_security(self):
        b = self.bond
        return (
            f"## Security & Collateral — {b.get('bond_name','')}\n\n"
            f"- **Security Type:** **{b.get('security_type','N/A')}**\n"
            + (
                "This is an **UNSECURED** bond — bondholders are unsecured creditors. "
                "In case of default, they rank below secured creditors."
                if b.get("security_type") == "Unsecured" else
                "This is a **SECURED** bond — backed by specific assets of the issuer."
            )
        )

    def _answer_document_info(self):
        if not self.documents:
            return "No documents have been uploaded for this bond yet. Upload a prospectus using the panel on the right."
        lines = ["## Uploaded Documents\n"]
        for d in self.documents:
            lines.append(f"- **{d.get('document_name','')}** ({d.get('document_type','')}) — {d.get('processing_status','')}")
            if d.get("document_summary"):
                lines.append(f"  Summary: {d.get('document_summary','')[:200]}...")
        return "\n".join(lines)

    def _answer_calculation(self, question):
        b = self.bond
        q = question.lower()
        fv = b.get("face_value", 0)
        rate = b.get("coupon_rate", 0)
        freq = b.get("coupon_frequency", "Semi-Annual")
        # Try to find days in question
        days_match = re.search(r'(\d+)\s*days?', q)
        days = int(days_match.group(1)) if days_match else 182
        dc = b.get("day_count_convention", "Actual/Actual")
        year_days = 360 if "360" in dc else 365
        calc_days = round(days / (365 / 30) * 30) if "30/" in dc else days
        accrued = (fv or 0) * (rate / 100) * calc_days / year_days
        coupon_per_period = self._coupon_amount(fv, rate, freq)
        return (
            f"## Calculation — {b.get('bond_name','')}\n\n"
            f"**Day Count Convention:** {dc}\n"
            f"**Face Value:** {self._fmt(fv)}\n"
            f"**Annual Rate:** {rate}%\n\n"
            f"### Accrued Interest for {days} days:\n"
            f"= {self._fmt(fv)} × {rate}% × {calc_days}/{year_days}\n"
            f"= **{self._fmt(accrued)}**\n\n"
            f"### Coupon per {freq} Payment:\n"
            f"= {self._fmt(fv)} × {rate}% ÷ {self._periods_per_year(freq)}\n"
            f"= **{self._fmt(coupon_per_period)}**"
        )

    def _answer_general(self, question):
        b = self.bond
        return (
            f"## Bizaxl Bond AI — {b.get('bond_name','Bond Analysis')}\n\n"
            f"I can answer questions about this bond. Here's what I know:\n\n"
            f"- **Bond:** {b.get('bond_name','N/A')}\n"
            f"- **ISIN:** {b.get('isin','N/A')}\n"
            f"- **Issuer:** {b.get('issuer_name','N/A')}\n"
            f"- **Coupon:** {b.get('coupon_rate',0)}% {b.get('coupon_type','')} {b.get('coupon_frequency','')}\n"
            f"- **Maturity:** {b.get('maturity_date','N/A')}\n"
            f"- **Rating:** {b.get('credit_rating','N/A')} ({b.get('credit_rating_agency','')})\n\n"
            f"**Try asking:**\n"
            f"- What is the coupon rate?\n"
            f"- Show coupon schedule\n"
            f"- When is the next payment?\n"
            f"- What are the risk factors?\n"
            f"- Explain covenants\n"
            f"- Calculate accrued interest for 90 days\n"
            f"- What is the ESG classification?\n"
            f"- Show yield to maturity\n"
            f"- What are the call option terms?"
        )

    def _search_documents(self, question):
        if not self.doc_text:
            return None
        q_words = set(question.lower().split())
        q_words -= {"what", "is", "the", "a", "an", "of", "in", "for", "and", "or", "this", "bond"}
        if not q_words:
            return None
        sentences = re.split(r'[.!?\n]', self.doc_text)
        scored = []
        for sent in sentences:
            s_low = sent.lower()
            score = sum(1 for w in q_words if w in s_low)
            if score > 0:
                scored.append((score, sent.strip()))
        scored.sort(reverse=True)
        top = [s[1] for s in scored[:5] if len(s[1]) > 20]
        if top:
            return f"## From Uploaded Documents\n\n" + "\n\n".join(top)
        return None

    def _extract_section(self, keyword, max_chars):
        if not self.doc_text:
            return ""
        pattern = re.compile(
            rf'(?i)(?:^|\n)([^\n]*(?:{keyword})[^\n]*(?:\n(?![A-Z\d])[^\n]*)*)',
            re.MULTILINE
        )
        matches = pattern.findall(self.doc_text)
        result = " ".join(matches)[:max_chars]
        return result.strip()

    # ── HELPERS ────────────────────────────────────────────────────────────────
    def _fmt(self, n):
        if n is None or n == "":
            return "N/A"
        try:
            n = float(n)
        except Exception:
            return str(n)
        if n >= 10000000:
            return f"₹{n/10000000:.2f}Cr"
        if n >= 100000:
            return f"₹{n/100000:.1f}L"
        return f"₹{n:,.0f}"

    def _periods_per_year(self, freq):
        return {"Annual": 1, "Semi-Annual": 2, "Quarterly": 4, "Monthly": 12,
                "At Maturity": 1, "Zero": 1}.get(freq, 2)

    def _coupon_amount(self, fv, rate, freq):
        if not fv or not rate:
            return 0
        return (float(fv) * float(rate) / 100) / self._periods_per_year(freq)
