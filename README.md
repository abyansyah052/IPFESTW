# Financial Scenario Testing Application

Aplikasi Streamlit untuk menguji berbagai skenario finansial proyek berdasarkan Production Sharing Contract (PSC) dengan CAPEX/OPEX analysis, CCUS enhancement, NPV/IRR calculation, dan scenario ranking system.

## Features

### Core Functionality
- **CAPEX Selection**: Pilih item dari kategori Production, Power, Transportation, dan Flaring
- **Auto-generate OPEX**: Sistem otomatis menghitung OPEX berdasarkan CAPEX yang dipilih
- **Financial Calculations**: Perhitungan lengkap dengan NPV, IRR, Payback Period, depreciation (DDB), PSC split, dan cash flow
- **Production Enhancement**: CCUS dengan EOR (+20%) dan EGR (+25%)
- **Export**: Export hasil ke Excel/CSV dengan multiple sheets

### Bulk Operations
- **Bulk Import**: Import 512 scenarios sekaligus dari Excel
- **Bulk Compare**: Bandingkan semua scenarios dengan scoring system otomatis
- **Advanced Ranking**: Multi-criteria scoring dengan weighted scoring
- **Leaderboard**: Top 100 scenarios berdasarkan overall score
- **Realistic IRR Filter**: Tab khusus untuk scenarios dengan IRR 15-30%

### Visualization
- **Interactive Charts**: NPV distribution, top/bottom performers, scatter plots
- **Comparison Views**: Detailed comparison dengan pagination dan sorting
- **Export Options**: Download comparison results dalam format CSV/Excel

## Tech Stack

- **Backend**: PostgreSQL (Supabase) + SQLAlchemy + Psycopg2
- **Frontend**: Streamlit + Plotly + Pandas
- **Calculations**: numpy-financial (NPV/IRR)
- **Database**: Supabase PostgreSQL (Transaction Pooler)
- **Deployment**: Streamlit Community Cloud
- **Performance**: Optimized batch queries (500x faster - 200s to 0.4s)

## Prerequisites

- Python 3.8+
- PostgreSQL database (local atau cloud seperti Neon.tech)
- pip atau conda untuk package management

## Installation

### 1. Clone Repository

```bash
cd ScenarioCalc
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

#### Option A: Local PostgreSQL

```bash
# Install PostgreSQL
# Create database
createdb scenario_calc

# Update .env file
DATABASE_URL=postgresql://username:password@localhost:5432/scenario_calc
```

#### Option B: Neon.tech (Free Cloud PostgreSQL)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy connection string
4. Update .env file

```
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

### 5. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your database URL
nano .env
```

### 6. Initialize Database

```bash
cd database
python init_db.py
```

Output harus menunjukkan:
```
Database tables created successfully
CAPEX Categories inserted
CAPEX Subcategories inserted
CAPEX Items inserted
OPEX Mappings inserted
Fiscal Terms inserted
Pricing Assumptions inserted
Production Enhancement rates inserted
Database initialization completed successfully!
```

## Running the Application

### Local Development

```bash
streamlit run app.py
```

Application akan buka di browser pada `http://localhost:8501`

**Database Connection:**
- Menggunakan Supabase Transaction Pooler
- Connection string di `.env` atau `secrets.toml` (untuk Streamlit Cloud)
- Format: `postgresql://user:password@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`

### Production Deployment

#### Streamlit Community Cloud

