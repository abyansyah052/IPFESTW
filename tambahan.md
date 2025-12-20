
**expected calculation output (J35-J41):**
- NPV at 13%
- IRR
- Payback Period
- Gross Revenue = SUM all revenues
- Contractor Take = SUM contractor after-tax (K25:T25, skip year 2026)
- Gov Take = SUM government total (K30:T30, skip year 2026)
- Contractor PTCF = SUM contractor tax (K23:T23, skip year 2026)

## 2. Key Findings:

1. **Tahun 2026** tidak ada Contractor/Government split (karena full CAPEX habis duluan)
2. **PSC Split mulai tahun 2027** (column K onwards)
3. **Cash Flow = Available** (bukan Revenue - OPEX - CAPEX)
4. **NPV bisa negatif** karena CAPEX besar di awal

## Complete Python Code - FINAL VERSION:

```python
# calculator.py - COMPLETE REWRITE
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
import numpy_financial as npf
from dataclasses import dataclass
from database import Database

@dataclass
class FiscalTerms:
    gov_oil_pretax: Decimal = Decimal('0.3277')
    gov_gas_pretax: Decimal = Decimal('0.3277')
    contractor_oil_pretax: Decimal = Decimal('0.6723')
    contractor_gas_pretax: Decimal = Decimal('0.6723')
    contractor_tax_rate: Decimal = Decimal('0.405')
    discount_rate: Decimal = Decimal('0.13')
    depreciation_life: int = 5
    depreciation_factor: Decimal = Decimal('0.25')
    asr_rate: Decimal = Decimal('0.05')
    salvage_value: Decimal = Decimal('0')
    opex_escalation_rate: Decimal = Decimal('0.02')

@dataclass
class PricingAssumptions:
    oil_price: Decimal = Decimal('60.00')
    gas_price: Decimal = Decimal('5.50')
    mmscf_to_mmbtu: Decimal = Decimal('1027')
    working_days: int = 220

@dataclass
class ProductionEnhancement:
    eor_rate: Decimal = Decimal('0.20')
    egr_rate: Decimal = Decimal('0.25')

class FinancialCalculator:
    
    def __init__(self, db: Database):
        self.db = db
    
    def calculate_scenario(self, scenario_id: int) -> Tuple[List[Dict], Dict]:
        """
        Main calculation engine - matches Excel Calculation Example structure
        """
        
        # Load data
        scenario = self.load_scenario(scenario_id)
        production_data = self.load_production_data(scenario['production_profile_id'])
        capex_items = self.load_scenario_capex(scenario_id)
        fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
        pricing = self.load_pricing(scenario['pricing_id'])
        enhancement = self.load_enhancement(scenario['enhancement_id'])
        
        # Generate OPEX
        self.generate_opex(scenario_id, capex_items, scenario)
        opex_data = self.load_scenario_opex(scenario_id)
        
        # Calculate totals
        total_capex = sum(Decimal(str(item['total_cost'])) for item in capex_items)
        asr_amount = total_capex * fiscal.asr_rate
        
        project_start_year = self.get_project_start_year(scenario['production_profile_id'])
        last_year = project_start_year + scenario['project_duration'] - 1
        first_year = project_start_year
        
        results = []
        cumulative_cf = Decimal('0')
        
        for idx, prod_year in enumerate(production_data):
            period = idx + 1
            year = prod_year['year']
            
            # === PRODUCTION WITH ENHANCEMENT ===
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
            
            # Depreciation: only first 5 years
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
            
            # === PSC SPLIT (tidak dihitung di tahun pertama jika available negatif besar) ===
            # Di Excel, PSC split mulai dari tahun kedua (column K = 2027)
            # Tapi formula tetap ada, jadi kita hitung untuk semua tahun
            
            contractor_pretax = available_for_split * fiscal.contractor_oil_pretax
            contractor_tax = contractor_pretax * fiscal.contractor_tax_rate
            contractor_aftertax = contractor_pretax - contractor_tax
            
            government_pretax = available_for_split * fiscal.gov_oil_pretax
            government_tax = contractor_tax  # Tax goes to government
            government_total = government_pretax + government_tax
            
            # === NET CASH FLOW ===
            # Net CF = Available for Split (sama dengan Revenue - Total Cost)
            net_cf = available_for_split
            cumulative_cf += net_cf
            
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
                'net_cash_flow': float(net_cf),
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
        Declining Balance Depreciation - Excel DDB function
        """
        if period > life or period < 1:
            return Decimal('0')
        
        rate = factor / Decimal(life)
        depreciation = Decimal('0')
        remaining_value = cost
        
        for p in range(1, period + 1):
            year_depreciation = remaining_value * rate
            
            # Straight-line comparison
            periods_remaining = Decimal(life - p + 1)
            if periods_remaining > 0:
                straight_line = (remaining_value - salvage) / periods_remaining
            else:
                straight_line = Decimal('0')
            
            # Use greater of DDB or straight-line
            if straight_line > year_depreciation:
                year_depreciation = straight_line
            
            if p == period:
                depreciation = year_depreciation
            
            remaining_value -= year_depreciation
            
            if remaining_value < salvage:
                remaining_value = salvage
                break
        
        return depreciation
    
    def calculate_metrics(
        self, 
        scenario_id: int, 
        results: List[Dict], 
        fiscal: FiscalTerms,
        total_capex: Decimal
    ) -> Dict:
        """
        Calculate financial metrics matching Excel output
        """
        
        # Cash flows for NPV and IRR
        cash_flows = [float(r['net_cash_flow']) for r in results]
        
        # NPV
        try:
            npv = Decimal(str(npf.npv(float(fiscal.discount_rate), cash_flows)))
        except:
            npv = None
        
        # IRR
        try:
            irr = Decimal(str(npf.irr(cash_flows)))
        except:
            irr = None
        
        # Payback Period
        payback = self.calculate_payback_period(results)
        
        # Gross Revenue = SUM of all revenues
        gross_revenue = sum(Decimal(str(r['total_revenue'])) for r in results)
        
        # Contractor Take = SUM of contractor after-tax (skip first year if needed)
        # In Excel: SUM(K25:T25) means years 2027-2036
        # But formula exists for all years, so we sum all
        contractor_take = sum(Decimal(str(r['contractor_aftertax'])) for r in results)
        
        # Gov Take = SUM of government total
        gov_take = sum(Decimal(str(r['government_total'])) for r in results)
        
        # Contractor PTCF = SUM of contractor tax
        contractor_ptcf = sum(Decimal(str(r['contractor_tax'])) for r in results)
        
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
        Calculate payback period when cumulative cash flow becomes positive
        Uses Excel formula: =P32+(-O33/P33)
        """
        for i, r in enumerate(results):
            if Decimal(str(r['cumulative_cash_flow'])) >= 0:
                if i == 0:
                    return Decimal('1')
                
                prev_cf = Decimal(str(results[i-1]['cumulative_cash_flow']))
                curr_cf = Decimal(str(r['cumulative_cash_flow']))
                
                if curr_cf == prev_cf:
                    return Decimal(i + 1)
                
                # Fraction calculation: previous period + (abs(prev_cf) / curr_period_cf)
                fraction = abs(prev_cf) / (curr_cf - prev_cf)
                return Decimal(i) + fraction
        
        return None
    
    def generate_opex(self, scenario_id: int, capex_items: List[Dict], scenario: Dict):
        """
        Auto-generate OPEX with 2% annual escalation
        """
        
        self.db.execute("DELETE FROM scenario_opex WHERE scenario_id = %s", (scenario_id,))
        
        project_duration = scenario['project_duration']
        project_start_year = self.get_project_start_year(scenario['production_profile_id'])
        
        # Load fiscal terms for escalation rate
        fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
        
        for capex_item in capex_items:
            opex_mappings = self.db.fetch_all(
                "SELECT * FROM opex_mapping WHERE capex_item_id = %s",
                (capex_item['capex_item_id'],)
            )
            
            for opex_map in opex_mappings:
                year_start = opex_map['year_start'] if opex_map['year_start'] else 1
                year_end = opex_map['year_end'] if opex_map['year_end'] else project_duration
                
                # Base OPEX calculation
                if opex_map['opex_calculation_method'] == 'PERCENTAGE':
                    base_opex_amount = Decimal(str(capex_item['total_cost'])) * Decimal(str(opex_map['opex_rate']))
                elif opex_map['opex_calculation_method'] == 'FIXED':
                    base_opex_amount = Decimal(str(opex_map['opex_rate']))
                elif opex_map['opex_calculation_method'] == 'PER_UNIT':
                    base_opex_amount = Decimal(str(capex_item['quantity'])) * Decimal(str(opex_map['opex_rate']))
                else:
                    base_opex_amount = Decimal('0')
                
                # Apply escalation per year
                for year_offset in range(year_start - 1, year_end):
                    year = project_start_year + year_offset
                    
                    # OPEX with escalation: OPEX_base * (1 + escalation_rate)^year_offset
                    escalation_factor = (Decimal('1') + fiscal.opex_escalation_rate) ** year_offset
                    opex_amount = base_opex_amount * escalation_factor
                    
                    self.db.execute(
                        """
                        INSERT INTO scenario_opex 
                        (scenario_id, year, opex_name, opex_amount, calculation_note)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (scenario_id, year, opex_map['opex_name'], float(opex_amount),
                         f"{opex_map['opex_calculation_method']}: {opex_map['opex_rate']} × (1.02^{year_offset})")
                    )
    
    def get_capex_for_year(self, capex_items: List[Dict], year: int) -> Decimal:
        """Get total CAPEX for specific year"""
        total = Decimal('0')
        for item in capex_items:
            if item.get('year_incurred') == year:
                total += Decimal(str(item['total_cost']))
        return total
    
    def get_opex_for_year(self, opex_data: List[Dict], year: int) -> Decimal:
        """Get total OPEX for specific year"""
        total = Decimal('0')
        for opex in opex_data:
            if opex['year'] == year:
                total += Decimal(str(opex['opex_amount']))
        return total
    
    # ... (other helper functions remain the same: load_scenario, load_production_data, etc.)
    
    def save_calculation_results(self, results: List[Dict]):
        """Save yearly calculation results"""
        for result in results:
            self.db.execute(
                """
                INSERT INTO calculation_results (
                    scenario_id, year, period,
                    oil_production_bbl, gas_production_mmscf, gas_production_mmbtu,
                    oil_revenue, gas_revenue, total_revenue,
                    capex, opex, depreciation, asr, total_cost_recoverable,
                    available_for_split,
                    contractor_pretax, contractor_tax, contractor_aftertax,
                    government_pretax, government_tax, government_total,
                    net_cash_flow, cumulative_cash_flow
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (scenario_id, year) DO UPDATE SET
                    period = EXCLUDED.period,
                    oil_production_bbl = EXCLUDED.oil_production_bbl,
                    gas_production_mmscf = EXCLUDED.gas_production_mmscf,
                    gas_production_mmbtu = EXCLUDED.gas_production_mmbtu,
                    oil_revenue = EXCLUDED.oil_revenue,
                    gas_revenue = EXCLUDED.gas_revenue,
                    total_revenue = EXCLUDED.total_revenue,
                    capex = EXCLUDED.capex,
                    opex = EXCLUDED.opex,
                    depreciation = EXCLUDED.depreciation,
                    asr = EXCLUDED.asr,
                    total_cost_recoverable = EXCLUDED.total_cost_recoverable,
                    available_for_split = EXCLUDED.available_for_split,
                    contractor_pretax = EXCLUDED.contractor_pretax,
                    contractor_tax = EXCLUDED.contractor_tax,
                    contractor_aftertax = EXCLUDED.contractor_aftertax,
                    government_pretax = EXCLUDED.government_pretax,
                    government_tax = EXCLUDED.government_tax,
                    government_total = EXCLUDED.government_total,
                    net_cash_flow = EXCLUDED.net_cash_flow,
                    cumulative_cash_flow = EXCLUDED.cumulative_cash_flow
                """,
                (
                    result['scenario_id'], result['year'], result['period'],
                    result['oil_production_bbl'], result['gas_production_mmscf'], result['gas_production_mmbtu'],
                    result['oil_revenue'], result['gas_revenue'], result['total_revenue'],
                    result['capex'], result['opex'], result['depreciation'], result['asr'],
                    result['total_cost_recoverable'], result['available_for_split'],
                    result['contractor_pretax'], result['contractor_tax'], result['contractor_aftertax'],
                    result['government_pretax'], result['government_tax'], result['government_total'],
                    result['net_cash_flow'], result['cumulative_cash_flow']
                )
            )
    
    def save_scenario_metrics(self, scenario_id: int, metrics: Dict):
        """Save scenario metrics"""
        self.db.execute(
            """
            INSERT INTO scenario_metrics (
                scenario_id,
                total_capex, total_opex, gross_revenue,
                contractor_take, government_take, contractor_ptcf,
                npv, irr, payback_period, asr_amount,
                calculated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (scenario_id) DO UPDATE SET
                total_capex = EXCLUDED.total_capex,
                total_opex = EXCLUDED.total_opex,
                gross_revenue = EXCLUDED.gross_revenue,
                contractor_take = EXCLUDED.contractor_take,
                government_take = EXCLUDED.government_take,
                contractor_ptcf = EXCLUDED.contractor_ptcf,
                npv = EXCLUDED.npv,
                irr = EXCLUDED.irr,
                payback_period = EXCLUDED.payback_period,
                asr_amount = EXCLUDED.asr_amount,
                calculated_at = NOW()
            """,
            (
                scenario_id,
                metrics['total_capex'], metrics['total_opex'], metrics['gross_revenue'],
                metrics['contractor_take'], metrics['government_take'], metrics['contractor_ptcf'],
                metrics['npv'], metrics['irr'], metrics['payback_period'], metrics['asr_amount']
            )
        )
    
    # Keep all existing load functions...
    def load_scenario(self, scenario_id: int) -> Dict:
        return self.db.fetch_one("SELECT * FROM scenarios WHERE id = %s", (scenario_id,))
    
    def load_production_data(self, profile_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT year, condensate_rate_bopd, gas_rate_mmscfd FROM production_data WHERE profile_id = %s ORDER BY year",
            (profile_id,)
        )
    
    def load_scenario_capex(self, scenario_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT sc.*, ci.code, ci.name, ci.unit, ci.unit_cost FROM scenario_capex sc JOIN capex_items ci ON ci.id = sc.capex_item_id WHERE sc.scenario_id = %s",
            (scenario_id,)
        )
    
    def load_scenario_opex(self, scenario_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT * FROM scenario_opex WHERE scenario_id = %s ORDER BY year",
            (scenario_id,)
        )
    
    def load_fiscal_terms(self, fiscal_id: int) -> FiscalTerms:
        data = self.db.fetch_one("SELECT * FROM fiscal_terms WHERE id = %s", (fiscal_id,))
        return FiscalTerms(
            gov_oil_pretax=Decimal(str(data['gov_oil_pretax'])),
            gov_gas_pretax=Decimal(str(data['gov_gas_pretax'])),
            contractor_oil_pretax=Decimal(str(data['contractor_oil_pretax'])),
            contractor_gas_pretax=Decimal(str(data['contractor_gas_pretax'])),
            contractor_tax_rate=Decimal(str(data['contractor_tax_rate'])),
            discount_rate=Decimal(str(data['discount_rate'])),
            depreciation_life=data['depreciation_life'],
            depreciation_factor=Decimal(str(data['depreciation_factor'])),
            asr_rate=Decimal(str(data['asr_rate'])),
            salvage_value=Decimal(str(data['salvage_value'])),
            opex_escalation_rate=Decimal(str(data['opex_escalation_rate']))
        )
    
    def load_pricing(self, pricing_id: int) -> PricingAssumptions:
        data = self.db.fetch_one("SELECT * FROM pricing_assumptions WHERE id = %s", (pricing_id,))
        return PricingAssumptions(
            oil_price=Decimal(str(data['oil_price'])),
            gas_price=Decimal(str(data['gas_price'])),
            mmscf_to_mmbtu=Decimal(str(data['mmscf_to_mmbtu'])),
            working_days=data['working_days']
        )
    
    def load_enhancement(self, enhancement_id: int) -> ProductionEnhancement:
        data = self.db.fetch_one("SELECT * FROM production_enhancement WHERE id = %s", (enhancement_id,))
        return ProductionEnhancement(
            eor_rate=Decimal(str(data['eor_rate'])),
            egr_rate=Decimal(str(data['egr_rate']))
        )
    
    def get_project_start_year(self, profile_id: int) -> int:
        result = self.db.fetch_one(
            "SELECT project_start_year FROM production_profiles WHERE id = %s",
            (profile_id,)
        )
        return result['project_start_year']
```

