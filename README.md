# Bond Market & Fixed Income Management Platform

A complete **Bond Market & Fixed Income Management** app built on Frappe Framework.

## Features

### Core Bond Management
- **Bond Master** — Full bond lifecycle with ISIN, CUSIP, coupon structure, day count conventions, business day conventions
- **Bond Types** — Corporate, Government (Central/State/Municipal), Zero Coupon, Convertible, Exchangeable, Amortizing, Step-Up/Down, Callable, Puttable, Perpetual
- **Coupon Types** — Fixed, Floating (benchmark + spread), Index Linked, Inflation Linked, Step-Up/Down, Variable, Zero
- **ESG Bonds** — Green, Blue, Social, Sustainability, Gender Equality, Climate, Pandemic, Transition bonds

### Client & Portfolio Management
- Bond Client KYC management (Individual, HUF, Corporate, FII, FPI, NRI)
- Real-time portfolio holdings with P&L, accrued interest, YTM
- Bond transactions (Buy/Sell/Transfer/Redemption)
- Client watchlist with price/coupon alerts

### Coupon & Settlement Operations
- Automated coupon schedule generation
- Coupon payment tracking with TDS management
- Settlement workflow (T+0, T+1, T+2)
- Contract notes with GST calculation
- Invoicing and client ledger

### 🤖 AI Bond Assistant (Star Feature)
- Upload bond prospectus (200–2000 pages PDF/Word/Text)
- Claude AI reads and extracts key terms, risk factors, covenants, ESG details
- Ask any question about the specific bond — AI answers from document context
- Quick question shortcuts for common queries
- Session-based chat history

### WhatsApp Alerts
- Coupon payment reminders (3 days before)
- Coupon credited notifications
- Monthly portfolio statements
- Bond maturity alerts (30 days before)
- Contract note delivery

## Installation

```bash
# Clone into frappe-bench
cd ~/frappe-bench/apps
git clone https://github.com/swethasarala1808-ai/bond_market.git bond_app

# Install
cd ~/frappe-bench
./env/bin/pip install -e apps/bond_app
bench --site beauty.localhost install-app bond_app
bench --site beauty.localhost migrate
bench --site beauty.localhost execute bond_app.install.after_install
```

## URLs
- Customer Portal: `/bond`
- Owner Dashboard: `/bond-dashboard`

## Configuration
1. Go to `/bond-dashboard` → Settings
2. Enter your **Claude API Key** (`sk-ant-...`) — required for AI Bond Assistant
3. Set company details, WhatsApp number, SEBI registration

## DocTypes (20 total)
Bond Master, Bond Coupon Schedule, Bond Step Schedule, Bond Amortization Schedule,
Bond Issuer, Bond ESG Report, Bond Client, Bond Holding, Bond Transaction,
Bond Watchlist, Bond Coupon Payment, Bond Coupon Receipt, Bond Settlement,
Bond Contract Note, Bond Invoice, Bond Ledger, Bond Document, Bond AI Chat,
Bond Settings, Bond Relationship Manager

## Design System
- Dashboard: Dark theme (`#030e1f` bg, `#14F1B1` mint, `#114EFF` blue)
- Customer Portal: Light theme (white bg, navy text, mint CTAs)
- Typography: DM Sans (Google Fonts)
- Same sidebar layout as pet-dashboard / stock-dashboard (Bizaxl design system)

## License
MIT
