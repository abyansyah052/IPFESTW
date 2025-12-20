# Financial Scenario Testing Application

Aplikasi Streamlit untuk menguji berbagai skenario finansial proyek berdasarkan Production Sharing Contract (PSC) dengan CAPEX/OPEX analysis, CCUS enhancement, dan NPV calculation.

## 🎯 Features

- **CAPEX Selection**: Pilih item dari kategori Production, Power, Transportation, dan Flaring
- **Auto-generate OPEX**: Sistem otomatis menghitung OPEX berdasarkan CAPEX yang dipilih
- **Financial Calculations**: Perhitungan lengkap dengan NPV, depreciation (DDB), PSC split, dan cash flow
- **Production Enhancement**: CCUS dengan EOR (+20%) dan EGR (+25%)
- **Scenario Comparison**: Bandingkan multiple skenario dengan rekomendasi otomatis
- **Export**: Export hasil ke Excel dengan multiple sheets
- **Visualizations**: Grafik interaktif untuk revenue, cash flow, dan PSC split

## 🛠️ Tech Stack

- **Backend**: PostgreSQL + SQLAlchemy + Psycopg2
- **Frontend**: Streamlit + Plotly + Pandas
- **Database**: PostgreSQL (Neon.tech/Supabase/Railway)
- **Deployment**: Streamlit Community Cloud

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database (local atau cloud seperti Neon.tech)
- pip atau conda untuk package management

## 🚀 Installation

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
✓ Database tables created successfully
✓ CAPEX Categories inserted
✓ CAPEX Subcategories inserted
✓ CAPEX Items inserted
✓ OPEX Mappings inserted
✓ Fiscal Terms inserted
✓ Pricing Assumptions inserted
✓ Production Enhancement rates inserted
✅ Database initialization completed successfully!
```

## 🎮 Running the Application

### Local Development

```bash
streamlit run app.py
```

Application akan buka di browser pada `http://localhost:8501`

### Production Deployment

#### Streamlit Community Cloud

1. Push code ke GitHub repository
2. Login ke [share.streamlit.io](https://share.streamlit.io)
3. Deploy dari GitHub repo
4. Add secrets di Streamlit dashboard:
   ```toml
   DATABASE_URL = "postgresql://user:pass@host/db"
   ```

## 📊 Usage Guide

### 1. Create Scenario

1. Go to **"➕ Create Scenario"**
2. Pilih CAPEX items dari sidebar:
   - **Production**: CCUS EGR, CCUS EOR, Supersonic Separator
   - **Power**: CCPP, FWT
   - **Transportation**: Pipeline atau Shipping (STS, OWS, VLGC)
   - **Flaring**: FGRS
3. Set quantity untuk setiap item
4. Input scenario name dan description
5. Click **"✨ Create & Calculate Scenario"**
6. View hasil kalkulasi

### 2. View Scenarios

1. Go to **"📊 View Scenarios"**
2. Select scenario dari dropdown
3. View detail:
   - Annual results
   - CAPEX/OPEX breakdown
   - Visualizations (charts)
   - Summary report

### 3. Compare Scenarios

1. Go to **"🔍 Compare Scenarios"**
2. Select 2+ scenarios
3. Click **"🔍 Compare Scenarios"**
4. View:
   - Best scenario recommendation
   - Ranking table
   - Comparison charts
   - Export comparison

### 4. Export Results

- Click **"📥 Export to Excel"** button
- Download file dengan format:
  - Sheet 1: Summary
  - Sheet 2: CAPEX details
  - Sheet 3: OPEX details
  - Sheet 4: Annual results
  - Sheet 5: Metrics

## 📐 Financial Model

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
R_t = (P_oil,t × $60) + (P_gas,MMBTU,t × $5.5)
```

**Operating Profit:**
```
OP_t = R_t - D_t - OPEX_t
```

**PSC Split:**
```
Contractor Pre-tax = OP_t × 0.6723
Contractor Tax = Contractor Pre-tax × 0.405
Contractor After-tax = Contractor Pre-tax - Tax
Government Pre-tax = OP_t × 0.3277
Government Total = Government Pre-tax + Tax
```

**NPV:**
```
NPV = Σ(t=1 to 12) CF_t / (1+0.13)^t
```

**ASR:**
```
ASR = CAPEX_total × 0.05
```

## 📁 Project Structure

```
ScenarioCalc/
├── app.py                      # Main Streamlit app
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .gitignore
├── README.md
├── database/
│   ├── models.py              # SQLAlchemy models
│   ├── connection.py          # Database connection
│   └── init_db.py            # Database initialization
├── engine/
│   ├── calculator.py          # Financial calculation engine
│   ├── opex_generator.py     # OPEX auto-generator
│   └── comparator.py         # Scenario comparison
├── utils/
│   └── export.py             # Excel export functionality
└── exports/                   # Generated export files
```

## 🐛 Troubleshooting

### Database Connection Error
```
Check DATABASE_URL in .env file
Test connection: psql "postgresql://..."
```

### Import Error
```bash
pip install --upgrade -r requirements.txt
```

### Streamlit Error
```bash
streamlit cache clear
```

## 🔧 Development

### Add New CAPEX Item

1. Edit `database/init_db.py`
2. Add item to INSERT statements
3. Re-run: `python init_db.py`

### Modify Calculations

Edit `engine/calculator.py` - method `calculate_scenario()`

### Change Fiscal Parameters

Update values in `FiscalTerms` table atau modify `init_db.py`

## 📝 Database Schema

### Main Tables
- `capex_categories` - CAPEX categories
- `capex_items` - CAPEX item details
- `opex_mapping` - OPEX calculation rules
- `scenarios` - User scenarios
- `scenario_capex` - Selected CAPEX per scenario
- `scenario_opex` - Auto-generated OPEX
- `calculation_results` - Annual financial results
- `scenario_metrics` - Summary metrics (NPV, totals)
- `fiscal_terms` - Fiscal parameters
- `pricing_assumptions` - Price assumptions
- `production_data` - Production profiles

## 🤝 Contributing

Untuk development atau bug fixes:
1. Create branch baru
2. Make changes
3. Test thoroughly
4. Submit pull request

## 📄 License

Internal use only - IPFEST Project

## 👥 Team

**SM5 UNIV - IPFEST 2024**

## 📞 Support

Untuk pertanyaan atau issues, contact development team.

---

**Version:** 1.0.0  
**Last Updated:** December 2024