## Updated Database Schema:

```sql
-- Add missing columns to calculation_results
ALTER TABLE calculation_results ADD COLUMN IF NOT EXISTS period INTEGER;
ALTER TABLE calculation_results ADD COLUMN IF NOT EXISTS asr DECIMAL(18,2) DEFAULT 0;
ALTER TABLE calculation_results ADD COLUMN IF NOT EXISTS total_cost_recoverable DECIMAL(18,2);
ALTER TABLE calculation_results ADD COLUMN IF NOT EXISTS available_for_split DECIMAL(18,2);
ALTER TABLE calculation_results RENAME COLUMN operating_profit TO available_for_split;

-- Update scenario_metrics columns
ALTER TABLE scenario_metrics ADD COLUMN IF NOT EXISTS gross_revenue DECIMAL(18,2);
ALTER TABLE scenario_metrics ADD COLUMN IF NOT EXISTS contractor_take DECIMAL(18,2);
ALTER TABLE scenario_metrics ADD COLUMN IF NOT EXISTS government_take DECIMAL(18,2);
ALTER TABLE scenario_metrics ADD COLUMN IF NOT EXISTS contractor_ptcf DECIMAL(18,2);
ALTER TABLE scenario_metrics DROP COLUMN IF EXISTS total_revenue;
ALTER TABLE scenario_metrics DROP COLUMN IF EXISTS total_contractor_aftertax;
ALTER TABLE scenario_metrics DROP COLUMN IF EXISTS total_government_take;
ALTER TABLE scenario_metrics DROP COLUMN IF EXISTS total_tax_paid;

-- Add OPEX escalation to fiscal_terms
ALTER TABLE fiscal_terms ADD COLUMN IF NOT EXISTS opex_escalation_rate DECIMAL(6,4) DEFAULT 0.02;
```
Code yang Benar untuk ASR:
Kamu perlu:
Tambah field asr di calculation_results table
Hitung ASR di tahun terakhir sebagai item terpisah
python
# Tambah kolom ASR di table
ALTER TABLE calculation_results ADD COLUMN asr DECIMAL(18,2) DEFAULT 0;

