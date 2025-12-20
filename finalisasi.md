Baik, saya sudah selesai menganalisis Excel baru kamu dengan openpyxl. Ada **beberapa kesalahan KRITIS** di dokumentasi MD kamu yang perlu diperbaiki:

## 🔴 KESALAHAN UTAMA DI FORMULA_DOCUMENTATION.MD:

### 1. **NET CASH FLOW ADALAH CUMULATIVE, BUKAN ANNUAL**

**❌ SALAH (di MD):**
```
NCF_t = Operating_Profit_t = Available_for_Split_t
```

**✅ BENAR (di Excel):**
```python
# Year 1 (2026):
NCF_1 = Revenue_1 - Total_Cost_1

# Year 2+ (2027-2037):
NCF_t = (Revenue_t + NCF_(t-1)) - Total_Cost_t

# Excel formulas:
# J33: =J9-J17
# K33: =(K9+J33)-K17
# L33: =(L9+K33)-L17
# ... dst
```

Ini adalah **CUMULATIVE CASH FLOW**, bukan standalone per tahun!

***

### 2. **PSC SPLIT HANYA BERLAKU JIKA AVAILABLE > 0 DAN BUKAN TAHUN ASR**

**❌ SALAH (di MD):**
PSC Split dihitung untuk semua tahun tanpa kondisi.

**✅ BENAR (di Excel):**
```python
if available_for_split <= 0:
    # TIDAK ADA PSC SPLIT
    contractor_pretax = 0
    contractor_tax = 0
    contractor_aftertax = 0
    government_pretax = 0
    government_tax = 0
    government_total = 0
elif year == last_year (2037):  # ASR year
    # TIDAK ADA PSC SPLIT di tahun ASR
    contractor_pretax = 0
    contractor_tax = 0
    contractor_aftertax = 0
    government_pretax = 0
    government_tax = 0
    government_total = 0
else:
    # PSC SPLIT BERLAKU
    contractor_pretax = available_for_split × 0.6723
    contractor_tax = contractor_pretax × 0.405
    contractor_aftertax = contractor_pretax - contractor_tax
    government_pretax = available_for_split × 0.3277
    government_tax = contractor_tax
    government_total = government_pretax + government_tax
```

**Hasil di Excel:**
- **2026**: Available = -$147M → **NO SPLIT**
- **2027-2036**: Available > 0 → **SPLIT APPLIES** (10 tahun)
- **2037**: Available = $3.1M, tapi ada ASR → **NO SPLIT**

***

### 3. **DEPRECIATION FORMULA (DDB) SALAH**

**❌ SALAH (di MD):**
```
Rate = Factor / Life = 0.25 / 5 = 0.05
D_t = (Book_Value_t-1) × 0.05
```
Tapi tidak ada switch ke straight-line.

**✅ BENAR (di Excel):**
```python
# Excel DDB dengan factor=0.25, life=5
Rate = Factor / Life = 0.25 / 5 = 0.05

# Declining balance (5% per tahun dari remaining book value)
Book_Value_0 = CAPEX = $156,620,733

D_1 = Book_Value_0 × 0.05 = $7,831,036.65
D_2 = (Book_Value_0 - D_1) × 0.05 = $7,439,484.82
D_3 = (Book_Value_0 - D_1 - D_2) × 0.05 = $7,067,510.58
D_4 = ... × 0.05 = $6,714,135.05
D_5 = ... × 0.05 = $6,378,428.30

# Total depreciation = $35,430,595.39 (22.62% of CAPEX)
```

Ini adalah **simple declining balance 5%**, BUKAN double declining balance!

***

### 4. **SUMMARY TOTALS HANYA DARI TAHUN 2027-2036**

**❌ SALAH (di MD):**
```
contractor_take = sum(Contractor_AfterTax untuk semua tahun)
```

**✅ BENAR (di Excel):**
```python
# Excel formulas:
# Contractor Take: =SUM(K25:T25)  # 2027-2036 saja (10 tahun)
# Gov Take: =SUM(K30:T30)         # 2027-2036 saja (10 tahun)  
# Contractor PTCF: =SUM(K23:T23)  # 2027-2036 saja (10 tahun)

# Excludes:
# - Year 2026 (J) - karena no split
# - Year 2037 (U) - karena ASR year
```

***

### 5. **OPEX CALCULATION**

Di Excel terbaru, OPEX langsung di-sum dari Existing Data, bukan auto-generated dengan escalation 2%.

