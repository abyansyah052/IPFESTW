# DEPLOYMENT READY! ✅

## Status: Database Initialized & Application Running

### ✅ Completed Tasks

1. **Database Setup** - Supabase PostgreSQL configured and initialized
2. **CAPEX Data** - Updated dengan harga terbaru:
   - CCPP: $113,100,000/unit (100 MW)
   - FWT: $531,700,000/unit (100 MW)
   - Others: As per revised dataset
3. **OPEX Configuration** - Mostly 5% of CAPEX + escalation 2%/year
4. **Fiscal Terms** - Updated dengan DMO, post-tax splits
5. **Pricing** - Oil $60/bbl, Gas $5.5/MMBTU
6. **Streamlit App** - Running locally on http://localhost:8501

---

## Database Connection

**Supabase PostgreSQL:**
```
Host: db.swkgxntzamifnmktyabo.supabase.co
Port: 5432
Database: postgres
Username: postgres
Password: Abyansyah123
```

**Connection String:**
```
postgresql://postgres:Abyansyah123@db.swkgxntzamifnmktyabo.supabase.co:5432/postgres
```

---

## Quick Start

### Local Development

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run Streamlit app
streamlit run app.py

# 3. Open browser
http://localhost:8501
```

### Re-initialize Database (if needed)

```bash
source venv/bin/activate
python database/init_db.py
```

---

## Deployment to Streamlit Cloud

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Financial Scenario Testing App"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect GitHub repository
4. Select: `main` branch, `app.py` as main file
5. Click "Advanced settings" → "Secrets"

### 3. Add Secrets

```toml
# .streamlit/secrets.toml
DATABASE_URL = "postgresql://postgres:Abyansyah123@db.swkgxntzamifnmktyabo.supabase.co:5432/postgres"
```

6. Click "Deploy"

---

## Verified Data

### CAPEX Items (Revised)
```
CCUS_EGR        | $20,410,366.50 /unit.well
CCUS_EOR        | $16,510,366.50 /unit.well
SUPERSONIC      | $3,000,000.00 /unit
CCPP            | $113,100,000.00 /unit (100 MW)
FWT             | $531,700,000.00 /unit (100 MW)
PIPELINE_CO2    | $3,000,000.00 /km
STS             | $2,000,000.00 /vessel
OWS             | $25,000.00 /unit
VLGC            | $110,000,000.00 /unit
FGRS            | $3,000,000.00 /unit
```

### OPEX Mappings (Revised)
```
CCUS_EGR        | 5.0% of CAPEX
CCUS_EOR        | 5.0% of CAPEX
SUPERSONIC      | Fixed $150,000/year
CCPP            | 5.0% of CAPEX
FWT             | 5.0% of CAPEX
PIPELINE_CO2    | Fixed $150,000/year
STS             | 5.0% of CAPEX
OWS             | Fixed $1,250/year
VLGC            | 5.0% of CAPEX
FGRS            | Fixed $150,000/year
+ 2% escalation per year
```

### Fiscal Terms (Revised)
```
Government Oil Pre-tax:     32.77%
Government Gas Pre-tax:     32.77%
Contractor Oil Pre-tax:     67.23%
Contractor Gas Pre-tax:     67.23%
Government Oil Post-tax:    60.0%
Government Gas Post-tax:    60.0%
Contractor Oil Post-tax:    40.0%
Contractor Gas Post-tax:    40.0%
Contractor Tax Rate:        40.5%
DMO Volume:                 25.0%
DMO Fee:                    $1.00
Discount Rate:              13.0%
ASR Rate:                   5.0%
OPEX Escalation:            2.0% per year
```

### Pricing
```
Oil Price:          $60.00/bbl
Gas Price:          $5.50/MMBTU
Gas Conversion:     1027 MMSCF to MMBTU
USD to IDR:         Rp 16,500
Working Days:       220 days/year
```

---

## Features Ready

✅ **CAPEX Selection**
- Production (CCUS EGR, CCUS EOR, Supersonic Separator)
- Power (CCPP 100MW, FWT 100MW)
- Transportation (Pipeline atau Shipping)
- Flaring (FGRS)

✅ **Auto-generate OPEX**
- Based on CAPEX with 5% or fixed rates
- 2% annual escalation

✅ **Financial Calculations**
- Production enhancement (EOR +20%, EGR +25%)
- Revenue calculation
- Depreciation (DDB method)
- PSC split (oil/gas separate)
- NPV calculation (13% discount)
- DMO calculation

✅ **Scenario Comparison**
- Multi-scenario ranking
- Best scenario recommendation
- Visualization charts

✅ **Export**
- Excel export with multiple sheets
- Summary reports

---

## Testing Checklist

- [x] Database connection
- [x] CAPEX data loaded correctly
- [x] OPEX auto-generation
- [x] Fiscal terms applied
- [x] Streamlit UI loads
- [ ] Create test scenario
- [ ] Verify calculations
- [ ] Test comparison feature
- [ ] Test export functionality

---

## Next Steps

1. **Test the Application** - Create a sample scenario and verify calculations
2. **Deploy to Streamlit Cloud** - Follow deployment steps above
3. **Share with Team** - Get the deployed URL

---

## Support

**Project:** Financial Scenario Testing  
**Version:** 1.0.0  
**Date:** December 2024  
**Team:** SM5 UNIV - IPFEST 2024

For issues atau questions, check:
- [README.md](README.md) - Full documentation
- [ToDo.md](ToDo.md) - Original requirements
- [revisidataset.md](revisidataset.md) - Revised dataset

---

**🎉 Application is ready to use!**

Access locally: http://localhost:8501