python
def calculate_scenario(self, scenario_id: int) -> Tuple[List[Dict], Dict]:
    """Main calculation engine"""
    
    scenario = self.load_scenario(scenario_id)
    production_data = self.load_production_data(scenario['production_profile_id'])
    capex_items = self.load_scenario_capex(scenario_id)
    fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
    pricing = self.load_pricing(scenario['pricing_id'])
    enhancement = self.load_enhancement(scenario['enhancement_id'])
    
    self.generate_opex(scenario_id, capex_items, scenario)
    opex_data = self.load_scenario_opex(scenario_id)
    
    total_capex = sum(Decimal(str(item['total_cost'])) for item in capex_items)
    
    # Calculate ASR (5% of total CAPEX)
    asr_amount = total_capex * fiscal.asr_rate
    project_start_year = self.get_project_start_year(scenario['production_profile_id'])
    last_year = project_start_year + scenario['project_duration'] - 1  # 2037
    
    results = []
    cumulative_cf = Decimal('0')
    
    for idx, prod_year in enumerate(production_data):
        period = idx + 1
        year = prod_year['year']
        
        # Production with enhancement
        base_oil_bbl = Decimal(str(prod_year['condensate_rate_bopd'])) * Decimal(str(pricing.working_days))
        base_gas_mmscf = Decimal(str(prod_year['gas_rate_mmscfd'])) * Decimal(str(pricing.working_days))
        
        enhanced_oil_bbl = base_oil_bbl * (Decimal('1') + enhancement.eor_rate)
        enhanced_gas_mmscf = base_gas_mmscf * (Decimal('1') + enhancement.egr_rate)
        enhanced_gas_mmbtu = enhanced_gas_mmscf * pricing.mmscf_to_mmbtu
        
        # Revenue
        oil_revenue = enhanced_oil_bbl * pricing.oil_price
        gas_revenue = enhanced_gas_mmbtu * pricing.gas_price
        total_revenue = oil_revenue + gas_revenue
        
        # Costs
        year_capex = self.get_capex_for_year(capex_items, year)
        year_opex = self.get_opex_for_year(opex_data, year)
        
        # ASR hanya di tahun terakhir (sebagai item terpisah, bukan CAPEX)
        year_asr = asr_amount if year == last_year else Decimal('0')
        
        # Depreciation hanya 5 tahun pertama
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
        
        # Total Cost Recoverable = CAPEX + OPEX + Depreciation + ASR
        total_cost_recoverable = year_capex + year_opex + depreciation + year_asr
        
        # Available for Production Split = Revenue - Total Cost Recoverable
        available_for_split = total_revenue - total_cost_recoverable
        
        # PSC Split berdasarkan Available for Split
        contractor_pretax = available_for_split * fiscal.contractor_oil_pretax
        contractor_tax = contractor_pretax * fiscal.contractor_tax_rate
        contractor_aftertax = contractor_pretax - contractor_tax
        
        government_pretax = available_for_split * fiscal.gov_oil_pretax
        government_tax = contractor_tax
        government_total = government_pretax + government_tax
        
        # Net Cash Flow = Revenue - (OPEX + CAPEX + ASR)
        # Note: Depreciation tidak masuk cash flow (non-cash expense)
        net_cf = total_revenue - year_opex - year_capex - year_asr
        cumulative_cf += net_cf
        
        year_result = {
            'scenario_id': scenario_id,
            'year': year,
            'oil_production_bbl': float(enhanced_oil_bbl),
            'gas_production_mmscf': float(enhanced_gas_mmscf),
            'gas_production_mmbtu': float(enhanced_gas_mmbtu),
            'oil_revenue': float(oil_revenue),
            'gas_revenue': float(gas_revenue),
            'total_revenue': float(total_revenue),
            'capex': float(year_capex),
            'opex': float(year_opex),
            'asr': float(year_asr),  # ASR sebagai field terpisah
            'depreciation': float(depreciation),
            'operating_profit': float(available_for_split),  # Ini sebenarnya "Available for Split"
            'contractor_pretax': float(contractor_pretax),
            'contractor_tax': float(contractor_tax),
            'contractor_aftertax': float(contractor_aftertax),
            'government_pretax': float(government_pretax),
            'government_tax': float(government_tax),
            'government_total': float(government_total),
            'net_cash_flow': float(net_cf),
            'cumulative_cash_flow': float(cumulative_cf)
        }
        
        results.append(year_result)
    
    self.save_calculation_results(results)
    metrics = self.calculate_metrics(scenario_id, results, fiscal, total_capex)
    self.save_scenario_metrics(scenario_id, metrics)
    
    return results, metrics