1. Push code ke GitHub repository
2. Login ke [share.streamlit.io](https://share.streamlit.io)
3. Deploy dari GitHub repo
4. Add secrets di Streamlit dashboard:
   ```toml
   DATABASE_URL = "postgresql://user:pass@host:port/db"
   ```

**Live App:** [https://ipfestw.streamlit.app](https://ipfestw.streamlit.app)

## Usage Guide

### 1. Create Scenario

1. Go to **"Create Scenario"**
2. Pilih CAPEX items dari sidebar:
   - **Production**: CCUS EGR, CCUS EOR, Supersonic Separator
   - **Power**: CCPP, FWT
   - **Transportation**: Pipeline atau Shipping (STS, OWS, VLGC)
   - **Flaring**: FGRS
3. Set quantity untuk setiap item
4. Input scenario name dan description
5. Click **"Create & Calculate Scenario"**
6. View hasil kalkulasi dengan NPV, IRR, Payback Period

### 2. Bulk Import Scenarios

1. Go to **"Bulk Import"**
2. Download Excel template (optional)
3. Prepare Excel file dengan columns:
   - Scenario Name, Description
   - CAPEX items dengan quantities
   - Production profile reference
4. Upload Excel file
5. System akan auto-import dan calculate semua scenarios
6. **Note**: 512 scenarios dapat di-import sekaligus

### 3. Manage Scenarios

1. Go to **"Manage Scenarios"**
2. View all scenarios dalam paginated table (20 per page)
3. Features:
   - Search/filter scenarios
   - Sort by name, date, metrics
   - View scenario details
   - Delete scenarios (with confirmation)
   - Export scenario list to CSV

### 4. Compare Scenarios

1. Go to **"Compare Scenarios"**
2. Select scenarios (options):
   - **Select All**: Compare all 513 scenarios
   - **Select Range**: Pilih range (e.g., 1-100)
   - **Manual Selection**: Pilih individual scenarios
3. Click **"Run Comparison"**
4. View hasil comparison:

   **Summary Statistics:**
   - Best NPV scenario
   - Best IRR scenario
   - Positive NPV count
   - Average Payback Period

   **Detailed Comparison** (2 tabs):
   - **Tab 1: All Scenarios**
     - Ranked by score (customizable sorting)
     - Pagination: 10 scenarios per page
     - Columns: Rank, Scenario, Score, NPV, IRR, Payback, Revenue, CAPEX, OPEX
   
   - **Tab 2: Realistic IRR (15-30%)**
     - Filtered scenarios dengan IRR antara 15-30%
     - Re-ranked within filtered set
     - Pagination: 20 scenarios per page
     - Export to CSV available

   **Visual Comparison** (3 tabs):
   - NPV Distribution histogram
   - Top/Bottom Performers bar charts
   - CAPEX vs NPV scatter plot

   **Leaderboard Top 100:**
   - Best 100 scenarios berdasarkan weighted score
   - Pagination: 10 per page
   - Export to CSV

### 5. Scenario Scoring System

**Weighted Scoring:**
- NPV: 30%
- Contractor Share: 25%
- IRR: 15% (capped at 100% untuk fairness)
- Payback Period: 10%
- CAPEX: 10%
- OPEX: 10%

**IRR Cap:** IRR di atas 100% di-cap untuk scoring agar scenarios dengan CAPEX sangat kecil tidak unfairly dominate ranking.

### 6. Export Results

**Compare Scenarios Export:**
- **CSV**: Download comparison table
- **Excel**: Full report dengan multiple sheets
  - Summary statistics
  - Detailed comparison
  - Annual cash flows
  - CAPEX/OPEX breakdown

**Leaderboard Export:**
- Download Top 100 scenarios dalam CSV format

**Realistic IRR Export:**
- Download all scenarios dengan IRR 15-30% dalam CSV format

## Financial Model

### Fiscal Terms
- **Contractor Pre-tax Split**: 67.23%
- **Government Pre-tax Split**: 32.77%
- **Contractor Tax Rate**: 40.5%
- **Discount Rate**: 13%

### Pricing
- **Oil Price**: $60/bbl
- **Gas Price**: $5.5/MMBTU
- **Gas Conversion**: 1027 MMSCF to MMBTU

### Production Enhancement (CCUS)
- **EOR**: +20% oil production
- **EGR**: +25% gas production

### Depreciation
- **Method**: Declining Balance (DDB)
- **Life**: 5 years
- **Factor**: 25% (0.25)
- **Salvage**: $0

### Calculations

**Revenue:**
```
R_t = (P_oil,t x $60) + (P_gas,MMBTU,t x $5.5)
```

**Cash Flow** (Excel-matching formula):
```
CF_t = Revenue_t - OPEX_t - CAPEX_t - Depreciation_t - ASR_t
```

**Operating Profit:**
```
OP_t = R_t - D_t - OPEX_t
```

**PSC Split:**
```
Contractor Pre-tax = OP_t x 0.6723
Contractor Tax = Contractor Pre-tax x 0.405
Contractor After-tax = Contractor Pre-tax - Tax
Government Pre-tax = OP_t x 0.3277
Government Total = Government Pre-tax + Tax
```

**NPV** (using CUMULATIVE cash flows to match Excel):
```
Cumulative_CF_t = Sum(i=1 to t) CF_i
NPV = Sum(t=1 to 12) Cumulative_CF_t / (1+0.13)^t
```
**Note**: NPV menggunakan cumulative CF (bukan annual CF) untuk match Excel formula

**IRR** (using CUMULATIVE cash flows):
```
IRR = rate where Sum(t=1 to 12) Cumulative_CF_t / (1+rate)^t = 0
```
**Note**: IRR menggunakan cumulative CF untuk match Excel =IRR() formula

**Payback Period** (FIXED - Dec 2024):
```
Payback = year_when_positive - (remaining_debt / annual_cf_that_year)
```
**Example**: If cumulative CF = -$28.8M at end of year 3, and year 4 CF = +$29.3M:
- Payback = 4 - (28.8 / 29.3) = 4 - 0.984 = 3.016 years

**ASR (Abandonment & Site Restoration):**
```
ASR = CAPEX_total x 0.05
```

## Project Structure

```
ScenarioCalc/
├── app.py                      # Main Streamlit app (1800+ lines)
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .gitignore
├── README.md
├── database/
│   ├── models.py              # SQLAlchemy models
│   ├── connection.py          # Database connection (Supabase pooler)
│   └── init_db.py            # Database initialization
├── engine/
│   ├── calculator.py          # Financial calculation engine (Excel-matching)
│   ├── opex_generator.py     # OPEX auto-generator
│   ├── comparator.py         # Scenario comparison & scoring
│   └── bulk_importer.py      # Bulk import from Excel
├── utils/
│   └── export.py             # Excel/CSV export functionality
└── exports/                   # Generated export files (gitignored)
```

## Database Stats

- **Total Scenarios**: 513 (512 imported + 1 manual test)
- **Calculation Results**: ~6,156 rows (513 scenarios x 12 years)
- **Database Size**: ~50MB
- **Query Performance**: 
  - Bulk compare all scenarios: **0.4 seconds** (optimized from 200s)
  - Single scenario calculation: <1 second

## Troubleshooting

### Database Connection Error
```bash
# Check DATABASE_URL in .env file
# For Supabase: Ensure using Transaction Pooler port (6543, not 5432)
# Test connection: 
psql "postgresql://user:pass@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
```

### Import Error
```bash
pip install --upgrade -r requirements.txt
```

### Streamlit Error
```bash
streamlit cache clear
```

### Payback Period Issues
```bash
# If payback periods seem incorrect, recalculate using fix script:
python _testing/fix_payback.py
```

### Performance Issues
- **Large comparison queries**: Use "Select Range" instead of "Select All"
- **Slow loading**: Check database connection latency
- **Memory**: Close unused browser tabs

## Development

### Add New CAPEX Item

1. Edit `database/init_db.py`
2. Add item to INSERT statements
3. Re-run: `python init_db.py`

### Modify Calculations

Edit `engine/calculator.py` - method `calculate_scenario()`
**Important**: NPV/IRR use cumulative CF to match Excel formula

### Change Fiscal Parameters

Update values in `FiscalTerms` table atau modify `init_db.py`

### Recalculate All Scenarios

```bash
# After formula changes, recalculate all scenarios
python -c "
from database.connection import get_session
from database.models import Scenario
from engine.calculator import FinancialCalculator

with get_session() as session:
    scenarios = session.query(Scenario).all()
    for s in scenarios:
        calc = FinancialCalculator(s, session)
        calc.calculate_scenario()
    session.commit()
"
```

### Fix Payback Periods Only

```bash
python _testing/fix_payback.py
```

## Database Schema

### Main Tables
- `capex_categories` - CAPEX categories (Production, Power, Transportation, Flaring)
- `capex_items` - CAPEX item details with unit costs
- `opex_mapping` - OPEX calculation rules (auto-generation)
- `scenarios` - User scenarios (513 total)
- `scenario_capex` - Selected CAPEX per scenario
- `scenario_opex` - Auto-generated OPEX
- `calculation_results` - Annual financial results (12 years x 513 scenarios)
- `scenario_metrics` - Summary metrics (NPV, IRR, Payback, totals)
- `fiscal_terms` - Fiscal parameters (PSC split, tax rate)
- `pricing_assumptions` - Price assumptions (oil/gas prices)
- `production_profiles` - Production data (oil/gas by year)
- `production_enhancement` - CCUS enhancement rates (EOR/EGR)

### Key Relationships
```
Scenario → ScenarioCapex → CapexItem
Scenario → ScenarioOpex (auto-generated)
Scenario → CalculationResult (12 rows per scenario)
Scenario → ScenarioMetrics (1 row - summary)
```

## Recent Updates & Bug Fixes

### December 21, 2024
1. **Realistic IRR Tab**: Added tab in Detailed Comparison untuk filter scenarios dengan IRR 15-30%
2. **Payback Period Bug Fix**: 
   - **Bug**: Formula salah menggunakan `year + fraction` instead of `year - fraction`
   - **Impact**: Payback periods sangat tidak akurat (contoh: 67 tahun seharusnya 3 tahun)
   - **Fix**: Corrected formula, recalculated 477 scenarios
   - **Examples**: 1798y→5y, 1092y→5y, 442y→5y, 67y→3y

### December 20, 2024
1. **IRR Scoring Cap**: IRR capped at 100% untuk scoring (prevent extreme values)
2. **Navigation Buttons Fix**: Fixed pagination buttons sync dengan selectbox
3. **Best NPV/IRR Display**: Show scenario names instead of IDs

### December 19, 2024
1. **Excel Formula Match**: NPV/IRR menggunakan cumulative CF untuk match Excel
2. **Bulk Import**: 512 scenarios imported successfully
3. **Performance Optimization**: Batch queries 500x faster (200s to 0.4s)

## Known Issues & Limitations

1. **IRR = NaN**: Beberapa scenarios memiliki IRR undefined (negative atau extreme values)
   - Cause: CAPEX sangat kecil ($25K) dengan revenue besar ($279M)
   - Solution: Filtered out dari Realistic IRR tab

2. **Streamlit Cloud Auto-Redeploy**: Sometimes requires manual reboot di dashboard
   - Workaround: Push empty commit untuk trigger rebuild

3. **Large Dataset Loading**: Initial load untuk 513 scenarios dapat memakan waktu 3-5 detik
   - Mitigation: Optimized queries, pagination implemented

## Contributing

Untuk development atau bug fixes:
1. Create branch baru: `git checkout -b feature/nama-feature`
2. Make changes
3. Test thoroughly (especially financial calculations)
4. Commit: `git commit -m "Description"`
5. Push: `git push origin feature/nama-feature`
6. Submit pull request

## Testing

```bash
# Run all tests
python -m pytest _testing/

# Test specific module
python _testing/test_calc.py

# Excel validation test
python _testing/test_excel_validation.py
```

## License

Internal use only - IPFEST Project

## Team

**SM5 UNIV - IPFEST 2024/2025**

## Support

Untuk pertanyaan atau issues:
- Create GitHub issue
- Contact development team
- Check troubleshooting section di atas

## Acknowledgments

- Streamlit Community untuk platform deployment
- Supabase untuk PostgreSQL database hosting
- NumPy Financial untuk NPV/IRR calculations
- Excel formula references untuk validation

---

**Version:** 2.0.0  
**Last Updated:** December 23, 2024  
**Database:** Supabase PostgreSQL  
**Live URL:** https://ipfestw.streamlit.app  
**Scenarios:** 513 total
