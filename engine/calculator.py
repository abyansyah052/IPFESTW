"""
Financial Calculation Engine
Implements all financial calculations based on the mathematical formulas
"""
import pandas as pd
import numpy as np
import numpy_financial as npf
from typing import Dict, List, Tuple
from database.models import (
    Scenario, ScenarioCapex, ScenarioOpex, CalculationResult, ScenarioMetrics,
    FiscalTerms, PricingAssumptions, ProductionData, ProductionEnhancement, CapexItem
)

class FinancialCalculator:
    """
    Handles all financial calculations for scenarios
    Based on Production Sharing Contract (PSC) fiscal model
    """
    
    def __init__(self, scenario: Scenario, session):
        self.scenario = scenario
        self.session = session
        self.fiscal_terms = session.query(FiscalTerms).filter_by(id=scenario.fiscal_terms_id).first()
        self.pricing = session.query(PricingAssumptions).filter_by(id=scenario.pricing_assumptions_id).first()
        self.enhancement = None
        if scenario.production_enhancement_id:
            self.enhancement = session.query(ProductionEnhancement).filter_by(id=scenario.production_enhancement_id).first()
    
    def calculate_enhanced_production(self, base_oil: float, base_gas: float, has_eor: bool, has_egr: bool) -> Tuple[float, float]:
        """
        Calculate enhanced production using CCUS enhancement rates
        
        Oil Production: P_oil,t = P_base,oil,t × (1 + r_EOR)
        Gas Production: P_gas,t = P_base,gas,t × (1 + r_EGR)
        
        Args:
            base_oil: Base oil production (bbl)
            base_gas: Base gas production (MMSCF)
            has_eor: Whether scenario uses EOR enhancement
            has_egr: Whether scenario uses EGR enhancement
            
        Returns:
            Tuple of (enhanced_oil, enhanced_gas)
        """
        enhanced_oil = base_oil
        enhanced_gas = base_gas
        
        if self.enhancement:
            if has_eor:
                # P_oil,t = P_base,oil,t × 1.20
                enhanced_oil = base_oil * (1 + self.enhancement.eor_enhancement_rate)
            
            if has_egr:
                # P_gas,t = P_base,gas,t × 1.25
                enhanced_gas = base_gas * (1 + self.enhancement.egr_enhancement_rate)
        
        return enhanced_oil, enhanced_gas
    
    def convert_gas_to_mmbtu(self, gas_mmscf: float) -> float:
        """
        Convert gas from MMSCF to MMBTU
        P_gas,MMBTU = P_gas,MMSCF × 1027
        
        Args:
            gas_mmscf: Gas production in MMSCF
            
        Returns:
            Gas production in MMBTU
        """
        return gas_mmscf * self.pricing.mmscf_to_mmbtu
    
    def calculate_revenue(self, oil_production: float, gas_production_mmbtu: float) -> Tuple[float, float, float]:
        """
        Calculate revenue from oil and gas production
        
        Total Revenue: R_t = (P_oil,t × Price_oil) + (P_gas,MMBTU,t × Price_gas)
        R_t = (P_oil,t × 60) + (P_gas,MMBTU,t × 5.5)
        
        Args:
            oil_production: Oil production (bbl)
            gas_production_mmbtu: Gas production (MMBTU)
            
        Returns:
            Tuple of (oil_revenue, gas_revenue, total_revenue) in USD
        """
        oil_revenue = oil_production * self.pricing.oil_price
        gas_revenue = gas_production_mmbtu * self.pricing.gas_price
        total_revenue = oil_revenue + gas_revenue
        
        return oil_revenue, gas_revenue, total_revenue
    
    def calculate_depreciation_ddb(self, capex_total: float, year: int, depreciation_life: int = 5) -> float:
        """
        Calculate depreciation using Declining Balance Method (DDB)
        
        D_t = DDB(Cost, Salvage, Life, Period_t, Factor)
        D_t = DDB(CAPEX_total, 0, 5, t, 0.25)
        
        Parameters:
        - Salvage value = 0
        - Depreciation life = 5 years
        - Declining balance factor = 25% (0.25)
        
        Args:
            capex_total: Total CAPEX investment
            year: Current year (1-based)
            depreciation_life: Years for depreciation
            
        Returns:
            Depreciation amount for the year
        """
        if year > depreciation_life:
            return 0
        
        salvage = self.fiscal_terms.salvage_value
        factor = self.fiscal_terms.depreciation_factor
        
        # DDB formula: depreciation = (cost - accumulated_depreciation) * (factor / life)
        rate = factor / depreciation_life
        book_value = capex_total
        accumulated_depreciation = 0
        
        for i in range(1, year + 1):
            annual_depreciation = (book_value - accumulated_depreciation) * rate
            # Ensure book value doesn't go below salvage value
            if book_value - accumulated_depreciation - annual_depreciation < salvage:
                annual_depreciation = book_value - accumulated_depreciation - salvage
            
            if i == year:
                return max(0, annual_depreciation)
            
            accumulated_depreciation += annual_depreciation
        
        return 0
    
    def calculate_operating_profit(self, revenue: float, depreciation: float, opex: float) -> float:
        """
        Calculate operating profit
        
        OP_t = R_t - Σ D_i - OPEX_t
        
        Args:
            revenue: Total revenue
            depreciation: Depreciation amount
            opex: Total OPEX
            
        Returns:
            Operating profit
        """
        return revenue - depreciation - opex
    
    def calculate_psc_split(self, operating_profit: float) -> Dict[str, float]:
        """
        Calculate Production Sharing Contract (PSC) split
        
        Pre-tax Contractor Share: CS_pre-tax,t = OP_t × α_contractor = OP_t × 0.6723
        Contractor Tax: Tax_t = CS_pre-tax,t × τ = CS_pre-tax,t × 0.405
        After-tax Contractor Share: CS_after-tax,t = CS_pre-tax,t - Tax_t
        Government Share: GS_pre-tax,t = OP_t × α_gov = OP_t × 0.3277
        Total Government Take: GS_total,t = GS_pre-tax,t + Tax_t
        
        Where:
        - α_contractor = 67.23% (contractor pre-tax split)
        - α_gov = 32.77% (government pre-tax split)
        - τ = 40.5% (contractor efficiency tax rate)
        
        Args:
            operating_profit: Operating profit amount
            
        Returns:
            Dictionary with PSC split components
        """
        contractor_pretax = operating_profit * self.fiscal_terms.contractor_oil_pretax
        contractor_tax = contractor_pretax * self.fiscal_terms.contractor_tax_rate
        contractor_aftertax = contractor_pretax - contractor_tax
        
        government_pretax = operating_profit * self.fiscal_terms.gov_oil_pretax
        government_total = government_pretax + contractor_tax
        
        return {
            'contractor_pretax': contractor_pretax,
            'contractor_tax': contractor_tax,
            'contractor_aftertax': contractor_aftertax,
            'government_pretax': government_pretax,
            'government_total': government_total
        }
    
    def calculate_npv(self, cash_flows: List[float], discount_rate: float = None) -> float:
        """
        Calculate Net Present Value (NPV) - Excel style
        
        NPV = Σ(t=1 to 12) CF_t / (1+r)^t
        
        Where r = 0.13 (13% discount rate)
        Excel treats first CF as end of period 1
        
        Args:
            cash_flows: List of cash flows for each year
            discount_rate: Discount rate (default from fiscal terms)
            
        Returns:
            Net Present Value
        """
        if discount_rate is None:
            discount_rate = self.fiscal_terms.discount_rate
        
        # Manual NPV calculation (Excel style)
        npv = sum(cf / ((1 + discount_rate) ** (i + 1)) 
                 for i, cf in enumerate(cash_flows))
        
        return npv
    
    def calculate_irr(self, cash_flows: List[float]) -> float:
        """
        Calculate Internal Rate of Return (IRR)
        
        IRR is the discount rate that makes NPV = 0
        Uses numpy's IRR calculation
        
        Args:
            cash_flows: List of cash flows
            
        Returns:
            IRR as decimal (e.g., 0.15 for 15%)
        """
        try:
            # numpy_financial.irr for IRR calculation (np.irr deprecated)
            return float(npf.irr(cash_flows))
        except:
            return None
    
    def calculate_payback_period(self, results: List[CalculationResult]) -> float:
        """
        Calculate Payback Period
        When cumulative cash flow becomes positive
        
        Uses Excel formula: Payback = T + (-CCF_T / CCF_T+1)
        Where:
        - T = year number when CCF first becomes positive (1-indexed)
        - CCF_T = cumulative CF of year before positive (negative value)
        - CCF_T+1 = cumulative CF of first positive year
        
        Args:
            results: List of calculation results
            
        Returns:
            Payback period in years (with fraction)
        """
        for i, result in enumerate(results):
            if result.cumulative_cash_flow >= 0:
                if i == 0:
                    return 1.0
                
                prev_cf = results[i-1].cumulative_cash_flow  # CCF_T (negative)
                curr_cf = result.cumulative_cash_flow        # CCF_T+1 (positive)
                
                if curr_cf == prev_cf:
                    return float(i + 1)
                
                # Excel formula: T + (-CCF_T / CCF_T+1)
                # T = i + 1 (1-indexed year number where CCF becomes positive)
                # Fraction = -prev_cf / curr_cf (since prev_cf is negative, this gives positive fraction)
                year_positive = i + 1  # Year number when first positive
                fraction = -prev_cf / curr_cf
                return float(year_positive) + fraction
        
        return None
    
    def calculate_asr(self, capex_total: float) -> float:
        """
        Calculate Abandonment Security Reserve
        
        ASR = CAPEX_total × 0.05
        
        ASR is calculated as 5% of total CAPEX and realized in the final year (2037)
        
        Args:
            capex_total: Total CAPEX investment
            
        Returns:
            ASR amount
        """
        return capex_total * self.fiscal_terms.asr_rate
    
    def get_total_capex(self) -> float:
        """Get total CAPEX for the scenario"""
        scenario_capex = self.session.query(ScenarioCapex).filter_by(scenario_id=self.scenario.id).all()
        return sum(item.total_cost for item in scenario_capex)
    
    def check_enhancement_types(self) -> Tuple[bool, bool]:
        """
        Check if scenario uses EOR and/or EGR enhancement
        
        Returns:
            Tuple of (has_eor, has_egr)
        """
        scenario_capex = self.session.query(ScenarioCapex).join(CapexItem).filter(
            ScenarioCapex.scenario_id == self.scenario.id
        ).all()
        
        has_eor = any(item.capex_item.code == 'CCUS_EOR' for item in scenario_capex)
        has_egr = any(item.capex_item.code == 'CCUS_EGR' for item in scenario_capex)
        
        return has_eor, has_egr
    
    def calculate_scenario(self) -> Tuple[List[CalculationResult], ScenarioMetrics]:
        """
        Main calculation method - calculates all financial metrics for the scenario
        Based on Excel Calculation Example structure from tambahan.md
        
        Returns:
            Tuple of (calculation_results, scenario_metrics)
        """
        # Get total CAPEX
        capex_total = self.get_total_capex()
        
        # Calculate ASR (5% of total CAPEX, paid in final year)
        asr_amount = capex_total * self.fiscal_terms.asr_rate
        
        # Check enhancement types
        has_eor, has_egr = self.check_enhancement_types()
        
        # Get production data
        production_data = self.session.query(ProductionData).filter_by(
            profile_id=self.scenario.production_profile_id
        ).order_by(ProductionData.year).all()
        
        # Get OPEX data
        scenario_opex = self.session.query(ScenarioOpex).filter_by(
            scenario_id=self.scenario.id
        ).order_by(ScenarioOpex.year).all()
        opex_by_year = {}
        for opex in scenario_opex:
            if opex.year not in opex_by_year:
                opex_by_year[opex.year] = 0
            opex_by_year[opex.year] += opex.opex_amount
        
        # Determine last year for ASR
        last_year = self.fiscal_terms.project_end_year
        
        # Calculate year by year
        results = []
        cumulative_cf = 0
        cash_flows = []
        
        for prod in production_data:
            year = prod.year
            period = year - self.fiscal_terms.project_start_year + 1
            
            # Convert daily rates to annual production
            # Annual = Daily Rate × Working Days (220)
            oil_prod_base = prod.condensate_rate_bopd * self.pricing.working_days
            gas_prod_base = prod.gas_rate_mmscfd * self.pricing.working_days
            
            # 1. Calculate enhanced production with EOR/EGR
            oil_prod, gas_prod = self.calculate_enhanced_production(
                oil_prod_base, 
                gas_prod_base,
                has_eor, 
                has_egr
            )
            
            # 2. Convert gas to MMBTU
            gas_mmbtu = self.convert_gas_to_mmbtu(gas_prod)
            
            # 3. Calculate revenue
            oil_rev, gas_rev, total_rev = self.calculate_revenue(oil_prod, gas_mmbtu)
            
            # 4. CAPEX (assuming all CAPEX in year 1 for now - you may need to adjust)
            year_capex = capex_total if period == 1 else 0
            
            # 5. Get OPEX for this year
            year_opex = opex_by_year.get(year, 0)
            
            # 6. Calculate depreciation (only first 5 years)
            if period <= self.fiscal_terms.depreciation_life:
                depreciation = self.calculate_depreciation_ddb(capex_total, period)
            else:
                depreciation = 0
            
            # 7. ASR (only in final year)
            year_asr = asr_amount if year == last_year else 0
            
            # 8. Total Cost Recoverable = CAPEX + OPEX + Depreciation + ASR
            total_cost_recoverable = year_capex + year_opex + depreciation + year_asr
            
            # 9. Available for Production Split = Revenue - Total Cost Recoverable
            available_for_split = total_rev - total_cost_recoverable
            
            # 10. PSC Split based on Available for Split
            # CRITICAL: NO SPLIT if:
            # 1. Available <= 0 (losses), OR
            # 2. Year is last year (ASR year)
            if available_for_split <= 0 or year == last_year:
                psc_split = {
                    'contractor_pretax': 0,
                    'contractor_tax': 0,
                    'contractor_aftertax': 0,
                    'government_pretax': 0,
                    'government_total': 0
                }
            else:
                psc_split = self.calculate_psc_split(available_for_split)
            
            # 11. Annual Cash Flow for IRR/NPV
            # Cash Flow = Revenue - OPEX - CAPEX (actual cash movement)
            # Note: Depreciation is NON-CASH, so not included in cash flow
            # ASR is actual cash reserve, so included
            annual_cf = total_rev - year_opex - year_capex - year_asr
            
            # 12. Cumulative Cash Flow
            cumulative_cf += annual_cf
            cash_flows.append(annual_cf)  # Use ANNUAL cash flow for NPV/IRR
            
            # Store result
            result = CalculationResult(
                scenario_id=self.scenario.id,
                year=year,
                oil_production=oil_prod,
                gas_production_mmscf=gas_prod,
                gas_production_mmbtu=gas_mmbtu,
                oil_revenue=oil_rev,
                gas_revenue=gas_rev,
                total_revenue=total_rev,
                depreciation=depreciation,
                opex_total=year_opex,
                operating_profit=available_for_split,  # This is "Available for Split"
                contractor_share_pretax=psc_split['contractor_pretax'],
                contractor_tax=psc_split['contractor_tax'],
                contractor_share_aftertax=psc_split['contractor_aftertax'],
                government_share_pretax=psc_split['government_pretax'],
                government_total_take=psc_split['government_total'],
                cash_flow=annual_cf,
                cumulative_cash_flow=cumulative_cf
            )
            results.append(result)
        
        # Calculate NPV at 13% using ANNUAL cash flows
        npv = self.calculate_npv(cash_flows, self.fiscal_terms.discount_rate)
        
        # Calculate IRR using ANNUAL cash flows (not cumulative!)
        # IRR is the discount rate that makes NPV of annual cash flows = 0
        irr = self.calculate_irr(cash_flows)
        
        # Calculate Payback Period
        payback_period = self.calculate_payback_period(results)
        
        # Calculate metrics (matching Excel J35-J41)
        # Gross Revenue = SUM all revenues
        gross_revenue = sum(r.total_revenue for r in results)
        
        # Contractor Take = SUM contractor after-tax (ONLY years with actual split)
        # Excludes Year 1 (loss) and Year 12 (ASR year) as per Excel
        contractor_take = sum(r.contractor_share_aftertax for r in results 
                             if r.contractor_share_aftertax > 0)
        
        # Gov Take = SUM government total (ONLY years with actual split)
        gov_take = sum(r.government_total_take for r in results 
                      if r.government_total_take > 0)
        
        # Contractor PTCF = SUM contractor tax (ONLY years with actual split)
        contractor_ptcf = sum(r.contractor_tax for r in results 
                             if r.contractor_tax > 0)
        
        # Total OPEX
        total_opex = sum(opex_by_year.values())
        
        # Create metrics
        metrics = ScenarioMetrics(
            scenario_id=self.scenario.id,
            total_capex=capex_total,
            total_opex=total_opex,
            total_revenue=gross_revenue,
            total_contractor_share=contractor_take,
            total_government_take=gov_take,
            npv=npv,
            irr=irr,
            payback_period_years=payback_period,
            asr_amount=asr_amount
        )
        
        return results, metrics
    
    def save_calculations(self):
        """
        Calculate and save results to database
        """
        # Delete existing results
        self.session.query(CalculationResult).filter_by(scenario_id=self.scenario.id).delete()
        self.session.query(ScenarioMetrics).filter_by(scenario_id=self.scenario.id).delete()
        
        # Calculate
        results, metrics = self.calculate_scenario()
        
        # Save results
        self.session.add_all(results)
        self.session.add(metrics)
        self.session.commit()
        
        return results, metrics