Perbedaan dengan code sebelumnya:
ASR tidak ditambahkan ke year_capex
ASR jadi field terpisah year_asr
total_cost_recoverable = CAPEX + OPEX + Depreciation + ASR
PSC split dihitung dari available_for_split (bukan operating_profit)
Cash flow = Revenue - OPEX - CAPEX - ASR (depreciation tidak masuk karena non-cash)

2. Depreciation Hanya 5 Tahun Pertama
python
# Depreciation calculation
if period <= fiscal.depreciation_life:  # period <= 5
    depreciation = self.calculate_depreciation_ddb(...)
else:
    depreciation = Decimal('0')  # Tahun 6-12 tidak ada depreciation

Sekarang depreciation hanya dihitung untuk:
Year 2026 (period 1)
Year 2027 (period 2)
Year 2028 (period 3)
Year 2029 (period 4)
Year 2030 (period 5)
Year 2031-2037 → depreciation = 0

DAN WAJIB DIGANTI UNTUK FUNGSI NPV:
def calculate_metrics(
    self, 
    scenario_id: int, 
    results: List[Dict], 
    fiscal: FiscalTerms,
    total_capex: Decimal
) -> Dict:
    """
    Calculate financial metrics matching Excel output
    """
    
    # Cash flows for NPV and IRR
    cash_flows = [float(r['net_cash_flow']) for r in results]
    
    # NPV - Excel style (treats first CF as end of period 1)
    try:
        # Option 1: Manual calculation (RECOMMENDED)
        discount_rate = float(fiscal.discount_rate)
        npv = sum(cf / ((1 + discount_rate) ** (i + 1)) 
                 for i, cf in enumerate(cash_flows))
        npv = Decimal(str(npv))
        
        # Option 2: Using numpy_financial (if available)
        # npv = Decimal(str(npf.npv(float(fiscal.discount_rate), cash_flows) 
        #                   * (1 + float(fiscal.discount_rate))))
    except Exception as e:
        print(f"NPV calculation error: {e}")
        npv = None
    
    # IRR - This is same for both Excel and Python
    try:
        irr = Decimal(str(npf.irr(cash_flows)))
    except:
        irr = None
    
    # Payback Period
    payback = self.calculate_payback_period(results)
    
    # Gross Revenue = SUM of all revenues
    gross_revenue = sum(Decimal(str(r['total_revenue'])) for r in results)
    
    # Contractor Take = SUM of contractor after-tax
    contractor_take = sum(Decimal(str(r['contractor_aftertax'])) for r in results)
    
    # Gov Take = SUM of government total
    gov_take = sum(Decimal(str(r['government_total'])) for r in results)
    
    # Contractor PTCF = SUM of contractor tax (pre-tax cash flow)
    contractor_ptcf = sum(Decimal(str(r['contractor_tax'])) for r in results)
    
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