**Excel formula (row 12):**
```
J12: =SUM('Existing Data'!R20:R26,'Existing Data'!R30)
K12: =SUM('Existing Data'!S20:S26,'Existing Data'!S30)
```

***

## ✅ CORRECTED PYTHON CODE:

```python
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class FiscalTerms:
    gov_pretax_split: Decimal = Decimal('0.3277')
    contractor_pretax_split: Decimal = Decimal('0.6723')
    contractor_tax_rate: Decimal = Decimal('0.405')
    discount_rate: Decimal = Decimal('0.13')
    depreciation_life: int = 5
    depreciation_factor: Decimal = Decimal('0.25')
    asr_rate: Decimal = Decimal('0.05')
    salvage_value: Decimal = Decimal('0')

class FinancialCalculator:
    
    def calculate_scenario(self, scenario_id: int) -> Tuple[List[Dict], Dict]:
        """
        Main calculation engine matching Excel logic exactly
        """
        
        # Load data
        scenario = self.load_scenario(scenario_id)
        production_data = self.load_production_data(scenario['production_profile_id'])
        capex_items = self.load_scenario_capex(scenario_id)
        fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
        pricing = self.load_pricing(scenario['pricing_id'])
        enhancement = self.load_enhancement(scenario['enhancement_id'])
        opex_data = self.load_scenario_opex(scenario_id)
        
        # Calculate totals
        total_capex = sum(Decimal(str(item['total_cost'])) for item in capex_items)
        asr_amount = total_capex * fiscal.asr_rate
        
        project_start_year = self.get_project_start_year(scenario['production_profile_id'])
        last_year = project_start_year + scenario['project_duration'] - 1
        
        results = []
        cumulative_cf = Decimal('0')  # This is what Excel shows in row 33
        
        for idx, prod_year in enumerate(production_data):
            period = idx + 1
            year = prod_year['year']
            
            # === PRODUCTION ===
            base_oil_bbl = Decimal(str(prod_year['condensate_rate_bopd'])) * Decimal(str(pricing.working_days))
            base_gas_mmscf = Decimal(str(prod_year['gas_rate_mmscfd'])) * Decimal(str(pricing.working_days))
            
            enhanced_oil_bbl = base_oil_bbl * (Decimal('1') + enhancement.eor_rate)
            enhanced_gas_mmscf = base_gas_mmscf * (Decimal('1') + enhancement.egr_rate)
            enhanced_gas_mmbtu = enhanced_gas_mmscf * pricing.mmscf_to_mmbtu
            
            # === REVENUE ===
            oil_revenue = enhanced_oil_bbl * pricing.oil_price
            gas_revenue = enhanced_gas_mmbtu * pricing.gas_price
            total_revenue = oil_revenue + gas_revenue
            
            # === COSTS ===
            year_capex = self.get_capex_for_year(capex_items, year)
            year_opex = self.get_opex_for_year(opex_data, year)
            
            # Depreciation: only first 5 years, declining balance 5%
            if period <= fiscal.depreciation_life:
                depreciation = self.calculate_depreciation_ddb(
                    cost=total_capex,
                    salvage=fiscal.salvage_value,
                    life=fiscal.depreciation_life,
                    period=period,
                    factor=fiscal.depreciation_factor
                )
            else:
                depreciation = Decimal('0')
            
            # ASR: only last year
            year_asr = asr_amount if year == last_year else Decimal('0')
            
            # === TOTAL COST RECOVERABLE ===
            total_cost_recoverable = year_capex + year_opex + depreciation + year_asr
            
            # === AVAILABLE FOR PRODUCTION SPLIT ===
            available_for_split = total_revenue - total_cost_recoverable
            
            # === PSC SPLIT - CRITICAL RULE ===
            # NO SPLIT if:
            # 1. Available <= 0 (losses), OR
            # 2. ASR year (last year)
            if available_for_split <= 0 or year == last_year:
                contractor_pretax = Decimal('0')
                contractor_tax = Decimal('0')
                contractor_aftertax = Decimal('0')
                government_pretax = Decimal('0')
                government_tax = Decimal('0')
                government_total = Decimal('0')
            else:
                # PSC Split applies
                contractor_pretax = available_for_split * fiscal.contractor_pretax_split
                contractor_tax = contractor_pretax * fiscal.contractor_tax_rate
                contractor_aftertax = contractor_pretax - contractor_tax
                
                government_pretax = available_for_split * fiscal.gov_pretax_split
                government_tax = contractor_tax  # Tax goes to government
                government_total = government_pretax + government_tax
            
            # === ANNUAL CASH FLOW ===
            annual_cf = available_for_split  # Revenue - Total Cost
            
            # === CUMULATIVE CASH FLOW (what Excel shows in row 33) ===
            cumulative_cf += annual_cf
            
            year_result = {
                'scenario_id': scenario_id,
                'year': year,
                'period': period,
                # Production
                'oil_production_bbl': float(enhanced_oil_bbl),
                'gas_production_mmscf': float(enhanced_gas_mmscf),
                'gas_production_mmbtu': float(enhanced_gas_mmbtu),
                # Revenue
                'oil_revenue': float(oil_revenue),
                'gas_revenue': float(gas_revenue),
                'total_revenue': float(total_revenue),
                # Costs
                'capex': float(year_capex),
                'opex': float(year_opex),
                'depreciation': float(depreciation),
                'asr': float(year_asr),
                'total_cost_recoverable': float(total_cost_recoverable),
                # Available
                'available_for_split': float(available_for_split),
                # Contractor
                'contractor_pretax': float(contractor_pretax),
                'contractor_tax': float(contractor_tax),
                'contractor_aftertax': float(contractor_aftertax),
                # Government
                'government_pretax': float(government_pretax),
                'government_tax': float(government_tax),
                'government_total': float(government_total),
                # Cash Flow
                'annual_cash_flow': float(annual_cf),
                'cumulative_cash_flow': float(cumulative_cf)
            }
            
            results.append(year_result)
        
        # Save to database
        self.save_calculation_results(results)
        
        # Calculate metrics
        metrics = self.calculate_metrics(scenario_id, results, fiscal, total_capex)
        self.save_scenario_metrics(scenario_id, metrics)
        
        return results, metrics
    
    def calculate_depreciation_ddb(
        self, 
        cost: Decimal, 
        salvage: Decimal, 
        life: int, 
        period: int, 
        factor: Decimal
    ) -> Decimal:
        """
        Excel DDB function - Declining Balance Depreciation
        With factor=0.25 and life=5, this is 5% declining balance
        """
        if period > life or period < 1:
            return Decimal('0')
        
        rate = factor / Decimal(life)  # 0.25 / 5 = 0.05 (5%)
        
        book_value = cost
        for p in range(1, period + 1):
            depreciation = book_value * rate
            
            # Check if below salvage
            if book_value - depreciation < salvage:
                depreciation = book_value - salvage
            
            if p == period:
                return depreciation
            
            book_value -= depreciation
        
        return Decimal('0')
    
    def calculate_metrics(
        self, 
        scenario_id: int, 
        results: List[Dict], 
        fiscal: FiscalTerms,
        total_capex: Decimal
    ) -> Dict:
        """
        Calculate financial metrics matching Excel
        """
        
        # Use cumulative cash flows for NPV/IRR (row 33 in Excel)
        cash_flows = [float(r['cumulative_cash_flow']) for r in results]
        
        # NPV - Excel style (first CF is end of period 1)
        try:
            discount_rate = float(fiscal.discount_rate)
            npv = sum(cf / ((1 + discount_rate) ** (i + 1)) 
                     for i, cf in enumerate(cash_flows))
            npv = Decimal(str(npv))
        except:
            npv = None
        
        # IRR
        try:
            import numpy_financial as npf
            irr = Decimal(str(npf.irr(cash_flows)))
        except:
            irr = None
        
        # Payback Period
        payback = self.calculate_payback_period(results)
        
        # Gross Revenue = SUM of all revenues
        gross_revenue = sum(Decimal(str(r['total_revenue'])) for r in results)
        
        # Contractor Take = SUM of contractor after-tax (ONLY years with split)
        # In Excel: =SUM(K25:T25) - excludes year 1 (J) and year 12 (U)
        contractor_take = sum(
            Decimal(str(r['contractor_aftertax'])) 
            for r in results 
            if r['contractor_aftertax'] > 0
        )
        
        # Gov Take = SUM of government total (ONLY years with split)
        gov_take = sum(
            Decimal(str(r['government_total'])) 
            for r in results 
            if r['government_total'] > 0
        )
        
        # Contractor PTCF = SUM of contractor tax (ONLY years with split)
        contractor_ptcf = sum(
            Decimal(str(r['contractor_tax'])) 
            for r in results 
            if r['contractor_tax'] > 0
        )
        
        # Other totals
        total_opex = sum(Decimal(str(r['opex'])) for r in results)
        
        metrics = {
            'total_capex': float(total_capex),
            'total_opex': float(total_opex),
            'gross_revenue': float(gross_revenue),
            'contractor_take': float(contractor_take),
            'government_take': float(gov_take),
            'contractor_ptcf': float(contractor_ptcf),
            'npv': float(npv) if npv else None,
            'irr': float(irr) if irr else None,
            'payback_period': float(payback) if payback else None,
            'asr_amount': float(total_capex * fiscal.asr_rate)
        }
        
        return metrics
    
    def calculate_payback_period(self, results: List[Dict]) -> Optional[Decimal]:
        """
        Calculate when cumulative CF becomes positive
        """
        for i, r in enumerate(results):
            if Decimal(str(r['cumulative_cash_flow'])) >= 0:
                if i == 0:
                    return Decimal('1')
                
                prev_cf = Decimal(str(results[i-1]['cumulative_cash_flow']))
                curr_cf = Decimal(str(r['cumulative_cash_flow']))
                
                if curr_cf == prev_cf:
                    return Decimal(i + 1)
                
                # Fraction: period + (abs(prev_cf) / (curr_cf - prev_cf))
                fraction = abs(prev_cf) / (curr_cf - prev_cf)
                return Decimal(i) + fraction
        
        return None
```

***

## 📋 CORRECTED MD DOCUMENTATION - KEY SECTIONS:

### PSC Split Rules

```markdown
## PSC Split Rules (CRITICAL)

PSC Split **HANYA BERLAKU** jika:
1. `Available_for_Split > 0` (ada profit), DAN
2. Bukan tahun ASR (tahun terakhir)

### Kondisi NO SPLIT:

#### 1. Available ≤ 0 (Losses)
```
if available_for_split <= 0:
    contractor_pretax = 0
    contractor_tax = 0
    contractor_aftertax = 0
    government_pretax = 0
    government_tax = 0
    government_total = 0
```

**Contoh:** Year 2026
- Revenue = $20,489,974
- Cost = $167,932,806
- Available = **-$147,442,832** (LOSS)
- Result: **NO PSC SPLIT** (both parties get $0)

#### 2. ASR Year (Last Year)
```
if year == last_year:  # 2037
    # NO PSC SPLIT even if Available > 0
    contractor_pretax = 0
    contractor_tax = 0
    contractor_aftertax = 0
    government_pretax = 0
    government_tax = 0
    government_total = 0
```

**Contoh:** Year 2037
- Revenue = $15,273,214
- Cost = $12,159,268 (includes ASR $7,831,037)
- Available = **$3,113,946** (PROFIT)
- Result: **NO PSC SPLIT** (ASR year exception)

### Kondisi SPLIT APPLIES:

```
if available_for_split > 0 and year != last_year:
    # PSC Split applies
    contractor_pretax = available_for_split × 0.6723
    contractor_tax = contractor_pretax × 0.405
    contractor_aftertax = contractor_pretax - contractor_tax
    
    government_pretax = available_for_split × 0.3277
    government_tax = contractor_tax
    government_total = government_pretax + government_tax
```

**Berlaku untuk:** Years 2027-2036 (10 tahun)
```

### Cash Flow Calculation

```markdown
## Cash Flow Analysis

### Annual Cash Flow
```
Annual_CF_t = Total_Revenue_t - Total_Cost_Recoverable_t
Annual_CF_t = Available_for_Split_t
```

### Cumulative Cash Flow (Excel Row 33)

**Year 1:**
```
Cumulative_CF_1 = Annual_CF_1
```

**Year 2+:**
```
Cumulative_CF_t = Cumulative_CF_(t-1) + Annual_CF_t
```

**Excel Formulas:**
```
J33: =J9-J17                  # Year 1: Revenue - Cost
K33: =(K9+J33)-K17            # Year 2: (Revenue + Prev_CF) - Cost
L33: =(L9+K33)-L17            # Year 3: (Revenue + Prev_CF) - Cost
...
U33: =(U9+T33)-U17            # Year 12: (Revenue + Prev_CF) - Cost
```

**IMPORTANT:** Excel menggunakan cumulative cash flow untuk perhitungan NPV dan IRR!
```
